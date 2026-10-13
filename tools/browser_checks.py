#!/usr/bin/env python3
"""
Browser checks for JOY2BUY: responsive layout, keyboard use, WCAG contrast
and other automated accessibility rules, JavaScript errors and screenshots.

Every customer and staff page below is opened in headless Chromium at three
widths (390, 768 and 1440 px). For each one the script records:

- Responsive: whether the page scrolls sideways, and which elements stick
  out past the right edge if it does.
- Accessibility: the violations axe-core reports for WCAG 2.1 A and AA,
  which includes the colour-contrast rule (4.5:1 for normal text).
- Keyboard: tabbing through the whole page, that every visible control is
  reached, that each one shows a focus indicator, that the skip link is
  first and works, and that the mobile menu opens from the keyboard.
- JavaScript: any console error or uncaught exception.

It exits with status 1 if any check fails.

    pip install playwright && playwright install chromium
    npm pack axe-core@4.10.2 && tar xzf axe-core-4.10.2.tgz
    python tools/browser_checks.py --axe package/axe.min.js \\
        --screenshots assets/images/screenshots

Signed-in pages use the same environment variables as validate_site.py:
JOY2BUY_CUSTOMER_USER / _PASSWORD and JOY2BUY_STAFF_USER / _PASSWORD.
The script adds one item to the customer's session cart and changes
nothing else.
"""
import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

WIDTHS = {"mobile": (390, 844), "tablet": (768, 1024), "desktop": (1440, 900)}
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]

# Runs in the page: every visible element a keyboard user should reach.
FOCUSABLE_JS = """() => {
    const selector = 'a[href], button:not([disabled]), select:not([disabled]),'
        + ' textarea:not([disabled]), [tabindex],'
        + ' input:not([type=hidden]):not([disabled])';
    return [...document.querySelectorAll(selector)].filter(el => {
        const box = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        // tabindex="-1" deliberately removes a duplicate link from the
        // tab order (e.g. a product photo next to the linked name).
        return el.getAttribute('tabindex') !== '-1'
            && box.width > 0 && box.height > 0
            && style.visibility !== 'hidden' && !el.closest('[inert]')
            && !el.closest('.modal:not(.show)');
    }).map(el => el.outerHTML.slice(0, 80));
}"""

# Runs in the page: describe the focused element and whether focus shows.
ACTIVE_JS = """() => {
    const el = document.activeElement;
    if (!el || el === document.body) return null;
    const style = getComputedStyle(el);
    const outline = style.outlineStyle !== 'none'
        && parseFloat(style.outlineWidth) > 0;
    const ring = style.boxShadow && style.boxShadow !== 'none';
    return {html: el.outerHTML.slice(0, 80), text: el.innerText || '',
            visible: outline || ring};
}"""

OVERFLOW_JS = """() => {
    const width = document.documentElement.clientWidth;
    const scrollWidth = document.documentElement.scrollWidth;
    if (scrollWidth <= width + 1) return [];
    // Report the widest offenders that are not inside a scroll container.
    const scrolls = el => ['auto', 'scroll'].includes(
        getComputedStyle(el).overflowX);
    const culprits = [...document.querySelectorAll('body *')]
        .filter(el => el.getBoundingClientRect().right > width + 1)
        .filter(el => {
            for (let up = el.parentElement; up; up = up.parentElement) {
                if (scrolls(up)) return false;
            }
            return true;
        })
        .slice(-3).map(el => el.outerHTML.slice(0, 80));
    return [`page is ${scrollWidth}px wide in a ${width}px window`,
            ...culprits];
}"""


class Report:
    def __init__(self):
        self.rows = []

    def add(self, page, check, passed, detail=""):
        self.rows.append((page, check, "PASS" if passed else "FAIL", detail))
        mark = "PASS" if passed else "FAIL"
        print(f"   {mark} {check}{': ' + detail if detail else ''}")

    @property
    def failed(self):
        return [row for row in self.rows if row[2] == "FAIL"]


