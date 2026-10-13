#!/usr/bin/env python3
"""
Validate the rendered HTML and CSS of JOY2BUY with the W3C Nu checker.

Every page is fetched exactly as a browser would receive it (signed in as a
customer or a staff member where the page needs it), then the markup is sent
to the Nu HTML Checker and the stylesheet to its CSS checker. Each message
the checker returns is printed, and the script exits with status 1 if any
page has an error or could not be fetched, so a failed validation can never
be mistaken for a pass.

Usage:

    python tools/validate_site.py --base-url http://127.0.0.1:8000/

Signed-in pages are checked only when credentials are supplied through
environment variables (never on the command line, where they would end up
in the shell history):

    JOY2BUY_CUSTOMER_USER, JOY2BUY_CUSTOMER_PASSWORD
    JOY2BUY_STAFF_USER, JOY2BUY_STAFF_PASSWORD

By default markup is sent to https://validator.w3.org/nu/. To work offline,
run the same checker locally (java -jar vnu.jar -Dnu.validator.servlet.bind-
address=127.0.0.1 nu.validator.servlet.Main 8888) and pass
--nu-url http://127.0.0.1:8888/. The script only reads pages and adds one
item to a session cart; it never places orders or changes stored data.
"""
import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "joy2buy-validate-site/1.0"
CSRF_RE = re.compile(r'name="csrfmiddlewaretoken" value="([^"]+)"')
STYLESHEET_RE = re.compile(r'href="([^"]*/css/style[^"]*\.css)"')


