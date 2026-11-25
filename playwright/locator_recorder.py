"""
Locator recorder: open a Playwright browser, click elements, and record the most
reliable Playwright locator for each one.

Setup:
    pip install playwright
    playwright install chromium

Usage:
    python locator_recorder.py https://example.com
    (click elements in the browser; press Ctrl+C in the terminal or close the window to stop)

Output: printed to the terminal and saved to recorded_locators.json
"""
import json
import sys
from playwright.sync_api import sync_playwright

# Runs in every page/frame. Proposes candidate locators, best first.
INIT_JS = r"""
(() => {
  if (window.__pwRecorderInstalled) return;
  window.__pwRecorderInstalled = true;

  const INTERACTIVE = 'button,a,input,select,textarea,label,summary,[role],[data-testid]';
  const ROLE_BY_TAG = {a:'link', button:'button', select:'combobox', textarea:'textbox',
    h1:'heading', h2:'heading', h3:'heading', h4:'heading', h5:'heading', h6:'heading',
    img:'img', nav:'navigation', li:'listitem', option:'option', table:'table'};
  const ROLE_BY_INPUT = {text:'textbox', email:'textbox', search:'textbox', tel:'textbox',
    url:'textbox', password:'textbox', '':'textbox', checkbox:'checkbox', radio:'radio',
    submit:'button', button:'button', reset:'button', number:'spinbutton', range:'slider'};

  const clean = s => (s || '').replace(/\s+/g, ' ').trim();
  const looksDynamic = v => /\d{4,}|[0-9a-f]{8}-[0-9a-f]{4}|^[a-z]*[-_:]?[0-9a-f]{6,}$/i.test(v) || /^:r/.test(v);

  function roleOf(el) {
    const explicit = el.getAttribute('role');
    if (explicit) return explicit.split(' ')[0];
    const tag = el.tagName.toLowerCase();
    if (tag === 'a') return el.hasAttribute('href') ? 'link' : null;
    if (tag === 'input') return ROLE_BY_INPUT[(el.getAttribute('type') || '').toLowerCase()] || null;
    return ROLE_BY_TAG[tag] || null;
  }

  function labelText(el) {
    if (el.labels && el.labels.length) return clean(el.labels[0].innerText);
    const id = el.id;
    if (id) { const l = document.querySelector(`label[for="${CSS.escape(id)}"]`); if (l) return clean(l.innerText); }
    return '';
  }

  function nameOf(el) {
    const aria = el.getAttribute('aria-label'); if (aria) return clean(aria);
    const by = el.getAttribute('aria-labelledby');
    if (by) { const t = by.split(' ').map(i => document.getElementById(i)).filter(Boolean).map(n => n.innerText).join(' '); if (clean(t)) return clean(t); }
    const lt = labelText(el); if (lt) return lt;
    const tag = el.tagName.toLowerCase();
    if (tag === 'img') return clean(el.getAttribute('alt'));
    if (tag === 'input' && ['submit','button','reset'].includes((el.type||'').toLowerCase())) return clean(el.value);
    const txt = clean(el.innerText || el.textContent);
    return txt || clean(el.getAttribute('title'));
  }

  function cssPath(el) {
    const parts = [];
    let cur = el;
    while (cur && cur.nodeType === 1 && cur !== document.documentElement) {
      const tid = cur.getAttribute('data-testid');
      if (tid) { parts.unshift(`[data-testid="${CSS.escape(tid)}"]`); break; }
      if (cur.id && !looksDynamic(cur.id)) { parts.unshift('#' + CSS.escape(cur.id)); break; }
      let part = cur.tagName.toLowerCase();
      const parent = cur.parentElement;
      if (parent) {
        const same = [...parent.children].filter(c => c.tagName === cur.tagName);
        if (same.length > 1) part += `:nth-of-type(${same.indexOf(cur) + 1})`;
      }
      parts.unshift(part);
      cur = parent;
    }
    return parts.join(' > ');
  }

  function candidates(el) {
    const c = [];
    const tag = el.tagName.toLowerCase();
    for (const attr of ['data-testid']) {
      const v = el.getAttribute(attr); if (v) c.push({kind: 'testid', value: v});
    }
    for (const attr of ['data-test', 'data-qa', 'data-cy']) {
      const v = el.getAttribute(attr); if (v) c.push({kind: 'css', value: `[${attr}="${v}"]`});
    }
    const role = roleOf(el), name = nameOf(el);
    if (role && name && name.length <= 80) c.push({kind: 'role', role, name});
    const lt = labelText(el); if (lt) c.push({kind: 'label', value: lt});
    const ph = el.getAttribute('placeholder'); if (ph) c.push({kind: 'placeholder', value: ph});
    if (tag === 'img' && el.getAttribute('alt')) c.push({kind: 'alt', value: el.getAttribute('alt')});
    const txt = clean(el.innerText);
    if (txt && txt.length <= 60 && !['input','textarea','select'].includes(tag)) c.push({kind: 'text', value: txt});
    const title = el.getAttribute('title'); if (title) c.push({kind: 'title', value: title});
    if (el.id && !looksDynamic(el.id)) c.push({kind: 'css', value: '#' + CSS.escape(el.id)});
    const nm = el.getAttribute('name');
    if (nm) c.push({kind: 'css', value: `${tag}[name="${nm}"]`});
    c.push({kind: 'css', value: cssPath(el), fallback: true});
    return c;
  }

  document.addEventListener('click', (e) => {
    let el = e.target;
    if (!(el instanceof Element)) return;
    el = el.closest(INTERACTIVE) || el;  // svg/span inside a button -> the button
    document.querySelectorAll('[data-pw-picked]').forEach(n => n.removeAttribute('data-pw-picked'));
    el.setAttribute('data-pw-picked', '1');
    const info = {
      tag: el.tagName.toLowerCase(),
      outerHTML: el.outerHTML.slice(0, 200),
      candidates: candidates(el),
    };
    window.__pwRecord(info);
  }, true);
})();
"""


