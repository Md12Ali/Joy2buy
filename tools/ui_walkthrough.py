#!/usr/bin/env python3
"""
Scripted run of the browser-level cases in TESTING.md's manual test plan.

Each case follows the written steps in headless Chromium, clicking and
typing as a person would, and records what actually happened next to what
was expected. It is a repeatable record, not a replacement for trying the
site by hand: cases that need human judgement are left to the manual run.

    JOY2BUY_CUSTOMER_USER=... JOY2BUY_CUSTOMER_PASSWORD=... \\
    JOY2BUY_STAFF_USER=... JOY2BUY_STAFF_PASSWORD=... \\
    python tools/ui_walkthrough.py --base-url http://127.0.0.1:8000/

Intended for a local or staging copy with the seed_store catalogue. It
places one order (then cancels it, returning the stock), writes and
deletes one review, and restores any profile detail it changes.
"""
import argparse
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_checks import mirror_cdn  # noqa: E402

DELIVERY = {
    "Full name": "QA Customer",
    "Email": "qa.customer@example.com",
    "Phone": "07700 900123",
    "Address line 1": "1 Test Street",
    "Town or city": "Leeds",
    "Postcode": "LS1 4AP",
}


class Walkthrough:
    def __init__(self, args, browser):
        self.args = args
        self.browser = browser
        self.rows = []

    def url(self, path=""):
        return urljoin(self.args.base_url, path)

    def context(self, javascript=True):
        context = self.browser.new_context(
            java_script_enabled=javascript,
            viewport={"width": 1280, "height": 900},
        )
        if self.args.npm_mirror:
            mirror_cdn(context, self.args.npm_mirror)
        context.set_default_timeout(8000)
        return context

    def signed_in(self, role, javascript=True):
        context = self.context(javascript)
        page = context.new_page()
        page.goto(self.url("account/login/"))
        page.fill("input[name=username]",
                  os.environ[f"JOY2BUY_{role.upper()}_USER"])
        page.fill("input[name=password]",
                  os.environ[f"JOY2BUY_{role.upper()}_PASSWORD"])
        page.click("main form button[type=submit]")
        page.wait_for_load_state()
        return page

    def case(self, number, title):
        """Decorator: run a case and record PASS/FAIL with its notes."""
        def wrap(function):
            print(f"-- {number}. {title}")
            notes = []
            try:
                function(notes)
                result = "PASS"
            except (AssertionError, PlaywrightError) as error:
                detail = (str(error).splitlines() or ["check failed"])[0]
                notes.append(f"FAILED: {detail[:160]}")
                result = "FAIL"
            print(f"   {result}: {'; '.join(notes)}")
            self.rows.append((number, title, result, "; ".join(notes)))
            return function
        return wrap


def stock_shown(page):
    """The stock figure printed on a product page."""
    text = page.inner_text("main")
    match = re.search(r"\((\d+) available\)|only (\d+) left", text)
    return int(match[1] or match[2])


def badge(page):
    return int(page.locator("#cart-count-number").inner_text())


def empty_cart(page, base):
    """Remove every cart line through the normal confirm dialog."""
    page.goto(urljoin(base, "cart/"))
    for _ in range(20):
        if not page.locator("form.js-cart-remove").count():
            return
        page.locator("form.js-cart-remove button").first.click()
        accept = page.locator("#confirm-modal-accept")
        expect(accept).to_be_visible()
        accept.click()
        page.wait_for_load_state("networkidle")
        page.reload()
    raise AssertionError("cart could not be emptied")


