#!/usr/bin/env python3
"""
Verify a JOY2BUY deployment end to end with controlled test records.

Signed in as a staff member, the script creates, reads, updates and deletes
a test category and a test product whose names start with "QA test" and
end with a timestamp. After every step it checks two things:

- Immediate feedback: the page returned straight after the action shows
  the expected success message.
- Persistence: a brand-new session (signed in again from scratch) sees the
  change, so it was saved to the database and not just shown once.

The test product is created as a Draft, so shoppers never see it; the
script also confirms that a signed-out visitor gets 404 for it. Everything
it creates is deleted again, even if a step fails.

As a customer it adds a product to the cart, changes the quantity and
removes it (session only; no order is placed).

For an https:// site it also checks the production settings visible from
outside: HTTP redirects to HTTPS, HSTS and other security headers, Secure
cookies, and that error pages do not show Django's debug page.

    JOY2BUY_STAFF_USER=... JOY2BUY_STAFF_PASSWORD=... \\
    JOY2BUY_CUSTOMER_USER=... JOY2BUY_CUSTOMER_PASSWORD=... \\
    python tools/deployment_check.py --base-url https://<your-app>/

Exits with status 1 if any check fails.
"""
import argparse
import html
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_site import USER_AGENT, Browser  # noqa: E402


class Checks:
    def __init__(self):
        self.rows = []

    def record(self, step, check, passed, detail=""):
        result = "PASS" if passed else "FAIL"
        self.rows.append((step, check, result, detail))
        suffix = f" ({detail})" if detail else ""
        print(f"   {result} {step}: {check}{suffix}")
        return passed

    def skip(self, step, reason):
        self.rows.append((step, "-", "SKIPPED", reason))
        print(f"   SKIPPED {step}: {reason}")


def text(body):
    """Page text with HTML entities decoded, for matching messages."""
    return html.unescape(body)


def signed_in(base_url, role):
    user = os.environ.get(f"JOY2BUY_{role.upper()}_USER")
    password = os.environ.get(f"JOY2BUY_{role.upper()}_PASSWORD")
    if not (user and password):
        return None
    browser = Browser(base_url)
    return browser if browser.login(user, password) else False


def find(pattern, body):
    match = re.search(pattern, body)
    return match.group(1) if match else None


def staff_crud(args, checks):
    staff = signed_in(args.base_url, "staff")
    if staff is None:
        checks.skip("staff CRUD", "JOY2BUY_STAFF_USER/_PASSWORD not set")
        return
    if not checks.record("sign in", "staff account signs in", bool(staff)):
        return

    def fresh_staff():
        """A new session, so only saved data can be seen."""
        return signed_in(args.base_url, "staff")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    category_name = f"QA test category {stamp}"
    product_name = f"QA test product {stamp}"
    category_slug = product_slug = None
    try:
        # Create category.
        _, _, body = staff.post(
            "manage/categories/add/",
            {"name": category_name, "description": "Deployment check."},
            token_from="manage/categories/add/",
        )
        checks.record(
            "create category", "success message shown immediately",
            f'The "{category_name}" category has been added.' in text(body))
        _, _, manage = fresh_staff().get("manage/")
        category_slug = find(
            r'/manage/categories/([\w-]+)/edit/"[^>]*aria-label="Edit '
            + re.escape(category_name), text(manage))
        checks.record("create category", "saved (seen in a new session)",
                      category_slug is not None)

        # Create product in it, as a draft.
        _, _, form = staff.get("manage/products/add/")
        category_id = find(
            r'<option value="(\d+)"[^>]*>' + re.escape(category_name),
            text(form))
        url, _, body = staff.post(
            "manage/products/add/",
            {
                "category": category_id or "",
                "name": product_name,
                "description": "Created by tools/deployment_check.py.",
                "specifications": "Purpose: deployment check",
                "price": "9.99",
                "stock": "3",
                "status": "draft",
            },
            token_from="manage/products/add/",
        )
        checks.record(
            "create product", "success message shown immediately",
            f'"{product_name}" has been added.' in text(body))
        product_slug = find(r"/products/([\w-]+)/", url)
        _, status, body = fresh_staff().get(f"products/{product_slug}/")
        checks.record(
            "create product", "saved (seen in a new session)",
            status == 200 and product_name in text(body))
        _, status, _ = Browser(args.base_url).get(f"products/{product_slug}/")
        checks.record("create product",
                      "draft is hidden from signed-out visitors (404)",
                      status == 404, f"HTTP {status}")

        # Update product.
        _, _, body = staff.post(
            f"manage/products/{product_slug}/edit/",
            {
                "category": category_id or "",
                "name": product_name,
                "description": "Updated by tools/deployment_check.py.",
                "specifications": "Purpose: deployment check",
                "price": "12.34",
                "stock": "5",
                "status": "draft",
            },
            token_from=f"manage/products/{product_slug}/edit/",
        )
        checks.record(
            "update product", "success message shown immediately",
            f'"{product_name}" has been updated.' in text(body))
        _, _, body = fresh_staff().get(f"products/{product_slug}/")
        checks.record("update product", "new price saved (new session)",
                      "£12.34" in text(body))
    finally:
        # Delete product, then category - always, so nothing is left over.
        if product_slug:
            _, _, body = staff.post(
                f"manage/products/{product_slug}/delete/", {},
                token_from=f"manage/products/{product_slug}/delete/",
            )
            checks.record(
                "delete product", "success message shown immediately",
                f'"{product_name}" has been deleted.' in text(body))
            _, status, _ = fresh_staff().get(f"products/{product_slug}/")
            checks.record("delete product", "gone (404 in a new session)",
                          status == 404, f"HTTP {status}")
        if category_slug:
            _, _, body = staff.post(
                f"manage/categories/{category_slug}/delete/", {},
                token_from="manage/",
            )
            checks.record(
                "delete category", "success message shown immediately",
                f'The "{category_name}" category was deleted.' in text(body))
            _, _, manage = fresh_staff().get("manage/")
            checks.record("delete category", "gone (new session)",
                          category_name not in text(manage))