def build(frame, c):
    """Return (Locator, python_code) for a candidate."""
    k = c["kind"]
    if k == "testid":
        return frame.get_by_test_id(c["value"]), f"page.get_by_test_id({c['value']!r})"
    if k == "role":
        return (frame.get_by_role(c["role"], name=c["name"], exact=True),
                f"page.get_by_role({c['role']!r}, name={c['name']!r}, exact=True)")
    if k == "label":
        return frame.get_by_label(c["value"], exact=True), f"page.get_by_label({c['value']!r}, exact=True)"
    if k == "placeholder":
        return frame.get_by_placeholder(c["value"], exact=True), f"page.get_by_placeholder({c['value']!r}, exact=True)"
    if k == "alt":
        return frame.get_by_alt_text(c["value"], exact=True), f"page.get_by_alt_text({c['value']!r}, exact=True)"
    if k == "text":
        return frame.get_by_text(c["value"], exact=True), f"page.get_by_text({c['value']!r}, exact=True)"
    if k == "title":
        return frame.get_by_title(c["value"], exact=True), f"page.get_by_title({c['value']!r}, exact=True)"
    return frame.locator(c["value"]), f"page.locator({c['value']!r})"


def is_the_clicked_element(loc):
    """Locator must match exactly one element, and it must be the one just clicked."""
    try:
        if loc.count() != 1:
            return False
        return loc.evaluate("e => e.hasAttribute('data-pw-picked')")
    except Exception:
        return False


records = []


def on_record(source, info):
    frame = source["frame"]
    chosen = None
    for c in info["candidates"]:
        loc, code = build(frame, c)
        if is_the_clicked_element(loc):
            chosen = {"strategy": c["kind"] + (" (fallback)" if c.get("fallback") else ""), "locator": code}
            break
    if chosen is None:
        chosen = {"strategy": "none", "locator": None}
    entry = {"element": info["outerHTML"], "frame_url": frame.url, **chosen}
    records.append(entry)
    print(f"\n[{len(records)}] <{info['tag']}>  via {chosen['strategy']}\n    {chosen['locator']}")
    with open("recorded_locators.json", "w") as f:
        json.dump(records, f, indent=2)


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.expose_binding("__pwRecord", on_record)
        context.add_init_script(INIT_JS)
        page = context.new_page()
        page.goto(url)
        print("Recording... click elements in the browser. Close the window or Ctrl+C to stop.")
        try:
            page.wait_for_event("close", timeout=0)
        except KeyboardInterrupt:
            pass
        browser.close()
    print(f"\nSaved {len(records)} locators to recorded_locators.json")


if __name__ == "__main__":
    main()
