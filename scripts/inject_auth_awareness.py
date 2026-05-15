"""Inject auth-awareness JS into all top-nav pages so the 'Sign In' button
becomes 'Sign Out' (POST to /auth/logout) when the user is already signed in.
Otherwise clicking Sign In would 303 the logged-in user back to the homepage
and appear broken.
"""
import os

PAGES = [
    'static/index.html',
    'static/archive.html',
    'static/compass.html',
    'static/pathways/work-reset.html',
    'static/pathways/identity-walk.html',
    'static/pathways/ai-age.html',
    'static/pathways/money-architecture.html',
    'static/pathways/resilience-stack.html',
    'static/pathways/inner-battle.html',
    'static/pathways/family-foundation.html',
    'static/pathways/strategist-toolkit.html',
    'static/pathways/process-model.html',
]

SCRIPT_MARKER = 'data-auth-aware="v4"'

SCRIPT = """
<script data-auth-aware="v4">
(async function(){
  async function doLogout(ev){
    if(ev) ev.preventDefault();
    try{
      await fetch('/playbooks/auth/logout', {
        method:'POST',
        credentials:'same-origin',
        headers:{'Accept':'application/json','X-Requested-With':'fetch'},
      });
    }catch(e){}
    window.location.href = '/playbooks/';
  }

  function makeLogoutBtn(cls, label, block){
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = label;
    b.className = cls;
    b.style.cssText = 'border:none;cursor:pointer;font:inherit;letter-spacing:inherit;text-transform:inherit'
      + (block ? ';display:block;width:100%' : '');
    b.addEventListener('click', doLogout);
    return b;
  }

  // Manage Subscription -> Stripe Billing Portal via existing POST endpoint.
  // Stripe owns the cancel/refund/prorate logic so we cannot mis-handle it.
  function makeManageForm(isDrawer){
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/playbooks/manage-subscription';
    form.style.cssText = 'margin:0;padding:0;' + (isDrawer ? 'display:block' : 'display:inline');
    const btn = document.createElement('button');
    btn.type = 'submit';
    btn.textContent = 'Manage Subscription';
    if(isDrawer){
      btn.className = 'drawer-cta';
      btn.style.cssText = 'border:none;cursor:pointer;font:inherit;width:100%;display:block;padding:14px 18px;'
        + 'font-family:Poppins,sans-serif;font-size:0.85rem;font-weight:700;letter-spacing:1.5px;'
        + 'text-transform:uppercase;text-align:center;color:rgba(245,224,168,0.85);'
        + 'background:rgba(245,224,168,0.06);border-radius:10px;margin-bottom:6px';
    } else {
      btn.className = 'nav-link';
      btn.style.cssText = 'border:none;cursor:pointer;background:transparent;font:inherit;letter-spacing:inherit;text-transform:inherit';
    }
    form.appendChild(btn);
    return form;
  }

  try{
    const r = await fetch('/playbooks/auth/status', {credentials:'same-origin'});
    if(!r.ok) return;
    const data = await r.json();

    // Mark admins on the body so CSS rules like the referral-link hiding
    // selector (body:not(.auth-admin) a[href$="/referrals"]) can un-hide
    // admin-only surfaces. Doing this for every page paint keeps the rest
    // of the codebase declarative.
    if(data && data.is_admin){
      document.body.classList.add('auth-admin');
    }

    if(!data || !data.signed_in) return;

    // Topnav: Manage Subscription chip (subscribers only), then swap Sign In -> Sign Out
    if(data.is_subscriber){
      document.querySelectorAll('.topnav-utility').forEach(box => {
        if(box.querySelector('form[action$="/manage-subscription"]')) return;
        const signIn = box.querySelector('a.nav-button, button.nav-button');
        const form = makeManageForm(false);
        if(signIn) box.insertBefore(form, signIn); else box.appendChild(form);
      });
    }

    document.querySelectorAll('a.nav-button[href$="/auth"]').forEach(a => {
      a.replaceWith(makeLogoutBtn(a.className, 'Sign Out', false));
    });

    // Mobile drawer: insert Manage Subscription above Sign Out
    document.querySelectorAll('.nav-drawer a[href$="/auth"]').forEach(a => {
      if(data.is_subscriber){
        a.parentNode.insertBefore(makeManageForm(true), a);
      }
      a.replaceWith(makeLogoutBtn(a.className, 'Sign Out', true));
    });
  }catch(e){}
})();
</script>
"""

count = 0
for path in PAGES:
    if not os.path.exists(path):
        continue
    with open(path, encoding='utf-8') as f:
        html = f.read()
    if SCRIPT_MARKER in html:
        print(f"  (already injected) {path}")
        continue
    if '</body>' not in html:
        print(f"  (no </body>) {path}")
        continue
    html = html.replace('</body>', SCRIPT + '\n</body>', 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    count += 1
    print(f"  injected auth-awareness into {path}")

print(f"\nUpdated {count} pages.")