class Browser:
    """A minimal cookie-keeping HTTP client for one signed-in role."""

    def __init__(self, base_url):
        self.base_url = base_url
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )

    def url(self, path):
        return urllib.parse.urljoin(self.base_url, path)

    def get(self, path):
        """Return (final URL, status, body) for a GET request."""
        request = urllib.request.Request(
            self.url(path), headers={"User-Agent": USER_AGENT}
        )
        try:
            with self.opener.open(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                return response.geturl(), response.status, body
        except urllib.error.HTTPError as error:
            return self.url(path), error.code, error.read().decode("utf-8")

    def post(self, path, data, token_from):
        """POST a form, taking the CSRF token from the page ``token_from``."""
        _, _, page = self.get(token_from)
        match = CSRF_RE.search(page)
        if match:
            data = dict(data, csrfmiddlewaretoken=match.group(1))
        request = urllib.request.Request(
            self.url(path),
            data=urllib.parse.urlencode(data).encode(),
            headers={
                "User-Agent": USER_AGENT,
                "Referer": self.url(token_from),
            },
        )
        try:
            with self.opener.open(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                return response.geturl(), response.status, body
        except urllib.error.HTTPError as error:
            return self.url(path), error.code, error.read().decode("utf-8")

    def login(self, username, password):
        final_url, _, _ = self.post(
            "account/login/",
            {"username": username, "password": password},
            token_from="account/login/",
        )
        return "/account/login/" not in final_url


def check_with_nu(nu_url, content, content_type):
    """Send a document to the Nu checker and return its messages."""
    request = urllib.request.Request(
        nu_url.rstrip("/") + "/?out=json",
        data=content.encode("utf-8"),
        headers={
            "Content-Type": f"{content_type}; charset=utf-8",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["messages"]


def summarise(messages):
    """Split checker messages into errors and warnings."""
    error_types = {"error", "non-document-error"}
    errors = [m for m in messages if m["type"] in error_types]
    warnings = [m for m in messages if m.get("subType") == "warning"]
    return errors, warnings


def first_link(html, pattern):
    match = re.search(pattern, html)
    return match.group(0).strip('"') if match else None


def discover_pages(browser, role):
    """Return (label, path) pairs for every page this role should check."""
    _, _, home = browser.get("")
    product = first_link(home, r'"/products/[\w-]+/"')
    pages = [
        ("Product list (home)", ""),
        ("Search results", "?q=bottle"),
        ("Empty search", "?q=zzzz"),
        ("Product detail", product),
        ("Cart", "cart/"),
        ("Sign in", "account/login/"),
        ("Register", "account/signup/"),
        ("404 page", "no-such-page/"),
    ]
    if role == "public":
        return pages

    if role == "customer":
        _, _, dashboard = browser.get("account/")
        if product:
            product_id = first_link(
                browser.get(product)[2], r'"/cart/add/\d+/"'
            )
            if product_id:
                browser.post(product_id, {"quantity": 1}, token_from=product)
        return [
            ("Account dashboard", "account/"),
            ("Edit profile", "account/edit/"),
            ("Change password", "account/password/"),
            ("Cart with an item", "cart/"),
            ("Checkout", "orders/checkout/"),
            ("Order detail", first_link(dashboard, r'"/orders/[0-9A-F]+/"')),
        ]

    _, _, manage = browser.get("manage/")
    _, _, orders = browser.get("orders/manage/")
    edit = first_link(manage, r'"/manage/products/[\w-]+/edit/"')
    return [
        ("Store management", "manage/"),
        ("Add product", "manage/products/add/"),
        ("Edit product", edit),
        ("Delete product (confirm)",
         edit.replace("/edit/", "/delete/") if edit else None),
        ("Add category", "manage/categories/add/"),
        ("Edit category",
         first_link(manage, r'"/manage/categories/[\w-]+/edit/"')),
        ("Order management", "orders/manage/"),
        ("Order detail (staff)",
         first_link(orders, r'"/orders/[0-9A-F]+/"')),
    ]


def print_messages(messages):
    for message in messages:
        kind = message.get("subType") or message["type"]
        line = message.get("lastLine", "?")
        print(f"      [{kind}] line {line}: {message['message']}")


def run(args):
    results = []
    roles = [("public", None, None)]
    for role in ("customer", "staff"):
        user = os.environ.get(f"JOY2BUY_{role.upper()}_USER")
        password = os.environ.get(f"JOY2BUY_{role.upper()}_PASSWORD")
        roles.append((role, user, password))

    stylesheet = None
    for role, user, password in roles:
        print(f"\n== {role} pages ==")
        browser = Browser(args.base_url)
        if role != "public":
            if not (user and password):
                print("   SKIPPED: credentials not set in the environment")
                results.append((role, "(all pages)", "SKIPPED", 0, 0))
                continue
            if not browser.login(user, password):
                print("   FAILED: could not sign in")
                results.append((role, "Sign in", "FAILED", 1, 0))
                continue

        for label, path in discover_pages(browser, role):
            if path is None:
                print(f"   SKIPPED {label}: no example found on the site")
                results.append((role, label, "SKIPPED", 0, 0))
                continue
            final_url, status, html = browser.get(path)
            expected = 404 if label == "404 page" else 200
            if status != expected:
                print(f"   FAILED {label} ({path}): HTTP {status}")
                results.append((role, label, f"HTTP {status}", 1, 0))
                continue
            stylesheet = stylesheet or STYLESHEET_RE.search(html)
            errors, warnings = summarise(
                check_with_nu(args.nu_url, html, "text/html")
            )
            verdict = "PASS" if not errors else "FAIL"
            print(f"   {verdict:4} {label} /{path.lstrip('/')} - "
                  f"{len(errors)} errors, "
                  f"{len(warnings)} warnings")
            print_messages(errors + warnings)
            results.append((role, label, verdict, len(errors),
                            len(warnings)))

    print("\n== stylesheet ==")
    if stylesheet:
        css_path = stylesheet.group(1)
        _, status, css = Browser(args.base_url).get(css_path)
        errors, warnings = summarise(
            check_with_nu(args.nu_url, css, "text/css")
        )
        verdict = "PASS" if status == 200 and not errors else "FAIL"
        print(f"   {verdict:4} {css_path} - {len(errors)} errors, "
              f"{len(warnings)} warnings")
        print_messages(errors + warnings)
        results.append(("css", css_path, verdict, len(errors),
                        len(warnings)))
    else:
        print("   FAILED: style.css link not found on any page")
        results.append(("css", "style.css", "FAILED", 1, 0))

    failed = [row for row in results if row[2] not in {"PASS", "SKIPPED"}]
    print("\n| Role | Page | Result | Errors | Warnings |")
    print("| --- | --- | --- | --- | --- |")
    for row in results:
        print("| " + " | ".join(str(cell) for cell in row) + " |")
    print(f"\n{len(results) - len(failed)} of {len(results)} checks "
          f"passed or were skipped; {len(failed)} failed.")
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000/",
        help="Root of the site to check (default: %(default)s)",
    )
    parser.add_argument(
        "--nu-url",
        default="https://validator.w3.org/nu/",
        help="Nu HTML Checker endpoint (default: %(default)s)",
    )
    args = parser.parse_args()
    if not args.base_url.endswith("/"):
        args.base_url += "/"
    try:
        return run(args)
    except urllib.error.URLError as error:
        print(f"\nERROR: could not reach a server: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
