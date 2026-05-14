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

SCRIPT_MARKER = 'data-auth-aware="v2"'

SCRIPT = """
<script data-auth-aware="v2">
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

  try{
    const r = await fetch('/playbooks/auth/status', {credentials:'same-origin'});
    if(!r.ok) return;
    const data = await r.json();
    if(!data || !data.signed_in) return;

    document.querySelectorAll('a.nav-button[href$="/auth"]').forEach(a => {
      a.replaceWith(makeLogoutBtn(a.className, 'Sign Out', false));
    });
    document.querySelectorAll('.nav-drawer a[href$="/auth"]').forEach(a => {
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