def mirror_cdn(context, mirror):
    """Answer cdn.jsdelivr.net/npm/<pkg>@<ver>/<file> from local copies."""
    def handle(route):
        path = urlparse(route.request.url).path
        match = re.match(r"/npm/([^@/]+)@[^/]+/(.+)", path)
        local = Path(mirror, *match.groups()) if match else None
        if local and local.is_file():
            route.fulfill(path=str(local))
        else:
            route.abort()
    context.route("https://cdn.jsdelivr.net/**", handle)


def sign_in(page, base_url, role):
    user = os.environ.get(f"JOY2BUY_{role.upper()}_USER")
    password = os.environ.get(f"JOY2BUY_{role.upper()}_PASSWORD")
    if not (user and password):
        return False
    page.goto(urljoin(base_url, "account/login/"))
    page.fill("input[name=username]", user)
    page.fill("input[name=password]", password)
    page.click("main form button[type=submit]")
    page.wait_for_load_state("networkidle")
    return "/account/login/" not in page.url


def first_href(page, pattern):
    for href in page.eval_on_selector_all(
        "a[href]", "links => links.map(a => a.getAttribute('href'))"
    ):
        if re.fullmatch(pattern, href):
            return href
    return None


def pages_for(page, base_url, role):
    """Return (name, path) pairs for the role, discovering example URLs."""
    page.goto(base_url)
    product = first_href(page, r"/products/[\w-]+/")
    if role == "public":
        return [("homepage", ""), ("product-detail", product),
                ("shopping-cart", "cart/"), ("sign-in", "account/login/")]
    if role == "customer":
        page.goto(urljoin(base_url, product))
        page.click("form[action*='/cart/add/'] button[type=submit]")
        page.wait_for_load_state("networkidle")
        page.goto(urljoin(base_url, "account/"))
        order = first_href(page, r"/orders/[0-9A-F]+/")
        return [("account", "account/"), ("shopping-cart-full", "cart/"),
                ("checkout", "orders/checkout/"), ("order-detail", order)]
    page.goto(urljoin(base_url, "manage/"))
    edit = first_href(page, r"/manage/products/[\w-]+/edit/")
    page.goto(urljoin(base_url, "orders/manage/"))
    order = first_href(page, r"/orders/[0-9A-F]+/")
    return [("staff-store-management", "manage/"),
            ("staff-edit-product", edit),
            ("staff-order-management", "orders/manage/"),
            ("staff-order-detail", order)]


def check_keyboard(page, report, name):
    """Tab through the page and check reach, focus visibility and traps."""
    expected = set(page.evaluate(FOCUSABLE_JS))
    # Start from the top of the document, as a user arriving at the page
    # would, even if a field has autofocus: focus a temporary element
    # placed before everything else, then remove it.
    page.evaluate("""() => {
        const start = document.createElement('span');
        start.tabIndex = -1;
        document.body.prepend(start);
        start.focus();
        start.remove();
    }""")
    reached, hidden_focus, first = [], [], None
    for _ in range(len(expected) + 5):
        page.keyboard.press("Tab")
        active = page.evaluate(ACTIVE_JS)
        if active is None:
            break
        if first is None:
            first = active
        elif active["html"] == first["html"]:
            break  # wrapped round to the start: the whole page was reached
        reached.append(active["html"])
        if not active["visible"]:
            hidden_focus.append(active["html"])
    missed = expected - set(reached)
    report.add(name, "keyboard: every visible control reachable by Tab",
               not missed, f"{len(reached)} reached" + (
                   f", missed {sorted(missed)[:3]}" if missed else ""))
    report.add(name, "keyboard: focus indicator visible on each control",
               not hidden_focus, ", ".join(hidden_focus[:3]))
    skip_first = bool(first) and "skip" in first["text"].lower()
    report.add(name, "keyboard: skip link is the first stop", skip_first,
               first["text"].strip()[:40] if first else "nothing focused")
    if skip_first:
        page.locator(".skip-link").focus()
        page.keyboard.press("Enter")
        in_main = page.evaluate(
            "() => !!document.activeElement.closest('main')")
        report.add(name, "keyboard: skip link moves focus into <main>",
                   in_main)


