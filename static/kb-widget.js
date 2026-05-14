/*
 * kbWidget — shared client helper for interactive playbook widgets.
 *
 * Two modes, mirroring the server router:
 *   - "latest"  (default): one saved state per (slug, widget_key).
 *   - "history" : append-only entries for diary-style widgets.
 *
 * Behavior:
 *   - When signed in: GET/POST to /api/v1/widgets/:slug/:key.
 *   - When signed out: read/write window.localStorage with a kb:widget: prefix.
 *   - On sign-in, the helper can migrate any localStorage entries that exist
 *     for this slug+key into the user's account (one-shot per key).
 *
 * Public API:
 *   kbWidget.save(slug, key, data, opts?)      -> Promise<{persisted, mode}>
 *   kbWidget.load(slug, key, opts?)            -> Promise<{data, entries?}>
 *   kbWidget.clear(slug, key, opts?)           -> Promise<{cleared}>
 *   kbWidget.isSignedIn()                      -> boolean
 *   kbWidget.onReady(cb)                       -> register callback once helper is initialized
 *
 * opts:
 *   { history: bool, limit: number }
 *
 * Detection of signed-in state:
 *   The legacy reader injects window.KB_USER = { signed_in: <bool> } before
 *   loading this script. If KB_USER is undefined we treat as signed out.
 *
 * URL prefix awareness:
 *   The catalog is sometimes served under /playbooks/* (Cloudflare Worker).
 *   We detect prefix from location.pathname the same way the existing
 *   tracking script does.
 */

