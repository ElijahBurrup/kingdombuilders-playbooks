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

    // =====================================================================
    // Explicit "Save to My Saves" — distinct from auto-persisted state.
    //
    // A reader can hit a Save button on a widget to keep a snapshot of its
    // current state in their personal My Saves list. Anonymous users get
    // redirected to /auth?next=... and are returned to the same widget.
    //
    // The widget HTML opts in by calling:
    //   kbWidget.attachSave(element, {
    //     slug: 'the-foxs-trail',
    //     key: 'trail-map',
    //     widgetTitle: 'My Trail Map',
    //     playbookTitle: "The Fox's Trail",
    //     getPayload: function(){ return STATE; },
    //     getPreview: function(){ return 'Trail: ' + STATE.trail; }
    //   });
    // =====================================================================

    function savesEndpoint() {
        return apiBase() + "/saves";
    }

    function ensureSaveStyles() {
        if (document.getElementById("kb-save-styles")) return;
        var s = document.createElement("style");
        s.id = "kb-save-styles";
        s.textContent = [
            ".kb-save-btn{position:absolute;top:12px;right:12px;display:inline-flex;align-items:center;gap:6px;",
            "  padding:7px 13px 7px 11px;background:rgba(255,255,255,0.94);border:1.5px solid rgba(0,0,0,0.14);",
            "  border-radius:50px;cursor:pointer;z-index:5;font-family:'Nunito',sans-serif;font-size:0.6rem;",
            "  font-weight:800;letter-spacing:1.5px;text-transform:uppercase;color:#2A2A2A;transition:all 0.2s;",
            "  box-shadow:0 2px 8px rgba(0,0,0,0.1)}",
            ".kb-save-btn:hover{background:#fff;border-color:#666;color:#000;transform:translateY(-1px);box-shadow:0 4px 14px rgba(0,0,0,0.15)}",
            ".kb-save-btn svg{width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}",
            ".kb-save-btn.saved{background:#1F2440;border-color:#1F2440;color:#F5E0A8}",
            ".kb-save-btn.saved:hover{background:#3D4670;color:#fff}",
            ".kb-save-btn.saved svg{fill:#F5E0A8}",
            ".kb-save-btn:focus{outline:2px solid rgba(212,168,67,0.6);outline-offset:2px}",
            ".kb-save-host{position:relative}",
            ".kb-save-toast{position:fixed;bottom:30px;left:50%;transform:translateX(-50%) translateY(80px);",
            "  background:#1F2440;color:#F5E0A8;padding:13px 24px;border-radius:30px;font-family:'Nunito',sans-serif;",
            "  font-size:0.7rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;z-index:99999;opacity:0;",
            "  transition:all 0.4s;pointer-events:none;box-shadow:0 8px 28px rgba(0,0,0,0.35)}",
            ".kb-save-toast.show{opacity:1;transform:translateX(-50%) translateY(0)}",
            "@media (max-width:520px){.kb-save-btn{top:8px;right:8px;padding:6px 11px 6px 9px;font-size:0.55rem}}",
            "@media (prefers-reduced-motion: reduce){.kb-save-btn,.kb-save-toast{transition:none}}",
        ].join("");
        document.head.appendChild(s);
    }

    function bookmarkSVG() {
        return '<svg viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>';
    }

    function showSaveToast(msg) {
        ensureSaveStyles();
        var t = document.getElementById("kb-save-toast-host");
        if (!t) {
            t = document.createElement("div");
            t.id = "kb-save-toast-host";
            t.className = "kb-save-toast";
            document.body.appendChild(t);
        }
        t.textContent = msg;
        t.classList.add("show");
        clearTimeout(t._timer);
        t._timer = setTimeout(function () { t.classList.remove("show"); }, 2400);
    }

    function redirectToSignIn(returnUrl) {
        var prefix = getPrefix();
        var target = prefix + "/auth?tab=login&next=" + encodeURIComponent(returnUrl);
        location.href = target;
    }

    async function postSave(body) {
        return fetch(savesEndpoint(), {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
    }

    async function deleteSaveByKey(slug, key) {
        var url = savesEndpoint() + "/by-key?slug=" + encodeURIComponent(slug) +
                  "&key=" + encodeURIComponent(key);
        return fetch(url, { method: "DELETE", credentials: "include" });
    }

    async function checkSave(slug, key) {
        var url = savesEndpoint() + "/check?slug=" + encodeURIComponent(slug) +
                  "&key=" + encodeURIComponent(key);
        try {
            var resp = await fetch(url, { method: "GET", credentials: "include" });
            if (!resp.ok) return { saved: false, signed_in: isSignedIn() };
            return await resp.json();
        } catch (e) {
            return { saved: false, signed_in: isSignedIn() };
        }
    }

    function attachSave(host, opts) {
        if (!host || !opts || !opts.slug || !opts.key || !opts.widgetTitle ||
            !opts.playbookTitle || typeof opts.getPayload !== "function") {
            return;
        }
        ensureSaveStyles();

        if (!host.id) host.id = "save-anchor-" + opts.key;
        host.classList.add("kb-save-host");

        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "kb-save-btn";
        btn.setAttribute("aria-label", "Save this widget to My Saves");
        btn.innerHTML = bookmarkSVG() + '<span class="kb-save-label">Save</span>';
        host.appendChild(btn);

        var savedState = false;
        function render() {
            btn.classList.toggle("saved", savedState);
            btn.querySelector(".kb-save-label").textContent = savedState ? "Saved" : "Save";
            btn.setAttribute("aria-pressed", savedState ? "true" : "false");
        }

        function returnUrl() {
            return location.pathname + location.search + "#" + host.id;
        }

        btn.addEventListener("click", async function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            btn.disabled = true;
            try {
                if (savedState) {
                    var del = await deleteSaveByKey(opts.slug, opts.key);
                    if (del.ok) {
                        savedState = false;
                        render();
                        showSaveToast("Removed from My Saves");
                    } else if (del.status === 401) {
                        redirectToSignIn(returnUrl());
                    } else {
                        showSaveToast("Could not unsave");
                    }
                } else {
                    var payload = opts.getPayload();
                    var preview = "";
                    try {
                        preview = (typeof opts.getPreview === "function") ?
                            String(opts.getPreview() || "") : "";
                    } catch (e) { preview = ""; }
                    preview = preview.slice(0, 380);
                    var body = {
                        playbook_slug: opts.slug,
                        widget_key: opts.key,
                        widget_title: opts.widgetTitle,
                        playbook_title: opts.playbookTitle,
                        preview_text: preview,
                        payload: payload || {},
                    };
                    var resp = await postSave(body);
                    if (resp.status === 401) {
                        redirectToSignIn(returnUrl());
                        return;
                    }
                    if (resp.ok) {
                        savedState = true;
                        render();
                        showSaveToast("Saved to My Saves");
                    } else {
                        showSaveToast("Could not save");
                    }
                }
            } finally {
                btn.disabled = false;
            }
        });

        render();
        if (isSignedIn()) {
            checkSave(opts.slug, opts.key).then(function (r) {
                savedState = !!(r && r.saved);
                render();
            });
        }

        // Auto-press if the user came back from sign-in to this widget anchor.
        if (location.hash === "#" + host.id) {
            setTimeout(function () {
                if (isSignedIn() && !savedState && location.hash === "#" + host.id) {
                    btn.click();
                }
            }, 700);
        }
    }

    var kbWidget = {
        save: save,
        load: load,
        clear: clear,
        isSignedIn: isSignedIn,
        attachSave: attachSave,
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