def run(args):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        walk = Walkthrough(args, browser)
        base = args.base_url
        public = walk.context().new_page()

        @walk.case(1, "Every navbar and footer link opens without error")
        def _(notes):
            public.goto(base)
            hrefs = set(public.eval_on_selector_all(
                "header a[href], footer a[href]",
                "links => links.map(a => a.href)"))
            local = sorted(h for h in hrefs if h.startswith(base))
            external = [h for h in hrefs if not h.startswith(base)
                        and h.startswith("http")]
            bad = []
            for href in local:
                status = public.request.get(href).status
                if status != 200:
                    bad.append(f"{href} {status}")
            ext_new_tab = public.eval_on_selector_all(
                "header a[href^=http], footer a[href^=http]",
                f"""links => links.filter(a => !a.href.startsWith(
                    {base!r})).every(a => a.target === '_blank'
                    && a.rel.includes('noopener'))""")
            notes.append(f"{len(local)} site links all 200; "
                         f"{len(external)} external links open in a new tab")
            assert not bad, bad
            assert ext_new_tab, "external link without target=_blank"

        @walk.case(3, "Home page shows hero, category tabs and products")
        def _(notes):
            public.goto(base)
            cards = public.locator(".product-name").count()
            tabs = public.locator(".category-tabs .nav-link").count()
            notes.append(f"hero shown; {tabs} tabs; {cards} product cards")
            expect(public.locator(".hero")).to_be_visible()
            assert tabs >= 2 and cards > 0

        @walk.case(4, "Choosing a category tab filters the products")
        def _(notes):
            public.goto(base)
            tab = public.locator(".category-tabs .nav-link").nth(1)
            name = tab.inner_text().strip()
            tab.click()
            public.wait_for_load_state()
            labels = {t.strip().lower() for t in public.locator(
                ".product-category").all_inner_texts()}
            active = public.locator(
                ".category-tabs .nav-link.active").inner_text().strip()
            count = public.locator(".product-name").count()
            notes.append(f"tab '{name}': {count} products, categories "
                         f"shown {sorted(labels)}, active tab '{active}'")
            assert labels == {name.lower()} and active == name

        @walk.case(5, "Typing in search shows suggestions; choosing one "
                      "opens the product")
        def _(notes):
            public.goto(base)
            box = public.locator("#site-search")
            box.click()
            box.press_sequentially("b", delay=150)
            public.wait_for_timeout(600)
            hidden_after_one = public.locator(
                "#search-suggestions").is_hidden()
            box.press_sequentially("ottle", delay=150)
            first = public.locator("#search-suggestions a").first
            expect(first).to_be_visible()
            names = public.locator("#search-suggestions a span")
            count = names.count()
            suggestion = names.first.inner_text()
            first.click()
            public.wait_for_load_state()
            heading = public.locator("h1").inner_text()
            notes.append(f"no list after 1 letter: {hidden_after_one}; "
                         f"{count} suggestions; chose "
                         f"'{suggestion}', opened '{heading}'")
            assert hidden_after_one and heading == suggestion

        @walk.case(6, "Searching for 'zzzz' explains there are no matches")
        def _(notes):
            public.goto(urljoin(base, "?q=zzzz"))
            text = public.locator("main").inner_text()
            notes.append("'No products match your search' shown with a "
                         "link back" if "No products match" in text
                         else "message missing")
            assert "No products match your search" in text

        @walk.case(7, "Sort by price and 'in stock only' re-order and "
                      "filter the list")
        def _(notes):
            public.goto(base)
            public.select_option("#filter-sort", "price_low")
            public.wait_for_load_state()
            public.check("#filter-available")
            public.wait_for_load_state()
            prices = [float(p.replace("£", "").replace(",", ""))
                      for p in public.locator(".product-price")
                      .all_inner_texts()]
            sold_out = public.locator("button:has-text('Out of stock')")
            notes.append(f"URL {public.url.split('/', 3)[-1]}; prices "
                         f"{prices[:4]}...; out-of-stock cards: "
                         f"{sold_out.count()}")
            assert prices == sorted(prices) and sold_out.count() == 0

        @walk.case(9, "An out-of-stock product cannot be added")
        def _(notes):
            public.goto(urljoin(base, "?q=Tempo"))
            public.locator(".product-name a").first.click()
            public.wait_for_load_state()
            text = public.locator("main").inner_text()
            forms = public.locator(
                "form.js-cart-add:has(#detail-quantity)").count()
            notes.append(f"'Out of stock' shown: {'Out of stock' in text}; "
                         f"product add-to-cart forms: {forms}")
            assert "Out of stock" in text and forms == 0

        @walk.case(10, "Adding from the grid updates the badge without a "
                       "reload")
        def _(notes):
            public.goto(base)
            before = badge(public)
            public.evaluate("window.__marker = 1")
            public.locator(".product-card form.js-cart-add button").first\
                .click()
            expect(public.locator("#message-container .alert-success"))\
                .to_be_visible()
            same_page = public.evaluate("window.__marker === 1")
            message = public.locator(
                "#message-container .alert-success").inner_text()
            notes.append(f"badge {before} -> {badge(public)}; page not "
                         f"reloaded: {same_page}; message '{message.strip()}'")
            assert badge(public) == before + 1 and same_page

        @walk.case(13, "Changing a quantity updates line total and totals "
                       "immediately")
        def _(notes):
            public.goto(urljoin(base, "cart/"))
            line_total = public.locator("[data-line-total]").first
            before = line_total.inner_text()
            subtotal_before = public.locator(
                "[data-cart-subtotal]").inner_text()
            public.evaluate("window.__marker = 1")
            quantity = public.locator(
                ".js-cart-update input[name=quantity]").first
            quantity.fill("2")
            quantity.dispatch_event("change")
            expect(line_total).not_to_have_text(before)
            notes.append(
                f"line {before} -> {line_total.inner_text()}; subtotal "
                f"{subtotal_before} -> "
                f"{public.locator('[data-cart-subtotal]').inner_text()}; "
                f"no reload: {public.evaluate('window.__marker === 1')}")

        @walk.case(15, "A subtotal of £50 or more makes delivery free")
        def _(notes):
            quantity = public.locator(
                ".js-cart-update input[name=quantity]").first
            delivery = public.locator("[data-cart-delivery]")
            for value in range(2, 21):
                subtotal = float(public.locator("[data-cart-subtotal]")
                                 .inner_text().strip("£").replace(",", ""))
                if subtotal >= 50:
                    break
                quantity.fill(str(value + 1))
                quantity.dispatch_event("change")
                public.wait_for_timeout(700)
            notes.append(f"subtotal £{subtotal:.2f}, delivery shows "
                         f"'{delivery.inner_text()}'")
            assert subtotal >= 50 and delivery.inner_text() == "Free"

        @walk.case(14, "Remove asks for confirmation, then removes the line")
        def _(notes):
            lines = public.locator("[data-cart-line]").count()
            public.locator("form.js-cart-remove button").first.click()
            modal = public.locator("#confirm-modal")
            expect(modal).to_be_visible()
            question = public.locator("#confirm-modal-text").inner_text()
            public.click("#confirm-modal-accept")
            expect(public.locator("[data-cart-line]")).to_have_count(
                lines - 1)
            notes.append(f"modal asked '{question}'; lines {lines} -> "
                         f"{lines - 1}")

        @walk.case(16, "Cart add, update and remove work with JavaScript "
                       "switched off")
        def _(notes):
            page = walk.context(javascript=False).new_page()
            page.goto(urljoin(base, "?q=Pulse"))
            page.locator(".product-card form.js-cart-add button").first\
                .click()
            page.wait_for_load_state()
            added = page.locator(".alert-success").inner_text().strip()
            page.goto(urljoin(base, "cart/"))
            page.fill(".js-cart-update input[name=quantity]", "3")
            page.locator(".js-cart-update button[type=submit]").click()
            page.wait_for_load_state()
            updated = page.locator(".alert-success").inner_text().strip()
            page.locator("form.js-cart-remove button").click()
            page.wait_for_load_state()
            removed = page.locator(".alert-success").inner_text().strip()
            left = page.locator("[data-cart-line]").count()
            notes.append(f"'{added}' / '{updated}' / '{removed}'; lines "
                         f"left {left}")
            assert left == 0
            page.context.close()

        @walk.case(17, "Registering with mismatched passwords is refused")
        def _(notes):
            page = walk.context().new_page()
            page.goto(urljoin(base, "account/signup/"))
            page.fill("input[name=username]", "qa_never_created")
            page.fill("input[name=first_name]", "Never")
            page.fill("input[name=last_name]", "Created")
            page.fill("input[name=email]", "qa.never@example.com")
            page.fill("input[name=password1]", "Strong-Passphrase-1")
            page.fill("input[name=password2]", "Different-Passphrase-2")
            page.locator("main form button[type=submit]").click()
            page.wait_for_load_state()
            errors = page.locator(".invalid-feedback").all_inner_texts()
            shown = " | ".join(error.strip()[:60] for error in errors[:2])
            notes.append(f"errors: {shown}")
            assert "/account/signup/" in page.url
            assert any("match" in error for error in errors), errors
            page.context.close()

        @walk.case(19, "Signing in with a wrong password is refused")
        def _(notes):
            page = walk.context().new_page()
            page.goto(urljoin(base, "account/login/"))
            page.fill("input[name=username]",
                      os.environ["JOY2BUY_CUSTOMER_USER"])
            page.fill("input[name=password]", "not-the-password")
            page.click("main form button[type=submit]")
            page.wait_for_load_state()
            error = page.locator(".alert-danger, .invalid-feedback")\
                .first.inner_text().strip()
            notes.append(f"stayed on sign-in page with '{error[:80]}'")
            assert "/account/login/" in page.url
            page.context.close()

        @walk.case(20, "Checkout while signed out goes to sign in, then "
                       "back to checkout with the cart kept")
        def _(notes):
            page = walk.context().new_page()
            page.goto(urljoin(base, "?q=Pulse"))
            page.locator(".product-card form.js-cart-add button").first\
                .click()
            expect(page.locator("#cart-count-number")).to_have_text("1")
            page.goto(urljoin(base, "orders/checkout/"))
            at_login = "/account/login/" in page.url
            page.fill("input[name=username]",
                      os.environ["JOY2BUY_CUSTOMER_USER"])
            page.fill("input[name=password]",
                      os.environ["JOY2BUY_CUSTOMER_PASSWORD"])
            page.click("main form button[type=submit]")
            page.wait_for_load_state()
            notes.append(f"sent to sign in: {at_login}; then at "
                         f"/{page.url.split('/', 3)[-1]} with "
                         f"{badge(page)} item(s) in cart")
            assert at_login and "/orders/checkout/" in page.url
            assert "Pulse" in page.locator("main").inner_text()
            empty_cart(page, base)
            page.context.close()

        customer = walk.signed_in("customer")
        staff = walk.signed_in("staff")
        order_url = {}

        @walk.case(21, "Checkout with a blank phone and bad postcode "
                       "creates no order")
        def _(notes):
            empty_cart(customer, base)
            customer.goto(urljoin(base, "?q=Pulse"))
            customer.locator(".product-card form.js-cart-add button").first\
                .click()
            expect(customer.locator("#cart-count-number")).to_have_text("1")
            customer.goto(urljoin(base, "orders/checkout/"))
            for label, value in DELIVERY.items():
                customer.get_by_label(label, exact=False).first.fill(value)
            customer.get_by_label("Phone", exact=False).first.fill("")
            customer.get_by_label("Postcode", exact=False).first.fill("!!")
            customer.locator("main form button[type=submit]").click()
            customer.wait_for_load_state()
            errors = customer.locator(".invalid-feedback").count()
            notes.append(f"still on checkout; {errors} field errors shown")
            assert "/orders/checkout/" in customer.url and errors >= 2

        @walk.case(22, "A valid order shows a reference, empties the cart "
                       "and reduces stock")
        def _(notes):
            customer.goto(urljoin(base, "?q=Pulse"))
            customer.locator(".product-name a").first.click()
            stock_before = stock_shown(customer)
            product_url = customer.url
            customer.goto(urljoin(base, "orders/checkout/"))
            for label, value in DELIVERY.items():
                customer.get_by_label(label, exact=False).first.fill(value)
            customer.locator("main form button[type=submit]").click()
            customer.wait_for_load_state()
            order_url["url"] = customer.url
            reference = customer.url.rstrip("/").rsplit("/", 1)[-1]
            message = customer.locator(".alert-success").inner_text()
            customer.goto(product_url)
            stock_after = stock_shown(customer)
            notes.append(f"order {reference}: '{message.strip()[:50]}'; "
                         f"cart badge {badge(customer)}; stock "
                         f"{stock_before} -> {stock_after}")
            assert reference in message and badge(customer) == 0
            assert stock_after == stock_before - 1

        @walk.case(23, "The new order is listed on the dashboard as "
                       "Pending")
        def _(notes):
            customer.goto(urljoin(base, "account/"))
            reference = order_url["url"].rstrip("/").rsplit("/", 1)[-1]
            row = customer.locator("tr", has_text=reference)
            notes.append(f"row: {row.inner_text().split()[:6]}")
            expect(row).to_contain_text("Pending")

        @walk.case(35, "Staff mark the order Shipped; the customer can no "
                       "longer cancel")
        def _(notes):
            staff.goto(order_url["url"])
            staff.select_option("select[name=status]", "shipped")
            staff.click("text=Save status")
            staff.wait_for_load_state()
            message = staff.locator(".alert-success").inner_text().strip()
            customer.goto(order_url["url"])
            cancel = customer.locator("text=Cancel this order").count()
            notes.append(f"staff saw '{message}'; customer cancel buttons: "
                         f"{cancel}")
            assert "shipped" in message and cancel == 0
            staff.goto(order_url["url"])
            staff.select_option("select[name=status]", "processing")
            staff.click("text=Save status")

        @walk.case(24, "Cancelling a pending/processing order restores "
                       "stock")
        def _(notes):
            customer.goto(urljoin(base, "?q=Pulse"))
            customer.locator(".product-name a").first.click()
            product_url = customer.url
            stock_before = stock_shown(customer)
            customer.goto(order_url["url"])
            customer.click("text=Cancel this order")
            customer.click("#confirm-modal-accept")
            customer.wait_for_load_state()
            status = customer.locator("main").inner_text()
            customer.goto(product_url)
            stock_after = stock_shown(customer)
            notes.append(f"status Cancelled: {'Cancelled' in status}; "
                         f"stock {stock_before} -> {stock_after}")
            assert "Cancelled" in status and stock_after == stock_before + 1

        review_page = {}

        @walk.case(26, "A review without a rating is refused")
        def _(notes):
            customer.goto(urljoin(base, "?q=Gel Pen"))
            customer.locator(".product-name a").first.click()
            review_page["url"] = customer.url
            customer.fill("textarea[name=text]", "Smooth pens, bright "
                          "colours, no smudging.")
            customer.locator("form[action$='/review/'] button").click()
            customer.wait_for_load_state()
            text = customer.locator("main").inner_text()
            notes.append("'Please choose a star rating.' shown"
                         if "Please choose a star rating." in text
                         else "message missing")
            assert "Please choose a star rating." in text

        @walk.case(27, "A valid review appears and editing replaces it")
        def _(notes):
            customer.goto(review_page["url"])
            customer.select_option("select[name=rating]", "5")
            customer.fill("textarea[name=text]", "Smooth pens, bright "
                          "colours, no smudging.")
            customer.locator("form[action$='/review/'] button").click()
            customer.wait_for_load_state()
            first = customer.locator(".alert-success").inner_text().strip()
            customer.select_option("select[name=rating]", "3")
            customer.fill("textarea[name=text]", "Good pens, but two "
                          "colours dried out quickly.")
            customer.locator("form[action$='/review/'] button").click()
            customer.wait_for_load_state()
            second = customer.locator(".alert-success").inner_text().strip()
            reviews = customer.locator("text=dried out quickly").count()
            old = customer.locator("text=no smudging").count()
            notes.append(f"'{first}' then '{second}'; edited text shown: "
                         f"{reviews}, old text left: {old}")
            assert reviews >= 1 and old == 0

        @walk.case(28, "Deleting your own review asks first, then removes "
                       "it")
        def _(notes):
            customer.locator("form[action*='/reviews/'] button").first\
                .click()
            expect(customer.locator("#confirm-modal")).to_be_visible()
            customer.click("#confirm-modal-accept")
            customer.wait_for_load_state()
            left = customer.locator("text=dried out quickly").count()
            notes.append(f"modal shown; review left on page: {left}")
            assert left == 0

        @walk.case(29, "Updating the profile is confirmed and pre-fills "
                       "checkout")
        def _(notes):
            customer.goto(urljoin(base, "account/edit/"))
            city = customer.get_by_label("Town or city", exact=False).first
            original = city.input_value()
            city.fill("York")
            customer.click("text=Save changes")
            customer.wait_for_load_state()
            message = customer.locator(".alert-success").inner_text().strip()
            customer.goto(urljoin(base, "?q=Pulse"))
            customer.locator(".product-card form.js-cart-add button").first\
                .click()
            expect(customer.locator("#cart-count-number")).to_have_text("1")
            customer.goto(urljoin(base, "orders/checkout/"))
            prefilled = customer.get_by_label(
                "Town or city", exact=False).first.input_value()
            empty_cart(customer, base)
            customer.goto(urljoin(base, "account/edit/"))
            customer.get_by_label("Town or city", exact=False).first.fill(
                original)
            customer.click("text=Save changes")
            notes.append(f"'{message}'; checkout city pre-filled with "
                         f"'{prefilled}'; restored to '{original}'")
            assert prefilled == "York"

        @walk.case(30, "Saving to and removing from the wishlist toggles "
                       "the button and the dashboard")
        def _(notes):
            customer.goto(review_page["url"])
            button = customer.locator("form.js-wishlist button")
            start = button.inner_text()
            button.click()
            expect(button).not_to_have_text(start)
            middle = button.inner_text()
            customer.goto(urljoin(base, "account/"))
            listed = "Gel Pen" in customer.locator(
                "#wishlist-heading >> xpath=..").inner_text()
            customer.goto(review_page["url"])
            customer.locator("form.js-wishlist button").click()
            expect(customer.locator("form.js-wishlist button"))\
                .to_have_text(start)
            notes.append(f"'{start}' -> '{middle}' -> '{start}'; on "
                         f"dashboard while saved: {listed}")
            assert listed

        @walk.case(31, "A customer visiting /manage/ gets the 403 page")
        def _(notes):
            response = customer.goto(urljoin(base, "manage/"))
            heading = customer.locator("h1").inner_text()
            notes.append(f"HTTP {response.status}, '{heading}'")
            assert response.status == 403

        @walk.case(32, "A 3 MB image is rejected in the browser and, with "
                       "JavaScript off, by the server")
        def _(notes):
            from PIL import Image
            big = Path(tempfile.mkdtemp(), "too-big.png")
            Image.frombytes("RGB", (1100, 1100),
                            os.urandom(1100 * 1100 * 3)).save(big)
            size = big.stat().st_size / 1024 / 1024
            # With JavaScript: the file is refused as soon as it is chosen.
            staff.goto(urljoin(base, "manage/products/add/"))
            staff.set_input_files("input[name=image]", str(big))
            alert = staff.locator("#message-container .alert-danger")
            expect(alert).to_be_visible()
            cleared = staff.locator("input[name=image]").input_value() == ""
            browser_message = alert.inner_text().strip()
            # Without JavaScript: the server must refuse it.
            name = "QA oversized image test"
            page = walk.signed_in("staff", javascript=False)
            page.goto(urljoin(base, "manage/products/add/"))
            page.select_option("select[name=category]", index=1)
            page.fill("input[name=name]", name)
            page.fill("textarea[name=description]",
                      "A product that should never be saved.")
            page.fill("input[name=price]", "5.00")
            page.fill("input[name=stock]", "1")
            page.select_option("select[name=status]", "draft")
            page.set_input_files("input[name=image]", str(big))
            page.locator("main form button[type=submit]").click()
            page.wait_for_load_state()
            server_errors = page.locator(".invalid-feedback")\
                .all_inner_texts()
            page.goto(urljoin(base, f"manage/?q={name}"))
            saved = name in page.locator("main").inner_text()
            page.context.close()
            notes.append(f"{size:.1f} MB file. Browser: '{browser_message}'"
                         f", file cleared: {cleared}. Server (JS off): "
                         f"{server_errors}; product saved: {saved}")
            assert cleared and "larger than 2 MB" in browser_message
            assert "Image files must be 2 MB or smaller." in server_errors
            assert not saved

        @walk.case(36, "An unknown address shows the custom 404 page")
        def _(notes):
            response = public.goto(urljoin(base, "no-such-page/"))
            links = public.locator("main a.btn").all_inner_texts()
            notes.append(f"HTTP {response.status}, links {links}")
            assert response.status == 404 and "Back to the shop" in links

        browser.close()

    print("\n| # | Case | Result | What happened |\n| --- | --- | --- | --- |")
    for row in walk.rows:
        print("| " + " | ".join(str(cell) for cell in row) + " |")
    failed = [row for row in walk.rows if row[2] == "FAIL"]
    print(f"\n{len(walk.rows) - len(failed)} of {len(walk.rows)} cases "
          f"passed; {len(failed)} failed.")
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/")
    parser.add_argument("--npm-mirror", help="See browser_checks.py")
    args = parser.parse_args()
    if not args.base_url.endswith("/"):
        args.base_url += "/"
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