def check_mobile_menu(page, report, name):
    toggler = page.locator(".navbar-toggler")
    if not toggler.count():
        return
    toggler.focus()
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)
    opened = toggler.get_attribute("aria-expanded") == "true"
    report.add(name, "keyboard: mobile menu opens with Enter", opened)
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)


def check_axe(page, report, name, axe_source):
    page.add_script_tag(content=axe_source)
    result = page.evaluate(
        "tags => axe.run(document, {runOnly: {type: 'tag', values: tags}})",
        AXE_TAGS,
    )
    contrast = [v for v in result["violations"] if v["id"] == "color-contrast"]
    others = [v for v in result["violations"] if v["id"] != "color-contrast"]
    report.add(name, "contrast: WCAG AA colour-contrast (axe)",
               not contrast, "; ".join(
                   n["any"][0]["message"][:120]
                   for v in contrast for n in v["nodes"][:3]))
    report.add(name, f"axe: other WCAG 2.1 A/AA rules ({len(result['passes'])}"
               " rules passed)", not others,
               "; ".join(f"{v['id']} ({v['impact']}, {len(v['nodes'])} "
                         "nodes)" for v in others))


def run(args):
    report = Report()
    axe_source = Path(args.axe).read_text()
    js_errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for role in ("public", "customer", "staff"):
            context = browser.new_context()
            if args.npm_mirror:
                mirror_cdn(context, args.npm_mirror)
            page = context.new_page()
            page.on("pageerror", lambda error: js_errors.append(str(error)))
            page.on("console", lambda message: message.type == "error"
                    and js_errors.append(message.text))
            print(f"\n== {role} ==")
            if role != "public" and not sign_in(page, args.base_url, role):
                report.add(role, "sign in", False,
                           "credentials missing or rejected")
                context.close()
                continue
            for name, path in pages_for(page, args.base_url, role):
                if path is None:
                    report.add(name, "page exists", False,
                               "no example URL found")
                    continue
                for device, (width, height) in WIDTHS.items():
                    print(f"-- {name} at {width}px")
                    page.set_viewport_size({"width": width,
                                            "height": height})
                    page.goto(urljoin(args.base_url, path))
                    page.wait_for_load_state("networkidle")
                    label = f"{name} @{width}"
                    overflow = page.evaluate(OVERFLOW_JS)
                    report.add(label, "responsive: no sideways scrolling",
                               not overflow, ", ".join(overflow[:2]))
                    if args.screenshots:
                        folder = Path(args.screenshots, device)
                        folder.mkdir(parents=True, exist_ok=True)
                        page.screenshot(
                            path=folder / f"{device}-{name}.png",
                            full_page=True,
                        )
                    if device == "tablet":
                        continue
                    check_axe(page, report, label, axe_source)
                    if device == "mobile":
                        check_mobile_menu(page, report, label)
                    else:
                        check_keyboard(page, report, label)
            context.close()
        browser.close()
    report.add("all pages", "javascript: no console errors", not js_errors,
               "; ".join(js_errors[:3]))

    print("\n| Page | Check | Result | Detail |\n| --- | --- | --- | --- |")
    for row in report.rows:
        print("| " + " | ".join(row) + " |")
    print(f"\n{len(report.rows) - len(report.failed)} of {len(report.rows)} "
          f"checks passed; {len(report.failed)} failed.")
    return 1 if report.failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/")
    parser.add_argument("--axe", required=True,
                        help="Path to axe.min.js from the axe-core package")
    parser.add_argument("--screenshots",
                        help="Folder to save full-page screenshots in")
    parser.add_argument(
        "--npm-mirror",
        help="Serve cdn.jsdelivr.net/npm/<package>@<version>/<file> from "
             "<folder>/<package>/<file> (for networks that block the CDN)",
    )
    args = parser.parse_args()
    if not args.base_url.endswith("/"):
        args.base_url += "/"
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