def customer_cart(args, checks):
    customer = signed_in(args.base_url, "customer")
    if customer is None:
        checks.skip("customer cart", "JOY2BUY_CUSTOMER_USER/_PASSWORD not "
                    "set")
        return
    if not checks.record("sign in", "customer account signs in",
                         bool(customer)):
        return
    _, _, home = customer.get("")
    product = find(r'"/products/([\w-]+)/"', home)
    page = f"products/{product}/"
    product_id = find(r'"/cart/add/(\d+)/"', customer.get(page)[2])
    _, _, body = customer.post(f"cart/add/{product_id}/", {"quantity": 1},
                               token_from=page)
    checks.record("cart", "add: confirmation message shown",
                  "was added to your cart." in text(body))
    _, _, body = customer.post(f"cart/update/{product_id}/",
                               {"quantity": 2}, token_from="cart/")
    checks.record("cart", "update: confirmation message shown",
                  "quantity updated to 2." in text(body))
    checks.record("cart", "update: quantity 2 kept on reload",
                  'value="2"' in customer.get("cart/")[2])
    _, _, body = customer.post(f"cart/remove/{product_id}/", {},
                               token_from="cart/")
    checks.record("cart", "remove: confirmation message shown",
                  "was removed from your cart." in text(body))
    checks.record("cart", "remove: line gone on reload",
                  f"/cart/remove/{product_id}/" not in customer.get(
                      "cart/")[2])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def production_settings(args, checks):
    if not args.base_url.startswith("https://"):
        checks.skip("production settings", "site is not served over HTTPS")
        return
    opener = urllib.request.build_opener(NoRedirect)
    http_url = "http://" + args.base_url[len("https://"):]
    try:
        opener.open(urllib.request.Request(
            http_url, headers={"User-Agent": USER_AGENT}), timeout=30)
        location, status = "", 200
    except urllib.error.HTTPError as error:
        location, status = error.headers.get("Location", ""), error.code
    checks.record("https", "HTTP redirects to HTTPS",
                  status in {301, 302, 307, 308}
                  and location.startswith("https://"),
                  f"HTTP {status} -> {location or 'no redirect'}")

    request = urllib.request.Request(
        args.base_url + "account/login/", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        headers = response.headers
    checks.record("headers", "Strict-Transport-Security set",
                  "max-age=" in headers.get("Strict-Transport-Security", ""),
                  headers.get("Strict-Transport-Security", "missing"))
    checks.record("headers", "X-Frame-Options is DENY",
                  headers.get("X-Frame-Options") == "DENY")
    checks.record("headers", "X-Content-Type-Options is nosniff",
                  headers.get("X-Content-Type-Options") == "nosniff")
    cookies = headers.get_all("Set-Cookie") or []
    csrf = [c for c in cookies if c.startswith("csrftoken=")]
    checks.record("cookies", "CSRF cookie marked Secure",
                  bool(csrf) and "secure" in csrf[0].lower())
    _, status, body = Browser(args.base_url).get("no-such-page-qa/")
    checks.record("debug", "404 page is the custom page, not Django debug",
                  status == 404 and "DEBUG = True" not in body
                  and "Using the URLconf" not in body, f"HTTP {status}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/")
    args = parser.parse_args()
    if not args.base_url.endswith("/"):
        args.base_url += "/"
    checks = Checks()
    print(f"Checking {args.base_url} at "
          f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    production_settings(args, checks)
    staff_crud(args, checks)
    customer_cart(args, checks)

    print("\n| Step | Check | Result | Detail |\n| --- | --- | --- | --- |")
    for row in checks.rows:
        print("| " + " | ".join(row) + " |")
    failed = [row for row in checks.rows if row[2] == "FAIL"]
    print(f"\n{len(checks.rows) - len(failed)} of {len(checks.rows)} checks "
          f"passed or were skipped; {len(failed)} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