(function (global) {
    var LS_PREFIX = "kb:widget:";
    var MIGRATED_FLAG = "kb:widget:migrated:";

    function getPrefix() {
        try {
            var m = location.pathname.match(/^(\/[^\/]+)\/read\//);
            return m ? m[1] : "";
        } catch (e) {
            return "";
        }
    }

    function apiBase() {
        return getPrefix() + "/api/v1";
    }

    function isSignedIn() {
        return !!(global.KB_USER && global.KB_USER.signed_in === true);
    }

    function lsKey(slug, key, history) {
        return LS_PREFIX + slug + ":" + key + (history ? ":history" : "");
    }

    function lsGetLatest(slug, key) {
        try {
            var raw = localStorage.getItem(lsKey(slug, key, false));
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    function lsSetLatest(slug, key, data) {
        try {
            localStorage.setItem(lsKey(slug, key, false), JSON.stringify({ data: data, updated_at: new Date().toISOString() }));
        } catch (e) {
            /* quota exceeded or storage disabled — silently degrade */
        }
    }

    function lsGetHistory(slug, key) {
        try {
            var raw = localStorage.getItem(lsKey(slug, key, true));
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    function lsPushHistory(slug, key, data) {
        try {
            var list = lsGetHistory(slug, key);
            list.push({ data: data, created_at: new Date().toISOString() });
            // Cap local history at 200 entries (same as server limit).
            if (list.length > 200) list = list.slice(list.length - 200);
            localStorage.setItem(lsKey(slug, key, true), JSON.stringify(list));
        } catch (e) {
            /* silently degrade */
        }
    }

    function lsClear(slug, key, opts) {
        try {
            localStorage.removeItem(lsKey(slug, key, false));
            if (opts && opts.history) localStorage.removeItem(lsKey(slug, key, true));
        } catch (e) { /* ignore */ }
    }

    async function postJson(url, body) {
        var resp = await fetch(url, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        if (!resp.ok) {
            throw new Error("widget save failed: " + resp.status);
        }
        return resp.json();
    }

    async function getJson(url) {
        var resp = await fetch(url, {
            method: "GET",
            credentials: "include",
            headers: { "Accept": "application/json" }
        });
        if (!resp.ok) {
            throw new Error("widget load failed: " + resp.status);
        }
        return resp.json();
    }

    async function deleteJson(url) {
        var resp = await fetch(url, {
            method: "DELETE",
            credentials: "include"
        });
        if (!resp.ok) {
            throw new Error("widget clear failed: " + resp.status);
        }
        return resp.json();
    }

    function endpoint(slug, key) {
        return apiBase() + "/widgets/" + encodeURIComponent(slug) + "/" + encodeURIComponent(key);
    }

    async function save(slug, key, data, opts) {
        opts = opts || {};
        var history = !!opts.history;

        // Always mirror to localStorage so a refresh shortly after sign-in
        // does not lose state if the network is slow.
        if (history) lsPushHistory(slug, key, data);
        else lsSetLatest(slug, key, data);

        if (!isSignedIn()) {
            return { persisted: false, mode: history ? "history" : "latest", local: true };
        }

        try {
            var result = await postJson(endpoint(slug, key), { data: data, history: history });
            return Object.assign({ local: true }, result);
        } catch (err) {
            // Network failure: state is already in localStorage. Return a soft failure.
            return { persisted: false, mode: history ? "history" : "latest", local: true, error: String(err) };
        }
    }

    async function load(slug, key, opts) {
        opts = opts || {};
        var history = !!opts.history;
        var limit = opts.limit || 50;

        if (!isSignedIn()) {
            if (history) return { signed_in: false, entries: lsGetHistory(slug, key) };
            var local = lsGetLatest(slug, key);
            return { signed_in: false, data: local ? local.data : null };
        }

        var url = endpoint(slug, key) + (history ? ("?history=true&limit=" + limit) : "");
        try {
            var result = await getJson(url);

            // First-time sign-in migration: if server has nothing and localStorage
            // does, push the local data up exactly once.
            await maybeMigrateFromLocal(slug, key, history, result);

            // Refresh stale localStorage mirror.
            if (!history && result.data) {
                lsSetLatest(slug, key, result.data);
            }
            return result;
        } catch (err) {
            // On network error fall back to local data so the widget still works.
            if (history) return { signed_in: true, entries: lsGetHistory(slug, key), error: String(err) };
            var local = lsGetLatest(slug, key);
            return { signed_in: true, data: local ? local.data : null, error: String(err) };
        }
    }

    async function clear(slug, key, opts) {
        opts = opts || {};
        var history = !!opts.history;

        lsClear(slug, key, opts);

        if (!isSignedIn()) return { cleared: true, local: true };

        try {
            var url = endpoint(slug, key) + (history ? "?history=true" : "");
            var result = await deleteJson(url);
            return Object.assign({ local: true }, result);
        } catch (err) {
            return { cleared: false, error: String(err) };
        }
    }

    async function maybeMigrateFromLocal(slug, key, history, serverResult) {
        var flagKey = MIGRATED_FLAG + slug + ":" + key + (history ? ":history" : "");
        try {
            if (localStorage.getItem(flagKey) === "1") return;
        } catch (e) { return; }

        if (history) {
            var serverEntries = (serverResult && serverResult.entries) || [];
            if (serverEntries.length > 0) {
                try { localStorage.setItem(flagKey, "1"); } catch (e) {}
                return;
            }
            var local = lsGetHistory(slug, key);
            for (var i = 0; i < local.length; i++) {
                try {
                    await postJson(endpoint(slug, key), { data: local[i].data, history: true });
                } catch (e) {
                    // Stop on first failure; we'll retry on next load.
                    return;
                }
            }
            try { localStorage.setItem(flagKey, "1"); } catch (e) {}
            return;
        }

        if (serverResult && serverResult.data) {
            try { localStorage.setItem(flagKey, "1"); } catch (e) {}
            return;
        }
        var localLatest = lsGetLatest(slug, key);
        if (localLatest && localLatest.data) {
            try {
                await postJson(endpoint(slug, key), { data: localLatest.data, history: false });
                try { localStorage.setItem(flagKey, "1"); } catch (e) {}
                if (serverResult) serverResult.data = localLatest.data;
            } catch (e) {
                /* will retry on next load */
            }
        }
    }

    var readyCallbacks = [];
    function onReady(cb) {
        if (typeof cb !== "function") return;
        readyCallbacks.push(cb);
        if (kbWidget._ready) {
            try { cb(kbWidget); } catch (e) { /* ignore */ }
        }
    }

    var kbWidget = {
        save: save,
        load: load,
        clear: clear,
        isSignedIn: isSignedIn,
        onReady: onReady,
        _ready: false
    };

    global.kbWidget = kbWidget;

    function init() {
        kbWidget._ready = true;
        for (var i = 0; i < readyCallbacks.length; i++) {
            try { readyCallbacks[i](kbWidget); } catch (e) { /* ignore */ }
        }
        readyCallbacks = [];
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})(typeof window !== "undefined" ? window : this);
