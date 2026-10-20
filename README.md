# JOY2BUY

[![Tests](https://github.com/Md12Ali/Joy2buy/actions/workflows/tests.yml/badge.svg)](https://github.com/Md12Ali/Joy2buy/actions/workflows/tests.yml)

A full-stack e-commerce storefront and order management system built with Django 5.2, PostgreSQL, Bootstrap 5 and vanilla JavaScript.

Submitted for the Level 5 Diploma in Web Application Development, Unit 3: Back-End Development.

> **Payments are simulated.** Checkout creates a real order record and reduces stock, but no card details are requested and no money is taken.

| | |
| --- | --- |
| Live site | <https://joy2buy-shop-218caf987cba.herokuapp.com/> |
| Repository | <https://github.com/Md12Ali/Joy2buy> |
| Testing report | [TESTING.md](TESTING.md) |
| Deployment guide | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| Author | Mohammed Ali ([Md12Ali](https://github.com/Md12Ali)) |

## Contents

1. [Project rationale and purpose](#1-project-rationale-and-purpose)
2. [User stories](#2-user-stories)
3. [UX and design](#3-ux-and-design)
4. [Features](#4-features)
5. [Database schema](#5-database-schema)
6. [Security features](#6-security-features)
7. [Project structure](#7-project-structure)
8. [Running the project locally](#8-running-the-project-locally)
9. [Environment variables](#9-environment-variables)
10. [Testing](#10-testing)
11. [Deployment](#11-deployment)
12. [Development process](#12-development-process)
13. [Attribution and code ownership](#13-attribution-and-code-ownership)

---

## 1. Project rationale and purpose

Small independent retailers often rely on marketplace listings they do not control, or on spreadsheets and email to track orders. JOY2BUY is a self-contained store that gives such a retailer one place to list products, take orders and see what needs dispatching, while giving shoppers a fast, uncluttered way to buy.

### Target audience

| Audience | Who they are | What they need |
| --- | --- | --- |
| Shoppers | Adults buying everyday items (audio, home, fitness, tech accessories, stationery, travel) on a phone or laptop | Find a product quickly, trust the price and stock level, check out with little typing, see past orders |
| Store staff | The shop owner or an employee, not necessarily technical | Add and edit products without touching code, hide products that are not ready, move orders through to delivery |

### Value proposition

**For buyers**

- Search with live suggestions, category tabs, sorting and an "in stock only" filter.
- Honest stock information on every product, with reviews from other customers.
- A cart that works before signing in and is kept after signing in.
- Free delivery over £50 with the remaining amount shown in the cart.
- An account page with order history, saved delivery details, reviews and a wishlist.

**For store staff**

- A management area inside the site for products, categories and orders.
- Draft and archived statuses so a product can be prepared or retired without deleting it.
- Stock is reduced automatically at checkout and returned automatically, exactly once, when an order is cancelled.
- Past orders keep the product name and price paid, even if the product is later changed or deleted.

---

## 2. User stories

### Visitor (not signed in)

| # | As a | I want to | So that |
| --- | --- | --- | --- |
| V1 | visitor | browse all products in a grid | I can see what the store sells |
| V2 | visitor | filter products by category | I only see the kind of item I am interested in |
| V3 | visitor | search by keyword and see suggestions as I type | I can reach a specific product quickly |
| V4 | visitor | sort by price, rating or newest | I can compare options my way |
| V5 | visitor | open a product page with photo, price, stock, specifications and reviews | I can decide whether to buy |
| V6 | visitor | add items to a cart without an account | I am not forced to register before I am ready |
| V7 | visitor | register for an account | I can check out and track my orders |

### Customer (signed in)

| # | As a | I want to | So that |
| --- | --- | --- | --- |
| C1 | customer | sign in and sign out | my account and orders stay private |
| C2 | customer | change quantities or remove items in my cart | the order is right before I pay |
| C3 | customer | see the delivery charge and total before checking out | there are no surprises |
| C4 | customer | check out with my saved address filled in for me | ordering again is quick |
| C5 | customer | see a confirmation with an order reference | I know the order went through |
| C6 | customer | view my order history and each order's status | I know when to expect delivery |
| C7 | customer | cancel an order that has not been dispatched | I can fix a mistake myself |
| C8 | customer | write, edit and delete my own product review | I can share my experience and correct it later |
| C9 | customer | save products to a wishlist | I can come back to them later |
| C10 | customer | update my name, email, address and password | my details stay current and secure |
| C11 | customer | get a clear message after every action | I know whether it worked |

### Store staff

| # | As a | I want to | So that |
| --- | --- | --- | --- |
| S1 | staff member | add a category | products can be organised |
| S2 | staff member | add a product with price, stock, description, specifications and photo | it can be sold |
| S3 | staff member | edit a product, including its stock and status | the catalogue stays accurate |
| S4 | staff member | delete a product after a confirmation step | mistakes and discontinued lines are removed safely |
| S5 | staff member | see every order and filter by status | I know what needs dispatching |
| S6 | staff member | update an order's status | customers can follow progress |
| S7 | staff member | remove an inappropriate review | the store stays trustworthy |
| S8 | staff member | be the only kind of user who can reach management pages | customers cannot change the catalogue |

---

## 3. UX and design

### Design principles

- **Mobile first.** Layouts are written for a narrow screen and widen at Bootstrap's `sm`, `lg` and `xl` breakpoints (1, 2, 3 then 4 product columns).
- **One clear action per screen.** The amber button is reserved for the step that moves a purchase forward: add to cart, go to checkout, place order.
- **Immediate feedback.** Every create, update and delete produces a message banner. Cart changes update the badge and totals without a page reload.
- **Progressive enhancement.** Every feature works as a normal form post with JavaScript switched off; JavaScript only makes it faster.

### Colour palette

Contrast ratios were calculated with the WCAG 2.1 formula and confirmed in the browser by axe-core (see [TESTING.md](TESTING.md#4-accessibility-keyboard-contrast-and-responsive-checks)).

| Role | Hex | Used for | Contrast |
| --- | --- | --- | --- |
| Ink (navy) | `#14213d` | Header, footer, headings, primary buttons, focus outline on light areas | 15.06:1 on Paper |
| Amber | `#fca311` | Calls to action, cart badge, focus outline on navy areas | Ink text on Amber 7.9:1; Amber on Ink 7.9:1 |
| Paper (warm white) | `#faf8f4` | Page background | - |
| Text | `#1b1f2a` | Body copy | 15.52:1 on Paper |
| Muted | `#565d6d` | Secondary text, secondary outline buttons | 6.22:1 on Paper |
| Link | `#1d3b8b` | Text links | 9.65:1 on Paper |
| Success / Warning / Danger | `#146c43` / `#8a5300` / `#b02a37` | Stock labels, errors, delete buttons | 6.08 / 5.97 / 6.12:1 on Paper |

All text pairs exceed the WCAG 2.1 AA minimum of 4.5:1 and focus outlines exceed the 3:1 minimum for non-text indicators. Stock status is never shown by colour alone: it always has a text label.

### Typography

| Use | Typeface | Weight | Why |
| --- | --- | --- | --- |
| Brand, headings, prices | Poppins | 600 to 700 | Geometric and friendly; gives the brand a recognisable voice |
| Body, forms, tables | Inter | 400 to 600 | Designed for screens, very legible at small sizes |
| Fallback | System UI stack | - | The page is fully usable if web fonts fail to load |

### Wireframes

These planning wireframes were included with the first upload of the project.

**Product list, mobile (under 576px)**

```
+------------------------------+
| Free UK delivery over £50    |
+------------------------------+
| JOY2BUY          [Cart 2] [=]|
+------------------------------+
| Everyday essentials that     |
| are a joy to buy.            |
| [ Browse the range ]         |
+------------------------------+
| All products    18 found     |
| [ ] In stock   Sort [Newest] |
| (All)(Audio)(Fitness)(Home)> |
+------------------------------+
| +--------------------------+ |
| |         [photo]          | |
| | AUDIO                    | |
| | Aria Wireless Headphones | |
| | ***** (12)               | |
| | £79.99                   | |
| | [      Add to cart     ] | |
| +--------------------------+ |
|            ...               |
+------------------------------+
```

**Product list, desktop (1200px and wider)**

```
+--------------------------------------------------------------------------+
|                     Free UK delivery on orders over £50                  |
+--------------------------------------------------------------------------+
| JOY2BUY   [ Search products          ][Search]   Shop v  Sam v  [Cart 2] |
+--------------------------------------------------------------------------+
| Everyday essentials that are a joy to buy.                               |
| [ Browse the range ]                                                     |
+--------------------------------------------------------------------------+
| All products                         [ ] In stock only   Sort [Newest v] |
| (All) (Audio) (Fitness) (Home & Kitchen) (Stationery) (Tech) (Travel)    |
| +-------------+  +-------------+  +-------------+  +-------------+       |
| |   [photo]   |  |   [photo]   |  |   [photo]   |  |   [photo]   |       |
| | Name        |  | Name        |  | Name        |  | Name        |       |
| | £79.99      |  | £54.99      |  | £24.99      |  | £12.50      |       |
| | [Add to cart]|  | [Add to cart]|  | [Out of stock]| | [Add to cart]|   |
| +-------------+  +-------------+  +-------------+  +-------------+       |
|                      < Previous  1  2  Next >                            |
+--------------------------------------------------------------------------+
```

**Cart and checkout, desktop**

```
+-----------------------------------------------+  +---------------------+
| [img] FlexGrip Yoga Mat 6 mm          £49.98  |  | Order summary       |
|       £24.99 each                             |  | Subtotal     £49.98 |
|       Quantity [ 2 ]   [Remove]               |  | Delivery      £4.99 |
+-----------------------------------------------+  | Total        £54.97 |
  Continue shopping                                | [ Go to checkout ]  |
                                                   +---------------------+
```

### Screenshots of the finished site

Full-page captures of the running application at 390px (mobile), 768px (tablet) and 1440px (desktop), produced by `tools/browser_checks.py --screenshots`. Every page in each folder is listed in [TESTING.md](TESTING.md#4-accessibility-keyboard-contrast-and-responsive-checks).

| | Mobile (390px) | Tablet (768px) | Desktop (1440px) |
| --- | --- | --- | --- |
| Home | [view](assets/images/screenshots/mobile/mobile-homepage.png) | [view](assets/images/screenshots/tablet/tablet-homepage.png) | [view](assets/images/screenshots/desktop/desktop-homepage.png) |
| Product detail | [view](assets/images/screenshots/mobile/mobile-product-detail.png) | [view](assets/images/screenshots/tablet/tablet-product-detail.png) | [view](assets/images/screenshots/desktop/desktop-product-detail.png) |
| Cart | [view](assets/images/screenshots/mobile/mobile-shopping-cart-full.png) | [view](assets/images/screenshots/tablet/tablet-shopping-cart-full.png) | [view](assets/images/screenshots/desktop/desktop-shopping-cart-full.png) |
| Checkout | [view](assets/images/screenshots/mobile/mobile-checkout.png) | [view](assets/images/screenshots/tablet/tablet-checkout.png) | [view](assets/images/screenshots/desktop/desktop-checkout.png) |
| Order detail | [view](assets/images/screenshots/mobile/mobile-order-detail.png) | [view](assets/images/screenshots/tablet/tablet-order-detail.png) | [view](assets/images/screenshots/desktop/desktop-order-detail.png) |
| Account | [view](assets/images/screenshots/mobile/mobile-account.png) | [view](assets/images/screenshots/tablet/tablet-account.png) | [view](assets/images/screenshots/desktop/desktop-account.png) |
| Staff: products | [view](assets/images/screenshots/mobile/mobile-staff-store-management.png) | [view](assets/images/screenshots/tablet/tablet-staff-store-management.png) | [view](assets/images/screenshots/desktop/desktop-staff-store-management.png) |
| Staff: orders | [view](assets/images/screenshots/mobile/mobile-staff-order-management.png) | [view](assets/images/screenshots/tablet/tablet-staff-order-management.png) | [view](assets/images/screenshots/desktop/desktop-staff-order-management.png) |

![Desktop home page](assets/images/screenshots/desktop/desktop-homepage.png)

### Accessibility

- Semantic landmarks: `header`, `nav`, `main`, `section`, `aside`, `footer`, each labelled where there is more than one.
- A "Skip to main content" link is the first focusable element.
- Every form control has a visible `label`; errors are shown next to the field and required fields are marked in text as well as visually.
- Star ratings expose a text alternative such as "Rated 4.5 out of 5".
- Cart count and messages use `aria-live` so screen readers announce changes.
- A visible focus outline on every interactive element, and `prefers-reduced-motion` is respected.
- Images carry meaningful `alt` text; decorative icons are hidden from assistive technology.

---

## 4. Features

### CRUD summary

| Operation | Customers | Staff |
| --- | --- | --- |
| **Create** | Register, add to cart, place an order, write a review, save to wishlist | Add categories and products |
| **Read** | Product list, live search, category filter, product detail, cart, order history | Product and order management tables, any order |
| **Update** | Cart quantities, profile and delivery details, password, own review, cancel own order | Edit products and categories, change order status |
| **Delete** | Remove cart lines, delete own review, remove from wishlist | Delete products, empty categories and any review |

### Defensive design

- All input is validated on the server by Django forms, whatever the browser sends. HTML attributes (`min`, `max`, `required`, `maxlength`) are a convenience only.
- Cart quantities are capped at the stock available and at 20 per line. Prices are never stored in the session, so they cannot be altered by the shopper.
- Checkout runs in one database transaction with the product rows locked: either the order, its lines and the stock change are all saved, or none are.
- Cancelling an order (by the customer or by staff) locks the order row and re-reads its status inside the transaction before returning stock, so simultaneous or repeated requests can never return the same stock twice or reopen a cancelled order.
- Views that change data accept `POST` only. Deleting a product shows a confirmation page; other deletions ask for confirmation in a modal.
- Draft and archived products return 404 to shoppers. Orders can be opened only by their owner or by staff (403 otherwise).
- Redirect targets supplied by the browser are checked to be on this site.
- Custom 403, 404 and 500 pages keep users inside the site with a way back.

---

## 5. Database schema

The project uses Django's ORM over a relational database: PostgreSQL in production and SQLite for quick local development. There are six project models in four apps. `User` is Django's built-in `auth.User`.

The shopping cart is **not** a table. It lives in the visitor's session as `{"<product id>": quantity}` so guests can shop before registering; names and prices are always read from the database. Stock is a single `stock` column on `Product`, not a separate inventory table, and products have no variants (SKUs). See [Not implemented](#not-implemented-future-features).

### Entity relationship diagram

```mermaid
erDiagram
    USER ||--|| USERPROFILE : "has (CASCADE)"
    USERPROFILE }o--o{ PRODUCT : "wishlist (M2M)"
    CATEGORY ||--o{ PRODUCT : "contains (PROTECT)"
    PRODUCT ||--o{ PRODUCTREVIEW : "receives (CASCADE)"
    USER ||--o{ PRODUCTREVIEW : "writes (CASCADE)"
    USER |o--o{ ORDER : "places (SET NULL)"
    ORDER ||--|{ ORDERITEM : "contains (CASCADE)"
    PRODUCT |o--o{ ORDERITEM : "sold as (SET NULL)"

    USER {
        bigint id PK
        varchar username UK
        varchar email
        bool is_staff
    }
    USERPROFILE {
        bigint id PK
        bigint user_id FK, UK
        varchar phone
        varchar address_line1
        varchar address_line2
        varchar city
        varchar postcode
        varchar country
        datetime created
        datetime updated
    }
    CATEGORY {
        bigint id PK
        varchar name UK
        varchar slug UK
        text description
        varchar image
    }
    PRODUCT {
        bigint id PK
        bigint category_id FK
        varchar name
        varchar slug UK
        text description
        text specifications
        decimal price
        int stock
        varchar image
        decimal rating
        varchar status
        datetime created
        datetime updated
    }
    PRODUCTREVIEW {
        bigint id PK
        bigint product_id FK
        bigint user_id FK
        smallint rating
        text text
        datetime created
        datetime updated
    }
    ORDER {
        bigint id PK
        bigint user_id FK
        varchar status
        varchar transaction_id UK
        varchar full_name
        varchar email
        varchar phone
        varchar address_line1
        varchar address_line2
        varchar city
        varchar postcode
        varchar country
        decimal subtotal
        decimal delivery_cost
        decimal total
        datetime created
        datetime updated
    }
    ORDERITEM {
        bigint id PK
        bigint order_id FK
        bigint product_id FK
        varchar product_name
        decimal unit_price
        int quantity
    }
```

The same diagram as an image: [assets/images/erd.png](assets/images/erd.png).

The wishlist is stored in Django's automatic join table `profiles_userprofile_wishlist` (`id`, `userprofile_id`, `product_id`, with a unique constraint on the pair).

### Relationships and deletion behaviour

| From | Type | To | Field | On delete | What happens and why |
| --- | --- | --- | --- | --- | --- |
| UserProfile | One-to-one | User | `user` | CASCADE | Deleting an account deletes its profile. Every account has exactly one profile, created by a `post_save` signal. |
| UserProfile | Many-to-many | Product | `wishlist` | Join rows removed | Deleting either a profile or a product removes only the link, never the other side. |
| Product | Many-to-one | Category | `category` | **PROTECT** | A category that still contains products cannot be deleted (the database refuses and the staff page explains why). Products must be moved or deleted first. |
| ProductReview | Many-to-one | Product | `product` | CASCADE | A product's reviews are deleted with it. |
| ProductReview | Many-to-one | User | `user` | CASCADE | A user's reviews are deleted with their account. A signal then recalculates the product's average `rating`. |
| Order | Many-to-one | User | `user` | **SET NULL** | Sales records survive account deletion; the order keeps its copied name, email and address. |
| OrderItem | Many-to-one | Order | `order` | CASCADE | Lines cannot exist without their order. |
| OrderItem | Many-to-one | Product | `product` | **SET NULL** | Order history survives product deletion: `product_name` and `unit_price` are copied onto the line at checkout, so the record of what was bought and for how much never changes. |

### Field tables

"Database" constraints are enforced by PostgreSQL itself; "Validation" rules are enforced by Django forms and model validators before anything is saved.

#### Category

| Field | Type | Constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | Primary key | |
| `name` | CharField(80) | Database: NOT NULL, UNIQUE | |
| `slug` | SlugField(100) | Database: UNIQUE | Generated from the name on save |
| `description` | TextField | Optional | |
| `image` | ImageField | Optional. Validation: real image, 2 MB maximum | Stored under `categories/` |

#### Product

| Field | Type | Constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | Primary key | |
| `category` | ForeignKey to Category | Database: NOT NULL, FK, ON DELETE PROTECT, indexed | |
| `name` | CharField(120) | Database: NOT NULL | |
| `slug` | SlugField(140) | Database: UNIQUE | Generated from the name, numbered if already taken |
| `description` | TextField | Database: NOT NULL | |
| `specifications` | TextField | Optional | One "Label: value" per line |
| `price` | DecimalField(8,2) | Validation: minimum 0.01 | Exact decimal arithmetic, never floats |
| `stock` | PositiveIntegerField | Database: CHECK `stock >= 0`; default 0 | Reduced at checkout under a row lock; returned once on cancellation |
| `image` | ImageField | Optional. Validation: real image, 2 MB maximum | Stored under `products/` |
| `rating` | DecimalField(3,2) | Not editable; default 0.00 | Average review score, kept up to date by signals |
| `status` | CharField(10) | Choices: `active`, `draft`, `archived`; default `active` | Only active products are visible to shoppers |
| `created`, `updated` | DateTimeField | Set automatically | |

Index `product_status_created_idx` on (`status`, `created` descending) supports the storefront listing.

#### ProductReview

| Field | Type | Constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | Primary key | |
| `product` | ForeignKey to Product | Database: FK, ON DELETE CASCADE, indexed | |
| `user` | ForeignKey to User | Database: FK, ON DELETE CASCADE, indexed | |
| `rating` | PositiveSmallIntegerField | Database: CHECK `rating >= 0`. Validation: 1 to 5 | |
| `text` | TextField | Validation: 10 to 1000 characters | |
| `created`, `updated` | DateTimeField | Set automatically | |

Unique constraint `one_review_per_user_per_product` on (`product`, `user`): each customer has at most one review per product; submitting again edits it.

#### UserProfile

| Field | Type | Constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | Primary key | |
| `user` | OneToOneField to User | Database: FK, UNIQUE, ON DELETE CASCADE | |
| `phone` | CharField(20) | Optional | |
| `address_line1`, `address_line2` | CharField(120) | Optional | |
| `city` | CharField(60) | Optional | |
| `postcode` | CharField(12) | Optional | |
| `country` | CharField(60) | Optional; default "United Kingdom" | |
| `wishlist` | ManyToManyField to Product | Join table, unique per pair | |
| `created`, `updated` | DateTimeField | Set automatically | |

#### Order

| Field | Type | Constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | Primary key | |
| `user` | ForeignKey to User | Nullable. Database: FK, ON DELETE SET NULL | |
| `status` | CharField(12) | Choices: `pending`, `processing`, `shipped`, `delivered`, `cancelled`; default `pending` | Customers may cancel only while pending or processing; a cancelled order cannot be reopened |
| `transaction_id` | CharField(32) | Database: UNIQUE. Not editable | 16-character random reference, used in URLs instead of the numeric id |
| `full_name`, `email`, `phone` | CharField / EmailField | Required. Validation: email format, phone and postcode patterns | Copied at checkout |
| `address_line1`, `address_line2`, `city`, `postcode`, `country` | CharField | `address_line2` optional | The address as it was when ordered |
| `subtotal`, `total` | DecimalField(10,2) | Default 0.00 | Recalculated from the lines by `update_totals()` |
| `delivery_cost` | DecimalField(6,2) | Default 0.00 | Free at £50 or more, otherwise £4.99 (both configurable) |
| `created`, `updated` | DateTimeField | Set automatically | Orders are listed newest first |

#### OrderItem

| Field | Type | Constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | Primary key | |
| `order` | ForeignKey to Order | Database: FK, ON DELETE CASCADE | |
| `product` | ForeignKey to Product | Nullable. Database: FK, ON DELETE SET NULL | |
| `product_name` | CharField(120) | Required | Name at the time of purchase |
| `unit_price` | DecimalField(8,2) | Validation: minimum 0.00 | Price at the time of purchase |
| `quantity` | PositiveIntegerField | Database: CHECK `quantity >= 0`. Validation: minimum 1 | |

### Not implemented (future features)

The following do **not** exist in the code or database and are listed only as possible future work: product variants / SKUs, a separate inventory or stock-movement table, payment records, and delivery tracking. Earlier versions of this README mentioned `SKU`, `Inventory` and `OrderLineItem` models; those were errors. The order line model is `OrderItem`.

---

## 6. Security features

| Area | What is done | Where |
| --- | --- | --- |
| Secrets | `SECRET_KEY`, database URL and AWS keys are read from environment variables. `.env` is in `.gitignore`; only `.env.example` with placeholders is committed. The app refuses to start without a `SECRET_KEY` when `DEBUG` is off. The full Git history has been reviewed for leaked credentials (see [TESTING.md](TESTING.md#7-credential-review)). | `joy2buy/settings.py` |
| Debug mode | `DEBUG` defaults to `False` and is only turned on by `DEBUG=True` in a local `.env`. | `joy2buy/settings.py` |
| Passwords | Stored only as salted PBKDF2 hashes. Four validators enforce length (8+), reject common and all-numeric passwords, and reject passwords similar to the username or email. | `AUTH_PASSWORD_VALIDATORS` |
| CSRF | `CsrfViewMiddleware` is enabled and every `POST` form includes `{% csrf_token %}`. JavaScript requests send the same token. | Templates, `static/js/main.js` |
| Authentication | `@login_required` protects checkout, orders, account, reviews and wishlist. Logging out requires `POST`. | App `views.py` files |
| Authorisation | `@staff_required` protects all management views: anonymous users are redirected to sign in, signed-in customers receive 403. Object-level checks ensure customers can only see or cancel their own orders and delete their own reviews. | `joy2buy/decorators.py`, `orders/views.py`, `products/views.py` |
| Concurrency | Checkout locks product rows; cancellation and status changes lock the order row and re-check its status, so stock cannot be oversold or returned twice. | `orders/views.py` |
| Input validation | Server-side validation on every form; uploaded images are verified by Pillow and limited to 2 MB. | App `forms.py`, `products/validators.py` |
| SQL injection | All queries go through the Django ORM with bound parameters. No raw SQL. | - |
| Cross-site scripting | Template auto-escaping everywhere. JavaScript inserts server text with `textContent`, never `innerHTML`. | Templates, `static/js/main.js` |
| HTTPS | With `DEBUG=False`: HTTPS redirect (`SECURE_SSL_REDIRECT`, on by default), `SECURE_PROXY_SSL_HEADER` for Heroku's router, Secure session and CSRF cookies, HSTS for 30 days including subdomains, `X-Frame-Options: DENY`, `nosniff`, same-origin referrer policy. | `joy2buy/settings.py` |

Run Django's production audit at any time with `python manage.py check --deploy` (results are in [TESTING.md](TESTING.md#6-production-settings)).

---

## 7. Project structure

```
Joy2buy/
├── manage.py
├── requirements.txt          Python dependencies
├── Procfile                  Heroku process types (release: migrate, web: gunicorn)
├── runtime.txt               Python version for Heroku (3.12)
├── .env.example              Template for environment variables
├── setup.cfg                 flake8 settings
├── README.md / TESTING.md / DEPLOYMENT_GUIDE.md
├── joy2buy/                  Project package: settings, root URLs, error views, staff_required
├── products/                 Category, Product, ProductReview; storefront and staff CRUD
│   ├── management/commands/seed_store.py
│   └── templatetags/store_extras.py
├── cart/                     Session cart (cart.py), views, context processor
├── orders/                   Order, OrderItem; checkout, cancellation, order management
├── profiles/                 UserProfile; sign up, dashboard, wishlist
├── templates/                base.html, error pages, one folder per app, includes/
├── static/                   css/style.css, js/main.js, images/favicon.svg
├── .github/workflows/        tests.yml (CI), live-checks.yml (checks the deployed site)
├── tools/                    validate_site.py, browser_checks.py, ui_walkthrough.py, deployment_check.py
├── assets/images/screenshots Real screenshots (mobile, tablet, desktop)
└── media/                    Uploaded images in local development only
```

---

## 8. Running the project locally

Requirements: Python 3.12 (3.11 or newer works) and Git. PostgreSQL is optional locally; without `DATABASE_URL` a SQLite file is used.

```bash
git clone https://github.com/Md12Ali/Joy2buy.git
cd Joy2buy

python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                 # Windows: copy .env.example .env
```

Edit `.env` for local development:

```ini
DEBUG=True
SECRET_KEY=any-long-random-string-for-local-use
SECURE_SSL_REDIRECT=False
DATABASE_URL=
```

Then create the database, load the starter catalogue and create a staff account:

```bash
python manage.py migrate
python manage.py seed_store          # 6 categories and 18 products; safe to run again
python manage.py createsuperuser     # your staff account
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Sign in with the superuser to see **Store management** in the account menu. The Django admin is at `/admin/`.

`seed_store` loads only categories and products. It creates no users, reviews or orders.

To use MySQL instead of PostgreSQL, install `mysqlclient` and set `DATABASE_URL=mysql://USER:PASSWORD@HOST:3306/DBNAME`. No code changes are needed.

---

## 9. Environment variables

All configuration is read from the environment (from `.env` locally, from config vars on Heroku). Nothing secret is stored in the repository.

| Variable | Required | Default | Production value | Purpose |
| --- | --- | --- | --- | --- |
| `SECRET_KEY` | Yes when `DEBUG=False` | Random throwaway key only when `DEBUG=True` | 50+ random characters | Signs sessions and CSRF tokens. The app will not start in production without it. |
| `DEBUG` | No | `False` | `False` | Never `True` on a public site. |
| `ALLOWED_HOSTS` | Yes in production | `localhost,127.0.0.1` | `joy2buy-shop-218caf987cba.herokuapp.com` | Comma-separated host names the site answers to. |
| `CSRF_TRUSTED_ORIGINS` | Yes in production | empty | `https://joy2buy-shop-218caf987cba.herokuapp.com` | Origins (with scheme) allowed to submit forms. |
| `DATABASE_URL` | Yes in production | SQLite file `db.sqlite3` | Set by the Heroku Postgres add-on | Database connection. |
| `DATABASE_SSL_REQUIRE` | Recommended | `False` | `True` | Require TLS to the database. |
| `SECURE_SSL_REDIRECT` | No | `True` when `DEBUG=False` | Leave unset (`True`) | Redirect HTTP to HTTPS. Also controls Secure cookies and HSTS; set `False` only for a local plain-HTTP run. |
| `USE_AWS` | For persistent uploads | `False` | `True` | Store uploaded images in Amazon S3 (see below). |
| `AWS_STORAGE_BUCKET_NAME` | If `USE_AWS=True` | - | your bucket | S3 bucket for uploads. |
| `AWS_S3_REGION_NAME` | If `USE_AWS=True` | `eu-west-2` | your region | |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | If `USE_AWS=True` | - | an IAM user limited to that bucket | Read by boto3. |
| `FREE_DELIVERY_THRESHOLD` | No | `50.00` | | Subtotal at which delivery becomes free. |
| `STANDARD_DELIVERY_COST` | No | `4.99` | | Delivery charge below the threshold. |

### Persistent image storage

Heroku's file system is temporary: anything written to `media/` disappears when the dyno restarts (at least once a day and on every deploy). Product and category photos uploaded through the site therefore need external storage in production. With `USE_AWS=True` the default file storage becomes `storages.backends.s3.S3Storage` and `MEDIA_URL` points at the bucket. Without S3 the store still works, and products without a photo show a coloured tile with their initials. Step-by-step bucket setup is in [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#6-persistent-image-storage-amazon-s3).

---

## 10. Testing

The full report, with commands, outputs, manual test steps, bugs found and fixed, and known limitations, is in **[TESTING.md](TESTING.md)**. In summary:

| Check | Command | Result |
| --- | --- | --- |
| Automated tests (SQLite) | `python manage.py test` | 122 tests: 119 pass, 3 skipped (need PostgreSQL row locks) |
| Automated tests (PostgreSQL) | `DATABASE_URL=postgres://... python manage.py test` | 122 of 122 pass |
| PEP 8 | `python -m flake8` | 0 findings |
| JavaScript lint | `npx eslint static/js` | 0 problems |
| Migrations match models | `python manage.py makemigrations --check --dry-run` | No changes |
| HTML and CSS (Nu HTML Checker) | `python tools/validate_site.py` | 22 public, customer and staff pages plus `style.css`: 0 errors, 0 warnings |
| Accessibility, keyboard, responsive, JS | `python tools/browser_checks.py` | 145 of 145 checks pass |
| Browser-level manual test cases | `python tools/ui_walkthrough.py` | 28 of 28 scripted cases pass; results for each of the 40 planned cases in TESTING.md |
| Deployment CRUD and persistence | `python tools/deployment_check.py` | 19 of 19 checks pass on a production-like local build |
| Continuous integration | GitHub Actions `Tests` workflow on every push | flake8, migrations and all 122 tests on PostgreSQL 16 and SQLite |
| Live site | GitHub Actions `Live site checks` workflow | HTTPS, headers, HTML/CSS and accessibility checked on the deployed site (TESTING.md section 8) |

---

## 11. Deployment

The live site runs on Heroku with Heroku Postgres. Complete, tested instructions are in **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**. In short:

```bash
heroku create <app-name>
heroku addons:create heroku-postgresql:essential-0
heroku config:set SECRET_KEY="<random>" DEBUG=False DATABASE_SSL_REQUIRE=True \
    ALLOWED_HOSTS=<app-host> CSRF_TRUSTED_ORIGINS=https://<app-host>
git push heroku main          # build runs collectstatic; release phase runs migrate
heroku run python manage.py seed_store
heroku run python manage.py createsuperuser
```

---

## 12. Development process

### What the Git history shows

The public repository's history begins with a single upload of the finished project (`220439c`, 4 October 2026), followed by documentation and tooling commits. Feature-by-feature development before that upload is not recorded in this repository. The developer has confirmed that no other records of that earlier work (older repositories, archives, notes or screenshots) exist, so none are included, and none have been recreated after the fact.

### Commits since assessment feedback

Each change made in response to assessment feedback is a separate commit with a message explaining the problem, how it was found, and how it was verified:

| Commit | Change |
| --- | --- |
| `Lock and recheck order status before restocking on cancellation` | Concurrency fix with failing-then-passing tests (see TESTING.md, bug 7) |
| `Rewrite site validator to check validator results, not screenshots` | `tools/validate_site.py` |
| `Fix two HTML validation errors found by the Nu checker` | Bugs 8 and 9 |
| `Fix contrast, focus visibility and phone overflow found by axe` | Bugs 10 to 13 |
| `Add browser checks for responsive layout, keyboard, contrast and JS` | `tools/browser_checks.py` |
| `Replace placeholder images with real screenshots` | Removes mock-up images that were not real evidence |
| `Add deployment check using controlled test records` | `tools/deployment_check.py` |
| `Add scripted walkthrough of manual test cases; remove stale scripts` | `tools/ui_walkthrough.py` |
| `Rewrite README, deployment guide and testing report` | This documentation |
| `Add GitHub Actions: tests on PostgreSQL and on-demand live site checks` | CI on every push; checks of the deployed site |
| `Record live site check results` | Live results in TESTING.md section 8 |

Run `git log --stat` to see each commit in full.

---

## 13. Attribution and code ownership

### Project code

- `joy2buy/`, `products/`, `cart/`, `orders/`, `profiles/` (models, forms, views, URLs, admin, tests, template tags, management command)
- `templates/`, `static/css/style.css`, `static/js/main.js`, `static/images/favicon.svg`
- `tools/` (validation, browser, walkthrough and deployment check scripts)
- Product names, descriptions and specifications in `seed_store.py` are original, fictional catalogue entries. No third-party product photos are included.

**Development tools.** An AI assistant (Claude, by Anthropic) was used to help write and review code, tests and documentation, including the changes made after assessment feedback. Commits made with its help are marked with a `Co-Authored-By: Claude` trailer. The developer is responsible for the submitted work.

### External libraries and frameworks

Used unmodified; not the developer's own work.

| Library | Used for | Licence |
| --- | --- | --- |
| [Django](https://www.djangoproject.com/) | Web framework, ORM, authentication, forms, messages, admin, test runner | BSD-3-Clause |
| [Bootstrap 5.3](https://getbootstrap.com/) (CDN) | Grid, navbar, alerts, modal, dropdowns, form styles | MIT |
| [gunicorn](https://gunicorn.org/) | Production WSGI server | MIT |
| [WhiteNoise](https://whitenoise.readthedocs.io/) | Serving compressed static files | MIT |
| [dj-database-url](https://github.com/jazzband/dj-database-url) | Parsing `DATABASE_URL` | BSD-3-Clause |
| [psycopg2](https://www.psycopg.org/) | PostgreSQL driver | LGPL |
| [Pillow](https://python-pillow.org/) | Validating uploaded images | MIT-CMU (HPND) |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Loading `.env` in development | BSD-3-Clause |
| [django-storages](https://django-storages.readthedocs.io/) and boto3 | Optional Amazon S3 media storage | BSD-3-Clause / Apache-2.0 |
| [Google Fonts](https://fonts.google.com/): Inter, Poppins | Typography | SIL Open Font Licence |

Testing tools (not part of the deployed site): [Nu HTML Checker](https://validator.github.io/validator/) (MIT), [axe-core](https://github.com/dequelabs/axe-core) (MPL-2.0), [Playwright](https://playwright.dev/python/) (Apache-2.0), [flake8](https://flake8.pycqa.org/) (MIT).

### Patterns adapted from documentation

- The session-based cart follows the general approach in the Django documentation on [sessions](https://docs.djangoproject.com/en/5.2/topics/http/sessions/); the implementation in `cart/cart.py` is original.
- Row locking follows the Django documentation for [`select_for_update()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).
- Production settings follow the Django [deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) and the WhiteNoise documentation.
