# JOY2BUY testing report

This report records how JOY2BUY was tested, the commands used, their actual output, the bugs that testing found and how each was fixed, and what is still untested or limited.

## Contents

1. [Summary and test environment](#1-summary-and-test-environment)
2. [Automated tests](#2-automated-tests)
3. [Code validation](#3-code-validation)
4. [Accessibility, keyboard, contrast and responsive checks](#4-accessibility-keyboard-contrast-and-responsive-checks)
5. [Manual test plan and results](#5-manual-test-plan-and-results)
6. [Production settings](#6-production-settings)
7. [Credential review](#7-credential-review)
8. [Deployment verification](#8-deployment-verification)
9. [Bugs found and fixed](#9-bugs-found-and-fixed)
10. [Known limitations](#10-known-limitations)

---

## 1. Summary and test environment

| Area | Tool / command | Result |
| --- | --- | --- |
| Unit and integration tests, SQLite | `python manage.py test` | 122 run: 119 pass, 3 skipped by design |
| Unit and integration tests, PostgreSQL | `DATABASE_URL=postgres://... python manage.py test` | 122 of 122 pass |
| Concurrency (8 parallel requests) | `SimultaneousCancellationTests` on PostgreSQL | Fails on the old code; passes on the fixed code, 10 runs out of 10 |
| PEP 8 | `python -m flake8` | 0 findings in the whole project |
| Migrations | `python manage.py makemigrations --check --dry-run` | No changes detected |
| JavaScript syntax | `node --check static/js/main.js` | No errors |
| Rendered HTML and CSS | `tools/validate_site.py` (Nu HTML Checker) | 22 pages and `style.css`: 0 errors, 0 warnings (after fixing 2 bugs) |
| Accessibility, keyboard, contrast, responsive, JS console | `tools/browser_checks.py` (Chromium + axe-core) | 145 of 145 checks pass (21 failed before the fixes) |
| Browser-level manual test cases | `tools/ui_walkthrough.py` | 28 of 28 scripted cases pass |
| CRUD, immediate feedback and persistence | `tools/deployment_check.py` | 19 of 19 checks pass on the production-like build |
| Production settings | `python manage.py check --deploy` | 1 warning (W021, HSTS preload), deliberate |
| Credentials in Git history | gitleaks 8.21.2 and a manual pattern search | No real credentials; 2 test-fixture passwords |
| Tests in public CI | GitHub Actions **Tests** workflow, [run 39498840738](https://github.com/Md12Ali/Joy2buy/actions/runs/39498840738) | flake8 clean; no missing migrations; 122 tests OK on PostgreSQL 16 (including the simultaneous-cancellation tests) and on SQLite |
| Live site | GitHub Actions **Live site checks** workflow, [run 39499040282](https://github.com/Md12Ali/Joy2buy/actions/runs/39499040282) | HTTPS and security headers 6/6; HTML/CSS 0 errors on 8 public pages + CSS; browser checks 49 pass, 2 skipped, 0 fail; signed-in checks not yet run |

**Where the checks were run (13 October 2026).** A production-like local build of the current code:

- **App and database:** gunicorn 23.0.0 with 3 workers, PostgreSQL 16.15, Django 5.2.18 on Python 3.13.
- **Settings:** `DEBUG=False`, WhiteNoise with the manifest storage after `collectstatic`, and `SECURE_SSL_REDIRECT=False` because there is no TLS locally.
- **Data:** the `seed_store` catalogue (6 categories, 18 products), plus one QA customer and one QA staff account created for testing.
- **Browser checks:** Chromium 141 via Playwright 1.56.0, with axe-core 4.10.2 and Nu HTML Checker (vnu.jar) 26.10.12.

The test environment's network blocked `validator.w3.org`, `cdn.jsdelivr.net` and the live Heroku site:
- **HTML and CSS validation:** the Nu checker ran locally. It is the same software, with the same JSON API, as validator.w3.org/nu.
- **Bootstrap 5.3.3:** browser requests for the jsDelivr files were answered from the identical npm package (`--npm-mirror`). jsDelivr's `/npm/` URLs serve that package's files unchanged.
- **Live site:** the environment above could not reach <https://joy2buy-shop-218caf987cba.herokuapp.com/>, so the live checks were run from GitHub Actions instead; see [section 8](#8-deployment-verification).

The fresh-clone setup in the README was also followed literally on Python 3.12.3 (the version in `runtime.txt`), using SQLite:
- `seed_store` added 6 categories and 18 products; a second run added nothing.
- `createsuperuser` worked.
- `/`, `/cart/`, `/account/login/`, a product page and `/admin/login/` all returned 200.
- The test suite passed (`OK (skipped=3)`).

---

## 2. Automated tests

### Commands and output

```text
$ python manage.py test
Found 122 test(s).
...
Ran 122 tests in 16.652s

OK (skipped=3)
```

The 3 skipped tests fire genuinely simultaneous requests from 8 threads. SQLite has no row-level locks, so they only run against PostgreSQL:

```text
$ DATABASE_URL=postgres://postgres@127.0.0.1:5433/joy2buy python manage.py test -v 2
...
Ran 122 tests in 21.294s

OK
```

The same two runs happen in GitHub Actions on every push (`.github/workflows/tests.yml`, PostgreSQL 16 service); the first run is linked in section 1.

To run them yourself, point `DATABASE_URL` at any PostgreSQL database the user may create a test database on. Useful variations:

```bash
python manage.py test orders -v 2                                   # one app, every test name
python manage.py test orders.tests.RepeatedCancellationTests        # one class
```

### Coverage by app

| File | Tests | What is covered |
| --- | --- | --- |
| `products/tests.py` | 45 | Model creation, slugs, relationships, validators, rating signals; list, search, filter, detail and 404 pages; review create, update, delete and permissions; staff product and category CRUD |
| `cart/tests.py` | 20 | Add, update, remove; stock caps; invalid quantities; totals and delivery charge; JSON responses; open-redirect protection |
| `orders/tests.py` | 38 | Order and line models, totals; checkout form validation; placing an order, stock reduction and rollback; owner / staff access; cancellation; status updates; repeated, stale and simultaneous cancellation; valid HTML date format |
| `profiles/tests.py` | 19 | Profile signal; sign up, login, logout; password hashing and change; dashboard; profile update; wishlist |
| **Total** | **122** | |

Every test, by class (from the PostgreSQL `-v 2` run, all "ok"):

<details>
<summary>Show all 122 tests</summary>

| App | Test class | Tests | What each test checks |
| --- | --- | --- | --- |
| `cart` | `CartJsonTests` | 4 | add returns summary; invalid quantity returns 400 with message; remove returns empty cart; update returns line total |
| `cart` | `CartViewTests` | 16 | add requires post; add to cart stores quantity in session; adding twice increases quantity; cannot add out of stock product; cart count appears in navbar; cart drops products that become unavailable; cart page shows totals and delivery charge; delivery is free over threshold; empty cart page; external next address is ignored; invalid quantities are rejected; quantity is capped at stock; remove from cart; unknown product returns 404; update quantity; update rejects item not in cart |
| `orders` | `CheckoutFormTests` | 3 | bad phone postcode and email are rejected; required fields; valid details are normalised |
| `orders` | `CheckoutViewTests` | 7 | cart is trimmed when stock drops before checkout; checkout page loads with items; checkout requires login; empty cart redirects to shop; invalid details do not create an order; order is rolled back when stock runs out mid checkout; placing an order |
| `orders` | `OrderAccessTests` | 9 | anonymous user is redirected; customer can cancel and stock is returned; order date is a valid html datetime; other customer cannot cancel; other customer gets 403; owner can view order; shipped order cannot be cancelled; staff can view any order; unknown order returns 404 |
| `orders` | `OrderModelTests` | 4 | order line survives product deletion; relationships and helpers; totals add delivery below threshold; transaction id is generated and unique |
| `orders` | `RepeatedCancellationTests` | 7 | customer and staff cancelling restocks once; customer cancelling twice restocks once; staff cancelling twice restocks once; stale customer cancel after dispatch is refused; stale customer request does not restock again; stale staff request cannot reopen cancelled order; stale staff request does not restock again |
| `orders` | `StaffOrderTests` | 5 | customer cannot update status; invalid status is rejected; order list is staff only; staff can update status; staff cancellation restocks once and cannot be reopened |
| `products` | `FormTests` | 4 | product form accepts valid data; product form rejects bad price and short text; review form rejects out of range rating; review form requires rating and real text |
| `products` | `ModelTests` | 11 | active queryset hides drafts; category product relationship; category with products cannot be deleted; one review per user per product; price must be positive; rating follows reviews; review rating range is validated; slugs are generated and unique; spec list parses lines; stock helpers; string representations |
| `products` | `ReviewViewTests` | 8 | anonymous user is redirected to login; author can delete own review; create review; get is not allowed; invalid review is rejected with feedback; other customer cannot delete review; second submission updates the existing review; staff can delete any review |
| `products` | `StaffProductViewTests` | 10 | category in use is not deleted; delete asks for confirmation then deletes; duplicate category name is rejected; invalid product is not created; staff can create and update category; staff can create product; staff can open management pages; staff can update product; staff pages forbid ordinary customers; staff pages redirect anonymous users to login |
| `products` | `StorefrontViewTests` | 12 | category filter; draft product is hidden from shoppers; draft product is visible to staff; in stock filter and invalid sort and page; product detail page; product list shows active products only; search filters results; search suggestions ignore one letter; search suggestions return json; search with no match shows empty state; unknown category redirects to full list; unknown page uses custom 404 template |
| `profiles` | `AccountViewTests` | 10 | dashboard shows account sections; invalid profile update changes nothing; login page loads; login with correct and incorrect password; logout requires post and signs out; password change; private pages redirect anonymous users; profile form allows blank optional fields; update profile; wishlist toggle adds then removes |
| `profiles` | `ProfileModelTests` | 4 | default address; get profile recreates a missing profile; password is stored hashed; profile is created with user |
| `profiles` | `SignUpTests` | 5 | duplicate email is rejected; mismatched passwords are rejected; signup creates user profile and logs in; signup page loads; weak password is rejected |
| `orders` | `SimultaneousCancellationTests` | 3 | cancel racing dispatch leaves a consistent result; simultaneous customer and staff cancellations restock once; simultaneous customer cancellations restock once |

</details>

### Tests added for the cancellation race (bug 7)

These tests were written first, run against the unfixed code to reproduce the bug, then run again after the fix.

Before the fix, SQLite:

```text
FAIL: test_stale_customer_cancel_after_dispatch_is_refused
FAIL: test_stale_customer_request_does_not_restock_again
FAIL: test_stale_staff_request_cannot_reopen_cancelled_order
FAIL: test_stale_staff_request_does_not_restock_again
Ran 37 tests in 5.270s
FAILED (failures=4, skipped=3)
```

Before the fix, PostgreSQL. The order had 4 items and stock started at 6, so a single restock should give 10:

```text
FAIL: test_cancel_racing_dispatch_leaves_a_consistent_result
AssertionError: 14 != 10
FAIL: test_simultaneous_customer_and_staff_cancellations_restock_once
AssertionError: 38 != 10
FAIL: test_simultaneous_customer_cancellations_restock_once
AssertionError: 38 != 10
Ran 3 tests in 2.846s
FAILED (failures=3)
```

Eight simultaneous cancellations returned the same 4 items to stock eight times (6 + 8 x 4 = 38).

After the fix, all pass. The three threaded tests were then repeated 10 times in a row to rule out a lucky pass: `10 OK`.

---

## 3. Code validation

### Python (flake8)

```text
$ python -m flake8
$ echo $?
0
```

Settings are in `setup.cfg` (79-character lines; migrations excluded).

The assessment found 14 findings in `validate-and-screenshot.py`. That script had a further problem: it saved screenshots of the validator websites and then printed "ALL VALIDATIONS COMPLETED SUCCESSFULLY!" without reading what the validators said. It has been replaced by `tools/validate_site.py`, which:
- sends each page to the checker's JSON API and reads every message
- prints each error and warning with its line number
- exits with status 1 if any page has an error or cannot be fetched

The new script and the other tools in `tools/` have no flake8 findings.

The images previously in `assets/images/validation/` were not validator output (for example, one claimed "XHTML 1.0 Strict" for an HTML5 page, another listed JavaScript files that do not exist). They have been removed and replaced by the real results below.

### HTML and CSS (Nu HTML Checker)

```bash
export JOY2BUY_CUSTOMER_USER=... JOY2BUY_CUSTOMER_PASSWORD=...
export JOY2BUY_STAFF_USER=...    JOY2BUY_STAFF_PASSWORD=...
python tools/validate_site.py --base-url http://127.0.0.1:8000/ --nu-url http://127.0.0.1:8888/
# exit status 0
```

The rendered HTML of each page is validated as the browser receives it, signed in where needed. The stylesheet is checked by the same service.

The **first run** failed 20 of 23 checks. Every page had the same error: `aria-labelledby` on a `<div>` with no role, from the confirmation modal in `base.html` (bug 8). After that fix, the order pages (now reachable because the QA customer had an order) showed a second error: microseconds in a `<time datetime>` value (bug 9). **Final run:**

| Role | Page | Result | Errors | Warnings |
| --- | --- | --- | --- | --- |
| public | Product list (home) | PASS | 0 | 0 |
| public | Search results | PASS | 0 | 0 |
| public | Empty search | PASS | 0 | 0 |
| public | Product detail | PASS | 0 | 0 |
| public | Cart | PASS | 0 | 0 |
| public | Sign in | PASS | 0 | 0 |
| public | Register | PASS | 0 | 0 |
| public | 404 page | PASS | 0 | 0 |
| customer | Account dashboard | PASS | 0 | 0 |
| customer | Edit profile | PASS | 0 | 0 |
| customer | Change password | PASS | 0 | 0 |
| customer | Cart with an item | PASS | 0 | 0 |
| customer | Checkout | PASS | 0 | 0 |
| customer | Order detail | PASS | 0 | 0 |
| staff | Store management | PASS | 0 | 0 |
| staff | Add product | PASS | 0 | 0 |
| staff | Edit product | PASS | 0 | 0 |
| staff | Delete product (confirm) | PASS | 0 | 0 |
| staff | Add category | PASS | 0 | 0 |
| staff | Edit category | PASS | 0 | 0 |
| staff | Order management | PASS | 0 | 0 |
| staff | Order detail (staff) | PASS | 0 | 0 |
| css | /static/css/style.350b78310190.css | PASS | 0 | 0 |

```text
23 of 23 checks passed or were skipped; 0 failed.
```

None were skipped. `style.css` also passes as CSS level 3 with no warnings.

### JavaScript

`node --check static/js/main.js` reports no syntax errors. `tools/browser_checks.py` listens for console errors and uncaught exceptions on every page it opens, at every width and in every role, and recorded **none**.

---

## 4. Accessibility, keyboard, contrast and responsive checks

```bash
npm pack axe-core@4.10.2 && tar xzf axe-core-4.10.2.tgz
pip install playwright==1.56.0 && playwright install chromium
python tools/browser_checks.py --axe package/axe.min.js --screenshots assets/images/screenshots
```

### What is checked

The script covers 12 pages: 4 public, 4 customer and 4 staff. Each opens at 390px, 768px and 1440px.

| Check | How | Widths |
| --- | --- | --- |
| Responsive | Fails if the page scrolls sideways, naming the elements that stick out | 390, 768, 1440 |
| Colour contrast | axe-core `color-contrast` rule (WCAG 2.1 AA: 4.5:1 for normal text, 3:1 for large text) | 390, 1440 |
| Other WCAG 2.1 A/AA rules | Every other axe-core rule tagged `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa` (labels, names, landmarks, ARIA, lists, alt text...) | 390, 1440 |
| Keyboard reach | Presses Tab from the top of the page until focus wraps round; every visible control must be reached | 1440 |
| Focus visible | Each focused control must show an outline or focus ring | 1440 |
| Skip link | Must be the first Tab stop and, when pressed, move focus into `<main>` | 1440 |
| Mobile menu | The menu button must open with the Enter key | 390 |
| JavaScript | No console errors or uncaught exceptions | all |

### Results before and after the fixes

The script was first run against the original CSS, then against the fixed CSS.

| Check | Before | After | Cause (see section 9) |
| --- | --- | --- | --- |
| Colour contrast | 8 failures: `#6c757d` text at 4.42:1 and `#dc3545` at 4.27:1 on the page background | 0 | Bug 10 |
| Focus visible | 12 failures: amber buttons (Search, Add to cart, Place order, Sign in, Go to checkout) showed no focus at all | 0 | Bug 11 |
| Focus outline contrast | Not measured by axe; calculated as 2.46:1 against the page background (3:1 needed) | Navy 15.06:1; amber in the navy header, hero and footer 7.9:1 | Bug 12 |
| Responsive | 1 failure: staff product page 443px wide in a 390px window | 0 | Bug 13 |
| **Total** | **124 of 145 passed, 21 failed** | **145 of 145 passed** | |

Final summary (axe passed between 19 and 30 rules per page, depending on what the page contains):

| Area | Check | Page x width runs | Result |
| --- | --- | --- | --- |
| Responsive | No sideways scrolling | 36 | PASS |
| Contrast | WCAG AA colour contrast (axe) | 24 | PASS |
| Accessibility | Other WCAG 2.1 A/AA rules (axe) | 24 | PASS |
| Keyboard | Every visible control reachable by Tab | 12 | PASS |
| Keyboard | Focus indicator visible on each control | 12 | PASS |
| Keyboard | Skip link is the first stop | 12 | PASS |
| Keyboard | Skip link moves focus into `<main>` | 12 | PASS |
| Keyboard | Mobile menu opens with Enter | 12 | PASS |
| JavaScript | No console errors on any page | 1 (all pages) | PASS |

<details>
<summary>Show all 145 results</summary>

| Page @ width | Check | Result | Detail |
| --- | --- | --- | --- |
| homepage @390 | responsive: no sideways scrolling | PASS |  |
| homepage @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| homepage @390 | axe: other WCAG 2.1 A/AA rules (28 rules passed) | PASS |  |
| homepage @390 | keyboard: mobile menu opens with Enter | PASS |  |
| homepage @768 | responsive: no sideways scrolling | PASS |  |
| homepage @1440 | responsive: no sideways scrolling | PASS |  |
| homepage @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| homepage @1440 | axe: other WCAG 2.1 A/AA rules (27 rules passed) | PASS |  |
| homepage @1440 | keyboard: every visible control reachable by Tab | PASS | 56 reached |
| homepage @1440 | keyboard: focus indicator visible on each control | PASS |  |
| homepage @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| homepage @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| product-detail @390 | responsive: no sideways scrolling | PASS |  |
| product-detail @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| product-detail @390 | axe: other WCAG 2.1 A/AA rules (28 rules passed) | PASS |  |
| product-detail @390 | keyboard: mobile menu opens with Enter | PASS |  |
| product-detail @768 | responsive: no sideways scrolling | PASS |  |
| product-detail @1440 | responsive: no sideways scrolling | PASS |  |
| product-detail @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| product-detail @1440 | axe: other WCAG 2.1 A/AA rules (28 rules passed) | PASS |  |
| product-detail @1440 | keyboard: every visible control reachable by Tab | PASS | 30 reached |
| product-detail @1440 | keyboard: focus indicator visible on each control | PASS |  |
| product-detail @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| product-detail @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| shopping-cart @390 | responsive: no sideways scrolling | PASS |  |
| shopping-cart @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| shopping-cart @390 | axe: other WCAG 2.1 A/AA rules (19 rules passed) | PASS |  |
| shopping-cart @390 | keyboard: mobile menu opens with Enter | PASS |  |
| shopping-cart @768 | responsive: no sideways scrolling | PASS |  |
| shopping-cart @1440 | responsive: no sideways scrolling | PASS |  |
| shopping-cart @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| shopping-cart @1440 | axe: other WCAG 2.1 A/AA rules (25 rules passed) | PASS |  |
| shopping-cart @1440 | keyboard: every visible control reachable by Tab | PASS | 21 reached |
| shopping-cart @1440 | keyboard: focus indicator visible on each control | PASS |  |
| shopping-cart @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| shopping-cart @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| sign-in @390 | responsive: no sideways scrolling | PASS |  |
| sign-in @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| sign-in @390 | axe: other WCAG 2.1 A/AA rules (23 rules passed) | PASS |  |
| sign-in @390 | keyboard: mobile menu opens with Enter | PASS |  |
| sign-in @768 | responsive: no sideways scrolling | PASS |  |
| sign-in @1440 | responsive: no sideways scrolling | PASS |  |
| sign-in @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| sign-in @1440 | axe: other WCAG 2.1 A/AA rules (26 rules passed) | PASS |  |
| sign-in @1440 | keyboard: every visible control reachable by Tab | PASS | 24 reached |
| sign-in @1440 | keyboard: focus indicator visible on each control | PASS |  |
| sign-in @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| sign-in @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| account @390 | responsive: no sideways scrolling | PASS |  |
| account @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| account @390 | axe: other WCAG 2.1 A/AA rules (28 rules passed) | PASS |  |
| account @390 | keyboard: mobile menu opens with Enter | PASS |  |
| account @768 | responsive: no sideways scrolling | PASS |  |
| account @1440 | responsive: no sideways scrolling | PASS |  |
| account @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| account @1440 | axe: other WCAG 2.1 A/AA rules (30 rules passed) | PASS |  |
| account @1440 | keyboard: every visible control reachable by Tab | PASS | 24 reached |
| account @1440 | keyboard: focus indicator visible on each control | PASS |  |
| account @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| account @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| shopping-cart-full @390 | responsive: no sideways scrolling | PASS |  |
| shopping-cart-full @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| shopping-cart-full @390 | axe: other WCAG 2.1 A/AA rules (24 rules passed) | PASS |  |
| shopping-cart-full @390 | keyboard: mobile menu opens with Enter | PASS |  |
| shopping-cart-full @768 | responsive: no sideways scrolling | PASS |  |
| shopping-cart-full @1440 | responsive: no sideways scrolling | PASS |  |
| shopping-cart-full @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| shopping-cart-full @1440 | axe: other WCAG 2.1 A/AA rules (27 rules passed) | PASS |  |
| shopping-cart-full @1440 | keyboard: every visible control reachable by Tab | PASS | 24 reached |
| shopping-cart-full @1440 | keyboard: focus indicator visible on each control | PASS |  |
| shopping-cart-full @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| shopping-cart-full @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| checkout @390 | responsive: no sideways scrolling | PASS |  |
| checkout @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| checkout @390 | axe: other WCAG 2.1 A/AA rules (28 rules passed) | PASS |  |
| checkout @390 | keyboard: mobile menu opens with Enter | PASS |  |
| checkout @768 | responsive: no sideways scrolling | PASS |  |
| checkout @1440 | responsive: no sideways scrolling | PASS |  |
| checkout @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| checkout @1440 | axe: other WCAG 2.1 A/AA rules (28 rules passed) | PASS |  |
| checkout @1440 | keyboard: every visible control reachable by Tab | PASS | 30 reached |
| checkout @1440 | keyboard: focus indicator visible on each control | PASS |  |
| checkout @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| checkout @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| order-detail @390 | responsive: no sideways scrolling | PASS |  |
| order-detail @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| order-detail @390 | axe: other WCAG 2.1 A/AA rules (21 rules passed) | PASS |  |
| order-detail @390 | keyboard: mobile menu opens with Enter | PASS |  |
| order-detail @768 | responsive: no sideways scrolling | PASS |  |
| order-detail @1440 | responsive: no sideways scrolling | PASS |  |
| order-detail @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| order-detail @1440 | axe: other WCAG 2.1 A/AA rules (27 rules passed) | PASS |  |
| order-detail @1440 | keyboard: every visible control reachable by Tab | PASS | 22 reached |
| order-detail @1440 | keyboard: focus indicator visible on each control | PASS |  |
| order-detail @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| order-detail @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| staff-store-management @390 | responsive: no sideways scrolling | PASS |  |
| staff-store-management @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| staff-store-management @390 | axe: other WCAG 2.1 A/AA rules (29 rules passed) | PASS |  |
| staff-store-management @390 | keyboard: mobile menu opens with Enter | PASS |  |
| staff-store-management @768 | responsive: no sideways scrolling | PASS |  |
| staff-store-management @1440 | responsive: no sideways scrolling | PASS |  |
| staff-store-management @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| staff-store-management @1440 | axe: other WCAG 2.1 A/AA rules (28 rules passed) | PASS |  |
| staff-store-management @1440 | keyboard: every visible control reachable by Tab | PASS | 85 reached |
| staff-store-management @1440 | keyboard: focus indicator visible on each control | PASS |  |
| staff-store-management @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| staff-store-management @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| staff-edit-product @390 | responsive: no sideways scrolling | PASS |  |
| staff-edit-product @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| staff-edit-product @390 | axe: other WCAG 2.1 A/AA rules (23 rules passed) | PASS |  |
| staff-edit-product @390 | keyboard: mobile menu opens with Enter | PASS |  |
| staff-edit-product @768 | responsive: no sideways scrolling | PASS |  |
| staff-edit-product @1440 | responsive: no sideways scrolling | PASS |  |
| staff-edit-product @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| staff-edit-product @1440 | axe: other WCAG 2.1 A/AA rules (26 rules passed) | PASS |  |
| staff-edit-product @1440 | keyboard: every visible control reachable by Tab | PASS | 29 reached |
| staff-edit-product @1440 | keyboard: focus indicator visible on each control | PASS |  |
| staff-edit-product @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| staff-edit-product @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| staff-order-management @390 | responsive: no sideways scrolling | PASS |  |
| staff-order-management @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| staff-order-management @390 | axe: other WCAG 2.1 A/AA rules (24 rules passed) | PASS |  |
| staff-order-management @390 | keyboard: mobile menu opens with Enter | PASS |  |
| staff-order-management @768 | responsive: no sideways scrolling | PASS |  |
| staff-order-management @1440 | responsive: no sideways scrolling | PASS |  |
| staff-order-management @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| staff-order-management @1440 | axe: other WCAG 2.1 A/AA rules (28 rules passed) | PASS |  |
| staff-order-management @1440 | keyboard: every visible control reachable by Tab | PASS | 23 reached |
| staff-order-management @1440 | keyboard: focus indicator visible on each control | PASS |  |
| staff-order-management @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| staff-order-management @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| staff-order-detail @390 | responsive: no sideways scrolling | PASS |  |
| staff-order-detail @390 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| staff-order-detail @390 | axe: other WCAG 2.1 A/AA rules (23 rules passed) | PASS |  |
| staff-order-detail @390 | keyboard: mobile menu opens with Enter | PASS |  |
| staff-order-detail @768 | responsive: no sideways scrolling | PASS |  |
| staff-order-detail @1440 | responsive: no sideways scrolling | PASS |  |
| staff-order-detail @1440 | contrast: WCAG AA colour-contrast (axe) | PASS |  |
| staff-order-detail @1440 | axe: other WCAG 2.1 A/AA rules (28 rules passed) | PASS |  |
| staff-order-detail @1440 | keyboard: every visible control reachable by Tab | PASS | 23 reached |
| staff-order-detail @1440 | keyboard: focus indicator visible on each control | PASS |  |
| staff-order-detail @1440 | keyboard: skip link is the first stop | PASS | Skip to main content |
| staff-order-detail @1440 | keyboard: skip link moves focus into `<main>` | PASS |  |
| all pages | javascript: no console errors | PASS |  |

</details>

### Screenshots

Full-page screenshots from the same run are in `assets/images/screenshots/{mobile,tablet,desktop}/`, named `<device>-<page>.png`:

- **Public:** `homepage`, `product-detail`, `shopping-cart` (empty), `sign-in`
- **Customer:** `account`, `shopping-cart-full`, `checkout`, `order-detail`
- **Staff:** `staff-store-management`, `staff-edit-product`, `staff-order-management`, `staff-order-detail`

### Limits of these checks

Automated tools find roughly a third to a half of accessibility problems. These checks did **not** include:
- a screen reader (NVDA, VoiceOver)
- 200% browser zoom
- Windows high-contrast mode
- manual judgement of reading order and link text

Those are listed for the manual run in section 5.

---

## 5. Manual test plan and results

### About the earlier "37/37 manual tests" claim

The README previously said "Manual Testing: 37/37 Tests Passing", but no individual results ever existed. The first version of the project (commit `220439c`) contains this same 38-case plan with every result marked "Not yet run". **That claim is withdrawn.** It has been replaced by the evidence below, which states for each case how it has actually been checked so far.

### How each case has been checked

- **Scripted:** the written steps were carried out in a real browser (headless Chromium) by `tools/ui_walkthrough.py` on the production-like local build, 13 October 2026. The "What happened" text is copied from that run's output.
- **Automated:** covered by the named unit test(s) or tool, all passing.
- **By hand on the live site:** results go in the right-hand column. This must be done by the developer and has **not** been recorded yet.

Test accounts: a QA customer account with no special rights and a QA staff account (`is_staff`). Data: the `seed_store` catalogue.

| # | Area | Steps | Expected result | Scripted / automated evidence (13 Oct 2026, local) | By hand on live site (date, Pass/Fail, notes) |
| --- | --- | --- | --- | --- | --- |
| 1 | Navigation | On the home page, open every link in the navbar and footer | Each opens the right page with no 404; external links open in a new tab | **Pass** (scripted): 10 site links all returned 200; 2 external links have `target="_blank"` and `rel="noopener"` | Not yet recorded |
| 2 | Navigation | Narrow the window below 992px; press the menu button with mouse and with Enter | Menu collapses behind a toggle and opens when pressed | **Pass** (automated): `browser_checks.py` "mobile menu opens with Enter" on 12 pages at 390px | Not yet recorded |
| 3 | Catalogue | Open the home page | Hero, category tabs and a grid of active products | **Pass** (scripted): hero shown; 7 tabs; 12 product cards | Not yet recorded |
| 4 | Catalogue | Click the "Audio" category tab | Only Audio products listed; the tab is highlighted | **Pass** (scripted): 3 products, all labelled "Audio"; active tab "Audio" | Not yet recorded |
| 5 | Search | Click the search box, type "b", pause, then type "ottle" slowly; click the first suggestion | No list after 1 letter; suggestions after 2+; the chosen product opens | **Pass** (scripted): no list after 1 letter; suggestion "Insulated Steel Water Bottle 750 ml" opened that product | Not yet recorded |
| 6 | Search | Search for `zzzz` | "No products match your search" with a link back | **Pass** (scripted) | Not yet recorded |
| 7 | Catalogue | Choose "Price: low to high", tick "In stock only" | List re-orders by price; out-of-stock items disappear; both filters stay in the URL | **Pass** (scripted): URL `?available=1&sort=price_low`; prices 8.99, 11.99, 12.50, 14.99...; 0 out-of-stock cards | Not yet recorded |
| 8 | Product | Open a product **with a photo**, hover over the photo | The image zooms and follows the pointer | **Not run**: the seed data has no product photos. Upload one as staff first | Not yet recorded |
| 9 | Product | Open "Tempo Portable Bluetooth Speaker" (stock 0) | "Out of stock" shown; no add-to-cart form | **Pass** (scripted) | Not yet recorded |
| 10 | Cart | On the home page press "Add to cart" on the first card | Success message; badge increases; no page reload | **Pass** (scripted): badge 0 -> 1; page not reloaded; "Universal Travel Adapter was added to your cart." | Not yet recorded |
| 11 | Cart | On a product with low stock, ask for more than is in stock | Quantity reduced to the stock available, with a warning | **Pass** (automated): `cart.tests...test_quantity_is_capped_at_stock` | Not yet recorded |
| 12 | Cart | Type `0`, `-1` and `abc` as a quantity and submit | Rejected with a clear error; cart unchanged | **Pass** (automated): `test_invalid_quantities_are_rejected`, `test_invalid_quantity_returns_400_with_message` | Not yet recorded |
| 13 | Cart | In the cart, change a quantity from 1 to 2 | Line total, subtotal, delivery and total update immediately | **Pass** (scripted): line £22.50 -> £45.00; subtotal £22.50 -> £45.00; no reload | Not yet recorded |
| 14 | Cart | Press Remove on a line, then confirm | A confirmation dialog appears; confirming removes the line | **Pass** (scripted): dialog asked "Remove Universal Travel Adapter from your cart?"; lines 1 -> 0 | Not yet recorded |
| 15 | Cart | Raise the quantity until the subtotal is £50 or more | Delivery shows "Free" | **Pass** (scripted): subtotal £67.50, delivery "Free" | Not yet recorded |
| 16 | Cart | Switch JavaScript off; repeat add, change quantity, remove | Everything works through normal page loads, with messages | **Pass** (scripted, JS disabled): "...was added to your cart." / "...quantity updated to 3." / "...was removed from your cart."; 0 lines left | Not yet recorded |
| 17 | Auth | Register with two different passwords | Field error; no account created | **Pass** (scripted): "The two password fields didn't match."; stayed on the form | Not yet recorded |
| 18 | Auth | Register with valid details | Account created, signed in, welcome message, dashboard | **Pass** (automated): `profiles.tests...test_signup_creates_user_profile_and_logs_in` | Not yet recorded |
| 19 | Auth | Sign in with a wrong password | Error; not signed in | **Pass** (scripted): "Please enter a correct username and password..." | Not yet recorded |
| 20 | Auth | Signed out, add an item, open `/orders/checkout/`, sign in | Sent to sign in, then back to checkout; cart kept | **Pass** (scripted): returned to `/orders/checkout/` with 1 item | Not yet recorded |
| 21 | Checkout | Fill the form but leave Phone empty and enter `!!` as postcode | Errors next to those fields; no order | **Pass** (scripted): 2 field errors; still on checkout | Not yet recorded |
| 22 | Checkout | Place a valid order for one "Pulse True Wireless Earbuds" | Confirmation with reference; cart empty; stock reduced by 1 | **Pass** (scripted): order `76DC2AD0567949A2` confirmed; badge 0; stock 60 -> 59 | Not yet recorded |
| 23 | Orders | Open the account dashboard | The new order is listed as "Pending" | **Pass** (scripted) | Not yet recorded |
| 24 | Orders | Open the order and press "Cancel this order", confirm | Status "Cancelled"; stock restored | **Pass** (scripted): stock 59 -> 60. Also `RepeatedCancellationTests` and `SimultaneousCancellationTests` | Not yet recorded |
| 25 | Orders | Signed in as a different customer, open the first customer's order URL | 403 page | **Pass** (automated): `test_other_customer_gets_403`, `test_other_customer_cannot_cancel` | Not yet recorded |
| 26 | Reviews | Submit a review with text but no rating | "Please choose a star rating."; nothing saved | **Pass** (scripted) | Not yet recorded |
| 27 | Reviews | Submit a 5-star review, then change it to 3 stars with new text | Review appears; editing replaces it (one review per customer) | **Pass** (scripted): "Thank you - your review is live." then "Your review has been updated."; old text gone | Not yet recorded |
| 28 | Reviews | Delete your review and confirm | Confirmation dialog, then the review disappears | **Pass** (scripted) | Not yet recorded |
| 29 | Profile | Change "Town or city" to York and save; add an item; open checkout | Success message; checkout pre-filled with York | **Pass** (scripted): "Your details have been updated."; checkout city "York"; then restored | Not yet recorded |
| 30 | Wishlist | On a product press "Save to wishlist", check the dashboard, then remove | Button text toggles; dashboard wishlist updates | **Pass** (scripted): "Save to wishlist" -> "Remove from wishlist" -> back; listed on dashboard while saved | Not yet recorded |
| 31 | Staff | As a customer, visit `/manage/` | 403 page | **Pass** (scripted): HTTP 403 "You do not have access to this page" | Not yet recorded |
| 32 | Staff | As staff, choose a 3 MB image on "Add product" | Refused with a 2 MB message | **Pass** (scripted): 3.5 MB file refused in the browser ("That image is larger than 2 MB..."); with JavaScript off the server refused it ("Image files must be 2 MB or smaller."); nothing saved | Not yet recorded |
| 33 | Staff | Add, edit and delete a product | A message confirms each step; delete asks first | **Pass** (automated): `deployment_check.py` create/update/delete with messages and persistence; `products.tests` staff CRUD tests | Not yet recorded |
| 34 | Staff | Set a product to "Draft" | It disappears from the shop but stays in the management table | **Pass** (automated): `deployment_check.py` "draft is hidden from signed-out visitors (404)" | Not yet recorded |
| 35 | Staff | Open an order as staff, set status to "Shipped", save | Message; the customer can no longer cancel | **Pass** (scripted): "Order ... is now shipped."; customer sees no cancel button | Not yet recorded |
| 36 | Errors | Visit `/no-such-page/` | Custom 404 page with links back | **Pass** (scripted): HTTP 404 with "Back to the shop" and "View your cart" | Not yet recorded |
| 37 | Responsive | View every page at 360-390px, 768px and 1280-1440px | No sideways scrolling; 1, 2 and 4 product columns | **Pass** (automated): `browser_checks.py`, 36 page/width runs (after bug 13 fix) | Not yet recorded |
| 38 | Accessibility | Tab through the home page with the keyboard only | Skip link first; focus always visible; all controls reachable | **Pass** (automated): `browser_checks.py` on 12 pages (after bugs 11 and 12 fixes) | Not yet recorded |
| 39 | Accessibility | Use a screen reader (NVDA or VoiceOver) to add to cart and check out | Cart count and messages are announced; all controls have names | **Not run** | Not yet recorded |
| 40 | Accessibility | Zoom the browser to 200% on the home page, cart and checkout | All content usable with no loss of information | **Not run** | Not yet recorded |

Scripted run output (`python tools/ui_walkthrough.py`, exit status 0):

<details>
<summary>Show the walkthrough results</summary>

| # | Case | Result | What happened |
| --- | --- | --- | --- |
| 1 | Every navbar and footer link opens without error | PASS | 10 site links all 200; 2 external links open in a new tab |
| 3 | Home page shows hero, category tabs and products | PASS | hero shown; 7 tabs; 12 product cards |
| 4 | Choosing a category tab filters the products | PASS | tab 'Audio': 3 products, categories shown ['audio'], active tab 'Audio' |
| 5 | Typing in search shows suggestions; choosing one opens the product | PASS | no list after 1 letter: True; 1 suggestions; chose 'Insulated Steel Water Bottle 750 ml', opened 'Insulated Steel Water Bottle 750 ml' |
| 6 | Searching for 'zzzz' explains there are no matches | PASS | 'No products match your search' shown with a link back |
| 7 | Sort by price and 'in stock only' re-order and filter the list | PASS | URL ?available=1&sort=price_low; prices [8.99, 11.99, 12.5, 14.99]...; out-of-stock cards: 0 |
| 9 | An out-of-stock product cannot be added | PASS | 'Out of stock' shown: True; product add-to-cart forms: 0 |
| 10 | Adding from the grid updates the badge without a reload | PASS | badge 0 -> 1; page not reloaded: True; message 'Universal Travel Adapter was added to your cart.' |
| 13 | Changing a quantity updates line total and totals immediately | PASS | line £22.50 -> £45.00; subtotal £22.50 -> £45.00; no reload: True |
| 15 | A subtotal of £50 or more makes delivery free | PASS | subtotal £67.50, delivery shows 'Free' |
| 14 | Remove asks for confirmation, then removes the line | PASS | modal asked 'Remove Universal Travel Adapter from your cart?'; lines 1 -> 0 |
| 16 | Cart add, update and remove work with JavaScript switched off | PASS | 'Pulse True Wireless Earbuds was added to your cart.' / 'Pulse True Wireless Earbuds quantity updated to 3.' / 'Pulse True Wireless Earbuds was removed from your cart.'; lines left 0 |
| 17 | Registering with mismatched passwords is refused | PASS | errors: The two password fields didn’t match. |
| 19 | Signing in with a wrong password is refused | PASS | stayed on sign-in page with 'Please enter a correct username and password. Note that both fields may be case-' |
| 20 | Checkout while signed out goes to sign in, then back to checkout with the cart kept | PASS | sent to sign in: True; then at /orders/checkout/ with 1 item(s) in cart |
| 21 | Checkout with a blank phone and bad postcode creates no order | PASS | still on checkout; 2 field errors shown |
| 22 | A valid order shows a reference, empties the cart and reduces stock | PASS | order 76DC2AD0567949A2: 'Order 76DC2AD0567949A2 placed. A summary is shown '; cart badge 0; stock 60 -> 59 |
| 23 | The new order is listed on the dashboard as Pending | PASS | row: ['76DC2AD0567949A2', '13', 'Oct', '2026', '1', '£44.98'] |
| 35 | Staff mark the order Shipped; the customer can no longer cancel | PASS | staff saw 'Order 76DC2AD0567949A2 is now shipped.'; customer cancel buttons: 0 |
| 24 | Cancelling a pending/processing order restores stock | PASS | status Cancelled: True; stock 59 -> 60 |
| 26 | A review without a rating is refused | PASS | 'Please choose a star rating.' shown |
| 27 | A valid review appears and editing replaces it | PASS | 'Thank you - your review is live.' then 'Your review has been updated.'; edited text shown: 2, old text left: 0 |
| 28 | Deleting your own review asks first, then removes it | PASS | modal shown; review left on page: 0 |
| 29 | Updating the profile is confirmed and pre-fills checkout | PASS | 'Your details have been updated.'; checkout city pre-filled with 'York'; restored to 'Leeds' |
| 30 | Saving to and removing from the wishlist toggles the button and the dashboard | PASS | 'Save to wishlist' -> 'Remove from wishlist' -> 'Save to wishlist'; on dashboard while saved: True |
| 31 | A customer visiting /manage/ gets the 403 page | PASS | HTTP 403, 'You do not have access to this page' |
| 32 | A 3 MB image is rejected in the browser and, with JavaScript off, by the server | PASS | 3.5 MB file. Browser: 'That image is larger than 2 MB. Please choose a smaller file.', file cleared: True. Server (JS off): ['Image files must be 2 MB or smaller.']; product saved: False |
| 36 | An unknown address shows the custom 404 page | PASS | HTTP 404, links ['Back to the shop', 'View your cart'] |

```text
28 of 28 cases passed; 0 failed.
```

</details>

---

## 6. Production settings

`check --deploy` was run with the production configuration: `DEBUG=False`, `SECURE_SSL_REDIRECT` unset, and `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` set to the Heroku host.

```text
$ python manage.py check --deploy
System check identified some issues:

WARNINGS:
?: (security.W021) You have not set the SECURE_HSTS_PRELOAD setting to True. Without this, your site cannot be submitted to the browser preload list.

System check identified 1 issue (0 silenced).
```

W021 is deliberate: a `*.herokuapp.com` subdomain cannot be added to the HSTS preload list.

The effective values in that configuration:

```text
DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 2592000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
X_FRAME_OPTIONS = DENY
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = same-origin
SESSION_COOKIE_HTTPONLY = True
```

Also confirmed: without `SECRET_KEY`, the app refuses to start when `DEBUG` is off (`ImproperlyConfigured: The SECRET_KEY environment variable must be set when DEBUG is False.`).

On the live site, `tools/deployment_check.py --base-url https://...` checks the same settings from outside: HTTP redirects to HTTPS, HSTS and security headers, Secure CSRF cookie, and no Django debug page. Recording that run is part of section 8.

---

## 7. Credential review

Every commit on every branch on GitHub (`main` and the feedback branch, including the commits made for this report) was checked for committed secrets on 13 October 2026.

| Check | Method | Result |
| --- | --- | --- |
| Secret scanner | gitleaks 8.21.2: `gitleaks git --log-opts="--all" .` | 2 findings, both `"Tr1cky-Passphrase"` in `profiles/tests.py` lines 20-21: a password typed into the sign-up form in a test. It only exists in the throwaway test database. **Not a credential.** |
| Key patterns | Search of every added line in `git log --all -p` for Django `django-insecure-` keys, AWS `AKIA...` keys, Stripe `sk_` keys, GitHub tokens, `postgres://user:password@host` URLs with real hosts, `SECRET_KEY = "..."` literals, and `HEROKU_API_KEY` | None found. Matches were placeholders only (`<a long random string>`, `USER:PASSWORD`, empty `AWS_ACCESS_KEY_ID=`) |
| Sensitive files | Every commit's file tree checked for `.env`, `*.sqlite3`, `*.pem`, `*.key` | None ever committed; `.env` and `db.sqlite3` are in `.gitignore` |
| Settings | `joy2buy/settings.py` | Every secret is read from the environment; no fallback production key |

**Conclusion:** no real credentials appear anywhere in the repository history, so no history rewrite or key rotation is needed on that account.

What this review cannot cover (developer to confirm):
- Heroku config vars. Check with `heroku config --app <app>` that `SECRET_KEY` is long and random, and that it has never been pasted into an issue, chat or screenshot.
- Who has access to the Heroku app and the AWS account. If a key was ever shared, rotate it with `heroku config:set SECRET_KEY=...`, which signs out all users.

---

## 8. Deployment verification

### Production-like local build (done)

`tools/deployment_check.py` was run against the gunicorn + PostgreSQL + `DEBUG=False` build described in section 1. It uses controlled records named "QA test category/product" with a timestamp, created as a Draft and deleted at the end.

```bash
python tools/deployment_check.py --base-url http://127.0.0.1:8000/   # exit status 0
```

| Step | Check | Result | Detail |
| --- | --- | --- | --- |
| production settings | - | SKIPPED | site is not served over HTTPS |
| sign in | staff account signs in | PASS |  |
| create category | success message shown immediately | PASS |  |
| create category | saved (seen in a new session) | PASS |  |
| create product | success message shown immediately | PASS |  |
| create product | saved (seen in a new session) | PASS |  |
| create product | draft is hidden from signed-out visitors (404) | PASS | HTTP 404 |
| update product | success message shown immediately | PASS |  |
| update product | new price saved (new session) | PASS |  |
| delete product | success message shown immediately | PASS |  |
| delete product | gone (404 in a new session) | PASS | HTTP 404 |
| delete category | success message shown immediately | PASS |  |
| delete category | gone (new session) | PASS |  |
| sign in | customer account signs in | PASS |  |
| cart | add: confirmation message shown | PASS |  |
| cart | update: confirmation message shown | PASS |  |
| cart | update: quantity 2 kept on reload | PASS |  |
| cart | remove: confirmation message shown | PASS |  |
| cart | remove: line gone on reload | PASS |  |

```text
19 of 19 checks passed or were skipped; 0 failed.
```

Afterwards a database query confirmed no "QA test" product or category was left behind.

### Live site (GitHub Actions, 20 October 2026)

The checks were run against <https://joy2buy-shop-218caf987cba.herokuapp.com/> from GitHub's servers by the **Live site checks** workflow (`.github/workflows/live-checks.yml`), [run 39499040282](https://github.com/Md12Ali/Joy2buy/actions/runs/39499040282). The full output and screenshots of the live site are saved with the run as the `live-check-results` artifact. That run had no QA account logins, so the signed-in checks were skipped; they can be repeated with logins (see below).

**Production settings seen from outside** (`deployment_check.py`):

| Check | Result | Detail |
| --- | --- | --- |
| HTTP redirects to HTTPS | PASS | HTTP 301 -> `https://joy2buy-shop-218caf987cba.herokuapp.com/` |
| Strict-Transport-Security set | PASS | `max-age=2592000; includeSubDomains` |
| X-Frame-Options is DENY | PASS | |
| X-Content-Type-Options is nosniff | PASS | |
| CSRF cookie marked Secure | PASS | |
| 404 page is the custom page, not Django's debug page (so `DEBUG` is off) | PASS | HTTP 404 |
| Staff CRUD, immediate feedback, persistence | SKIPPED | QA staff login not supplied to this run |
| Customer cart add / update / remove | SKIPPED | QA customer login not supplied to this run |

**HTML and CSS** (`validate_site.py`, using the official validator.w3.org service): home, search results, empty search, a product page, cart, sign in, register and the 404 page, plus `style.css`: **0 errors, 0 warnings** on all 9. Customer and staff pages were skipped (no logins).

**Accessibility, keyboard, responsive, JavaScript** (`browser_checks.py`): home, product, cart and sign-in pages at 390, 768 and 1440px: **49 of 51 checks passed, 2 skipped (customer and staff sign-in), 0 failed**. This includes axe-core contrast and WCAG 2.1 A/AA rules, keyboard reach, visible focus, skip link, mobile menu and no console errors.

**The live site runs the fixed code.** The live pages pass the HTML checks that the old confirmation-modal markup failed on every page (bug 8), and the keyboard focus check that the old CSS failed on the amber buttons (bug 11). So the deployment includes this repository's fixes.

| Check | Command | Result (date, output) |
| --- | --- | --- |
| Live release is the current commit | `heroku releases -n 3` vs `git rev-parse --short HEAD` | Not checked directly (no Heroku CLI access). Indirectly confirmed above: the live pages include the fixes for bugs 8 and 11 |
| Config var names present | `heroku config --json` (names only) | Not yet recorded |
| Production audit | `heroku run python manage.py check --deploy` | Not yet recorded; the settings it audits were confirmed from outside on 20 Oct 2026 (table above) |
| Migrations applied | `heroku run python manage.py showmigrations` | Not yet recorded; the live pages that read every table load without errors |
| CRUD, feedback, persistence, HTTPS, headers | `tools/deployment_check.py` (Live site checks workflow) | 20 Oct 2026: HTTPS and headers 6 of 6 PASS; CRUD and cart SKIPPED (no QA logins yet) |
| HTML and CSS | `tools/validate_site.py` (Live site checks workflow) | 20 Oct 2026: 8 public pages + CSS, 0 errors, 0 warnings |
| Accessibility, keyboard, responsive | `tools/browser_checks.py` (Live site checks workflow) | 20 Oct 2026: 49 PASS, 2 SKIPPED, 0 FAIL |
| Uploaded image survives a restart | Upload a photo, `heroku restart`, reload the product | Not yet recorded |

To run the signed-in checks too, add the QA accounts' logins as repository secrets (Settings > Secrets and variables > Actions): `JOY2BUY_STAFF_USER`, `JOY2BUY_STAFF_PASSWORD`, `JOY2BUY_CUSTOMER_USER`, `JOY2BUY_CUSTOMER_PASSWORD`. Then start **Actions > Live site checks > Run workflow**.

---

## 9. Bugs found and fixed

Bugs 1-6 were found during development (recorded in the first version of this project). Bugs 7-13 were found by the testing added after assessment feedback; each fix is a separate commit.

| # | Bug | How it was found | Cause | Fix | Verified by |
| --- | --- | --- | --- | --- | --- |
| 1 | Site failed to start when `.env` had an empty `DATABASE_URL=` line | Development | An empty string was passed to the URL parser | `settings.py` uses `os.environ.get("DATABASE_URL") or <sqlite url>` | Fresh-clone setup in section 1 |
| 2 | Changing a cart quantity and pressing Enter sent two requests | Development | Browser fires both `change` and `submit` | `main.js` ignores a submission while one for the same form is in flight | Manual case 13 |
| 3 | After a rejected profile edit the navbar showed the rejected name | Development | Form was bound to `request.user` | `profile_edit` binds the form to a copy | `test_invalid_profile_update_changes_nothing` |
| 4 | `HEAD` requests returned 405 | Development | `require_GET` | Replaced with `require_safe` | Unit tests |
| 5 | Every anonymous page view created a session row | Development | Cart wrote an empty dict on first access | `Cart` only writes when contents change | Unit tests |
| 6 | Star-rating tag raised an error on wishlist cards | Development | Missing review count converted to a number | Tag treats a missing count as unknown | Manual case 30 |
| 7 | **Simultaneous or repeated cancellations returned stock more than once** (8 parallel cancels: stock 38 instead of 10), and a stale staff request could reopen a cancelled order | New concurrency tests (section 2) | Status was checked on a plain read *before* the transaction, then stock was returned without re-checking | `_change_status()` locks the order row with `select_for_update()`, re-reads the status inside the transaction and only then restocks. A cancelled order cannot change again | 7 new tests in `RepeatedCancellationTests` and 3 in `SimultaneousCancellationTests` (PostgreSQL), failing before and passing after; 10 repeated passes |
| 8 | Every page was invalid HTML | Nu HTML Checker | Confirmation modal had `aria-labelledby` on a `<div>` with no role (Bootstrap only adds `role="dialog"` when it opens) | `role="dialog"` and `aria-describedby` in `base.html` | `validate_site.py`: 0 errors on 22 pages |
| 9 | Order and review dates were invalid HTML | Nu HTML Checker | `date:'c'` outputs microseconds; HTML allows at most 3 fraction digits | Seconds-precision format in three templates | New test `test_order_date_is_a_valid_html_datetime` (failed before, passes after); validator |
| 10 | Grey and red outline buttons failed WCAG AA contrast (4.42:1 and 4.27:1) | axe-core | `.btn-outline-secondary` / `.btn-outline-danger` kept Bootstrap's default colours | Use the palette's muted (6.22:1) and danger (6.12:1) colours | `browser_checks.py` contrast: 0 failures |
| 11 | Amber buttons had **no** visible keyboard focus | Keyboard check | Bootstrap's `.btn:focus-visible` removed the outline; its replacement shadow needs a variable custom buttons do not set | `.btn:focus-visible` gets the site focus outline | `browser_checks.py` focus check: 0 failures |
| 12 | Focus outline too faint on the page background (2.46:1; 3:1 needed) | Contrast calculation | Amber-dark outline on warm white | Navy outline (15.06:1) on light areas; amber (7.9:1) in navy areas | Calculation and visual check of screenshots |
| 13 | Staff product page scrolled sideways on phones (443px in a 390px window) | Responsive check | A visually hidden, absolutely positioned table heading escaped the `.table-responsive` wrapper | `.table-responsive { position: relative; }` | `browser_checks.py` responsive: 0 failures |

Faults in the **test tools themselves** were also found and fixed before their results were used:
- The old validation script reported success without reading the results.
- An early version of the overflow check could miss sideways scrolling caused only by elements inside a scroll container. This was caught by re-running against the old CSS, where it failed to flag bug 13.
- Several walkthrough steps initially read the wrong element.

None of these changed the site's behaviour.

---

## 10. Known limitations

- **Live site partly verified.** HTTPS, security headers, `DEBUG` off, HTML/CSS validity and accessibility of the public pages were confirmed on the live site (section 8). The signed-in live checks (staff CRUD and persistence, customer cart) and the Heroku-side checks (`check --deploy`, config vars, image persistence) are not yet recorded.
- **Manual testing by hand is not yet recorded.** Most cases have scripted or automated evidence, but cases 8, 39 and 40 have no result yet, and the "By hand on live site" column is empty.
- **Development history.** The public Git history starts with one upload of the finished project, so it does not show how individual features were built and tested before 4 October 2026. Only changes made since then are recorded as individual commits.
- **Payments are simulated.** No card details are taken; Stripe or similar would be the next step.
- **No emails** are sent (order confirmation, password reset).
- **Uploaded images need S3 on Heroku**; without it they disappear on restart. The seed data has no photos, so image zoom (case 8) has not been tested.
- **CDN assets** (Bootstrap, Google Fonts) are loaded without Subresource Integrity hashes, and the site depends on those CDNs being available.
- **Concurrency tests need PostgreSQL.** On SQLite the 3 threaded tests are skipped; the stale-read tests still run there.
- **Automated accessibility checks are not complete coverage.** No screen-reader or 200% zoom testing has been done yet (cases 39-40).
- **The cart lives in the session**, so it does not follow a customer between devices.
