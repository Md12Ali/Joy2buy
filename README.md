# JOY2BUY

A full-stack e-commerce storefront and order management system built with Django, PostgreSQL, Bootstrap 5 and vanilla JavaScript.

Submitted for the Level 5 Diploma in Web Application Development, Unit 3: Back-End Development.

> **Payments are simulated.** Checkout creates a real order record and reduces stock, but no card details are requested and no money is taken.

## Contents

1. [Project rationale and purpose](#1-project-rationale-and-purpose)
2. [User stories](#2-user-stories)
3. [UX and design strategy](#3-ux-and-design-strategy)
4. [Features](#4-features)
5. [Database schema](#5-database-schema)
6. [Security features](#6-security-features)
7. [Project structure](#7-project-structure)
8. [Running the project locally](#8-running-the-project-locally)
9. [Testing](#9-testing)
10. [Deployment](#10-deployment)
11. [Attribution and code ownership](#11-attribution-and-code-ownership)

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

**For store admins**

- A management area inside the site for products, categories and orders. No separate tool to learn.
- Draft and archived statuses so a product can be prepared or retired without deleting it.
- Stock is reduced automatically at checkout and returned automatically when an order is cancelled.
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

## 3. UX and design strategy

### Design principles

- **Mobile first.** Layouts are written for a narrow screen and widen at Bootstrap's `sm`, `lg` and `xl` breakpoints (1, 2, 3 then 4 product columns).
- **One clear action per screen.** The amber button is reserved for the step that moves a purchase forward: add to cart, go to checkout, place order.
- **Immediate feedback.** Every create, update and delete produces a message banner. Cart changes update the badge and totals without a page reload.
- **Progressive enhancement.** Every feature works as a normal form post with JavaScript switched off; JavaScript only makes it faster.

### Colour palette

| Role | Colour | Hex | Rationale | Contrast |
| --- | --- | --- | --- | --- |
| Ink | Navy | `#14213d` | Header, footer, headings and primary buttons. A dark neutral reads as dependable and lets product photos stand out. | 15.1:1 on Paper |
| Accent | Amber | `#fca311` | Calls to action and the cart badge. Warm and energetic, matching the "joy" in the name; used sparingly so it always means "do this next". | 7.9:1 with Ink text |
| Paper | Warm white | `#faf8f4` | Page background. Softer than pure white for long browsing sessions. | - |
| Text | Near black | `#1b1f2a` | Body copy. | 15.5:1 on Paper |
| Muted | Slate | `#565d6d` | Secondary text such as category labels. | 6.2:1 on Paper |
| Link | Blue | `#1d3b8b` | Text links, clearly different from body text. | 9.7:1 on Paper |
| Success / Warning / Danger | Green / Brown / Red | `#146c43` / `#8a5300` / `#b02a37` | In stock, low stock, out of stock and errors. | 6.1:1 or better |

All body text pairs exceed the WCAG 2.1 AA minimum of 4.5:1. Stock status is never shown by colour alone: it always has a text label.

### Typography

| Use | Typeface | Weight | Why |
| --- | --- | --- | --- |
| Brand, headings, prices | Poppins | 600 to 700 | Geometric and friendly; gives the brand a recognisable voice |
| Body, forms, tables | Inter | 400 to 600 | Designed for screens, very legible at small sizes |
| Fallback | System UI stack | - | The page is fully usable if web fonts fail to load |

Hierarchy: one `h1` per page, `h2` for page sections, `h3` for items inside a section (product cards, individual reviews).

### Wireframes

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
| +--------------------------+ |
| |         [photo]          | |
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
| 18 products found                                                        |
| (All) (Audio) (Fitness) (Home & Kitchen) (Stationery) (Tech) (Travel)    |
|                                                                          |
| +-------------+  +-------------+  +-------------+  +-------------+       |
| |   [photo]   |  |   [photo]   |  |   [photo]   |  |   [photo]   |       |
| | AUDIO       |  | TRAVEL      |  | FITNESS     |  | STATIONERY  |       |
| | Name        |  | Name        |  | Name        |  | Name        |       |
| | *****  (12) |  | ****   (3)  |  | No reviews  |  | *****  (8)  |       |
| | £79.99      |  | £54.99      |  | £24.99      |  | £12.50      |       |
| | [Add to cart]|  | [Add to cart]|  | [Out of stock]| | [Add to cart]|   |
| +-------------+  +-------------+  +-------------+  +-------------+       |
|                      < Previous  1  2  Next >                            |
+--------------------------------------------------------------------------+
| JOY2BUY          Shop              Account           Built with          |
+--------------------------------------------------------------------------+
```

**Product detail, desktop**

```
+--------------------------------------------------------------------------+
| Shop / Audio / Aria Wireless Over-Ear Headphones                         |
|                                                                          |
| +----------------------------+   AUDIO                                   |
| |                            |   Aria Wireless Over-Ear Headphones       |
| |        [large photo]       |   ***** 4.5 out of 5 from 12 reviews      |
| |      hover to zoom         |   £79.99                                  |
| |                            |   (o) In stock (24 available)             |
| +----------------------------+   Description text...                     |
|                                  Quantity [ 1 ]  [    Add to cart    ]   |
|                                  [ Save to wishlist ]                    |
|                                                                          |
| Specifications                                                           |
| Battery life      | Up to 30 hours                                       |
| Connectivity      | Bluetooth 5.3 and 3.5 mm cable                       |
|                                                                          |
| Customer reviews (12)                                                    |
| +---------------------+   +------------------------------------------+   |
| | Write a review      |   | ***** Sam               3 October 2026   |   |
| | Rating [ Choose v ] |   | Comfortable and clear.  [Delete review]  |   |
| | [ text area       ] |   +------------------------------------------+   |
| | [ Submit review ]   |   | ****  Alex ...                           |   |
| +---------------------+   +------------------------------------------+   |
+--------------------------------------------------------------------------+
```

**Cart and checkout, desktop**

```
+-----------------------------------------------+  +---------------------+
| [img] FlexGrip Yoga Mat 6 mm          £49.98  |  | Order summary       |
|       £24.99 each                             |  | Subtotal     £49.98 |
|       Quantity [ 2 ]   [Remove]               |  | Delivery      £4.99 |
+-----------------------------------------------+  | Total        £54.97 |
| [img] Insulated Steel Water Bottle    £18.50  |  | Spend £0.02 more    |
|       Quantity [ 1 ]   [Remove]               |  | for free delivery   |
+-----------------------------------------------+  | [ Go to checkout ]  |
  Continue shopping                                +---------------------+
```

### Accessibility

- Semantic landmarks: `header`, `nav`, `main`, `section`, `aside`, `footer`, each labelled where there is more than one.
- A "Skip to main content" link is the first focusable element.
- Every form control has a visible `label`; errors are announced next to the field and required fields are marked in text as well as visually.
- Star ratings expose a text alternative such as "Rated 4.5 out of 5".
- Cart count and messages use `aria-live` so screen readers announce changes.
- A visible focus outline on every interactive element, and `prefers-reduced-motion` is respected.
- Images carry meaningful `alt` text; decorative icons are hidden from assistive technology.
- External links open in a new tab with `rel="noopener noreferrer"` and say so to screen readers.

---

## 4. Features

### CRUD summary

| Operation | Customers | Staff |
| --- | --- | --- |
| **Create** | Register, add to cart, place an order, write a review, save to wishlist | Add categories and products |
| **Read** | Product list, live search, category filter, product detail, cart, order history, review log | Product and order management tables, any order |
| **Update** | Cart quantities, profile and delivery details, password, own review, cancel own order | Edit products and categories, change order status |
| **Delete** | Remove cart lines, delete own review, remove from wishlist | Delete products, empty categories and any review |

### Defensive design

- All input is validated on the server by Django forms, whatever the browser sends. HTML attributes (`min`, `max`, `required`, `maxlength`) are a convenience only.
- Cart quantities are capped at the stock available and at 20 per line. Prices are never stored in the session, so they cannot be altered by the shopper.
- Checkout runs in one database transaction with the product rows locked: either the order, its lines and the stock change are all saved, or none are.
- Views that change data accept `POST` only. Deleting a product shows a confirmation page; other deletions ask for confirmation in a modal.
- Draft and archived products return 404 to shoppers. Orders can be opened only by their owner or by staff (403 otherwise).
- Redirect targets supplied by the browser are checked to be on this site.
- Custom 403, 404 and 500 pages keep users inside the site with a way back.

---

## 5. Database schema

The project uses Django's ORM over a relational database (PostgreSQL in production, SQLite for local development). `User` is Django's built-in `auth.User`.

### Entity relationship diagram

```
                1        1                         *        *
     User ----------------- UserProfile -------------------- Product
      | 1                    (wishlist: many-to-many)        | *  | 1
      |                                                      |    |
      | *                                                    | 1  | *
    Order 1 ------- * OrderItem * ------- 0..1 Product   Category |
      (CASCADE)            (SET NULL)                             |
                                                                  |
     User 1 ---------- * ProductReview * ------------------------ 1 Product
```

### Relationships

| From | Type | To | Field | On delete | Meaning |
| --- | --- | --- | --- | --- | --- |
| UserProfile | One-to-one | User | `user` | CASCADE | Each account has exactly one profile, created automatically by a signal |
| UserProfile | Many-to-many | Product | `wishlist` | - | A customer saves many products; a product is saved by many customers |
| Product | Many-to-one (FK) | Category | `category` | PROTECT | A category cannot be deleted while it contains products |
| ProductReview | Many-to-one (FK) | Product | `product` | CASCADE | Reviews are removed with their product |
| ProductReview | Many-to-one (FK) | User | `user` | CASCADE | Reviews are removed with their author |
| Order | Many-to-one (FK) | User | `user` | SET NULL | Sales records survive account deletion |
| OrderItem | Many-to-one (FK) | Order | `order` | CASCADE | Lines belong to one order |
| OrderItem | Many-to-one (FK) | Product | `product` | SET NULL | Lines survive product deletion (name and price are copied onto the line) |

### Category

| Field | Type | Key / constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | **PK** | |
| `name` | CharField(80) | unique | |
| `slug` | SlugField(100) | unique | Generated from the name |
| `description` | TextField | optional | |
| `image` | ImageField | optional, 2 MB limit | Stored under `media/categories/` |

### Product

| Field | Type | Key / constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | **PK** | |
| `category` | ForeignKey | **FK** to Category, PROTECT | |
| `name` | CharField(120) | | |
| `slug` | SlugField(140) | unique | Generated from the name, numbered if taken |
| `description` | TextField | | |
| `specifications` | TextField | optional | One "Label: value" per line |
| `price` | DecimalField(8,2) | minimum 0.01 | |
| `stock` | PositiveIntegerField | default 0 | |
| `image` | ImageField | optional, 2 MB limit | Stored under `media/products/` |
| `rating` | DecimalField(3,2) | default 0.00, read-only | Average review score, updated by signals |
| `status` | CharField(10) | choices: active, draft, archived | Only active products are visible to shoppers |
| `created`, `updated` | DateTimeField | automatic | |

Index: (`status`, `created` descending) to support the storefront listing.

### ProductReview

| Field | Type | Key / constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | **PK** | |
| `product` | ForeignKey | **FK** to Product, CASCADE | |
| `user` | ForeignKey | **FK** to User, CASCADE | |
| `rating` | PositiveSmallIntegerField | 1 to 5 | |
| `text` | TextField | 10 to 1000 characters | |
| `created`, `updated` | DateTimeField | automatic | |

Unique constraint: (`product`, `user`), so each customer has one review per product.

### UserProfile

| Field | Type | Key / constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | **PK** | |
| `user` | OneToOneField | **FK** to User, unique, CASCADE | |
| `phone` | CharField(20) | optional | |
| `address_line1`, `address_line2` | CharField(120) | optional | |
| `city` | CharField(60) | optional | |
| `postcode` | CharField(12) | optional | |
| `country` | CharField(60) | default "United Kingdom" | |
| `wishlist` | ManyToManyField | to Product | Join table `profiles_userprofile_wishlist` |
| `created`, `updated` | DateTimeField | automatic | |

### Order

| Field | Type | Key / constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | **PK** | |
| `user` | ForeignKey | **FK** to User, SET NULL | |
| `status` | CharField(12) | choices: pending, processing, shipped, delivered, cancelled | |
| `transaction_id` | CharField(32) | unique, read-only | 16-character random reference used in URLs |
| `full_name`, `email`, `phone` | CharField / EmailField | required | Copied at checkout |
| `address_line1`, `address_line2`, `city`, `postcode`, `country` | CharField | line 2 optional | Shipping address as it was when ordered |
| `subtotal` | DecimalField(10,2) | | |
| `delivery_cost` | DecimalField(6,2) | | Free at £50 or more, otherwise £4.99 |
| `total` | DecimalField(10,2) | | |
| `created`, `updated` | DateTimeField | automatic | |

### OrderItem

| Field | Type | Key / constraints | Notes |
| --- | --- | --- | --- |
| `id` | BigAutoField | **PK** | |
| `order` | ForeignKey | **FK** to Order, CASCADE | |
| `product` | ForeignKey | **FK** to Product, SET NULL, nullable | |
| `product_name` | CharField(120) | | Name at time of purchase |
| `unit_price` | DecimalField(8,2) | | Price at time of purchase |
| `quantity` | PositiveIntegerField | minimum 1 | |

### Shopping cart

The cart is not a database table. It is kept in the visitor's session as `{"<product id>": quantity}` so guests can shop before registering. Product names and prices are always read from the database when the cart is shown.

---

## 6. Security features

| Area | What is done | Where |
| --- | --- | --- |
| Secrets | `SECRET_KEY`, database URL and AWS keys are read from environment variables. `.env` is listed in `.gitignore`; only `.env.example` with placeholders is committed. The app refuses to start without a `SECRET_KEY` when `DEBUG` is off. | `joy2buy/settings.py` |
| Debug mode | `DEBUG` defaults to `False` and is only turned on by `DEBUG=True` in a local `.env`. | `joy2buy/settings.py` |
| Database configuration | One setting, `DATABASE_URL`, selects the database. Credentials never appear in code. | `joy2buy/settings.py` |
| Passwords | Stored only as salted PBKDF2 hashes by Django's auth system. Four validators enforce length (8+), reject common and all-numeric passwords, and reject passwords similar to the username or email. | `AUTH_PASSWORD_VALIDATORS` |
| CSRF | `CsrfViewMiddleware` is enabled and every `POST` form includes `{% csrf_token %}`. JavaScript requests send the same token. | Templates, `static/js/main.js` |
| Authentication | `@login_required` protects checkout, orders, account, reviews and wishlist. Logging out requires `POST`. | App `views.py` files |
| Authorisation | `@staff_required` (built on `user_passes_test`) protects all management views: anonymous users are redirected to sign in, signed-in customers receive 403. Object-level checks ensure customers can only see or cancel their own orders and delete their own reviews. | `joy2buy/decorators.py`, `orders/views.py`, `products/views.py` |
| Input validation | Server-side validation on every form; uploaded images are verified by Pillow and limited to 2 MB. | App `forms.py`, `products/validators.py` |
| SQL injection | All queries go through the Django ORM with bound parameters. No raw SQL. | - |
| Cross-site scripting | Django template auto-escaping is on everywhere. JavaScript inserts server text with `textContent`, never `innerHTML`. | Templates, `static/js/main.js` |
| Open redirects | "next" addresses are checked with `url_has_allowed_host_and_scheme`. | `cart/views.py` |
| HTTPS | With `DEBUG=False`: HTTPS redirect, secure session and CSRF cookies, HSTS, `X-Frame-Options: DENY`, `nosniff`, same-origin referrer policy. | `joy2buy/settings.py` |
| Price integrity | The session cart stores only product ids and quantities; prices are read from the database at checkout. | `cart/cart.py` |

Run Django's own production audit at any time with:

```bash
python manage.py check --deploy
```

---

## 7. Project structure

```
joy2buy/
├── manage.py
├── requirements.txt          Python dependencies
├── Procfile                  Heroku process types (release + web)
├── runtime.txt               Python version for Heroku
├── .env.example              Template for local environment variables
├── setup.cfg                 flake8 / pycodestyle settings
├── joy2buy/                  Project package
│   ├── settings.py           All configuration, driven by environment variables
│   ├── urls.py               Root URL map and error handlers
│   ├── views.py              403 / 404 / 500 handlers
│   ├── decorators.py         staff_required
│   └── forms.py              Bootstrap form mixin
├── products/                 Category, Product, ProductReview; storefront and staff CRUD
│   ├── management/commands/seed_store.py
│   └── templatetags/store_extras.py
├── cart/                     Session cart (cart.py), views, context processor
├── orders/                   Order, OrderItem; checkout and order management
├── profiles/                 UserProfile; sign up, dashboard, wishlist
├── templates/                base.html, error pages, one folder per app, includes/
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── images/
└── media/                    Uploaded images (local development only)
```

Each app keeps its own `models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py` and `tests.py`. File and folder names are lower case with no spaces.

---

## 8. Running the project locally

Requirements: Python 3.11 or newer and Git.

```bash
git clone <your-repository-url> joy2buy
cd joy2buy

python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                 # Windows: copy .env.example .env
```

Edit `.env`: set `DEBUG=True`, set `SECRET_KEY` to a random string, set `SECURE_SSL_REDIRECT=False` and leave `DATABASE_URL` empty to use SQLite.

```bash
python manage.py migrate
python manage.py seed_store          # 6 categories and 18 products
python manage.py createsuperuser     # your staff account
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Sign in with the superuser to see **Store management** in the account menu. The Django admin is at `/admin/`.

To use MySQL instead of PostgreSQL, install `mysqlclient` and set `DATABASE_URL=mysql://USER:PASSWORD@HOST:3306/DBNAME`. No code changes are needed.

---

## 9. Testing

### Automated tests

111 unit tests are split across the four apps.

| File | Tests | What is covered |
| --- | --- | --- |
| `products/tests.py` | 45 | Model creation, slugs, relationships, validators, rating signals; list, search, filter, detail and 404 pages; review create, update, delete and permissions; staff product and category CRUD |
| `cart/tests.py` | 20 | Add, update, remove; stock caps; invalid quantities; totals and delivery charge; JSON responses; open redirect protection |
| `orders/tests.py` | 27 | Order and line models, totals; checkout form validation; placing an order, stock reduction, rollback; owner / staff access; cancellation; status updates |
| `profiles/tests.py` | 19 | Profile signal; sign up, login, logout; password hashing and change; dashboard; profile update; wishlist |

```bash
python manage.py test                 # run everything
python manage.py test orders -v 2     # one app, verbose
python -m flake8                      # PEP 8 check (pip install flake8)
python manage.py makemigrations --check --dry-run   # models match migrations
```

The tests assume the default delivery settings (free at £50, otherwise £4.99).

### Validation tools

| Tool | Scope | Result |
| --- | --- | --- |
| flake8 (PEP 8) | All Python files except migrations | Not yet run |
| W3C Markup Validator | Rendered HTML of each page (validate by URL or by "view source") | Not yet run |
| W3C CSS Validator (Jigsaw) | `static/css/style.css` | Not yet run |
| `node --check` | `static/js/main.js` | Pass (no syntax errors) |
| Lighthouse (accessibility) | Home, product, cart, checkout | Not yet run |

### Manual testing matrix

Replace "Not yet run" with **Pass** or **Fail** and the date once each case has been carried out on the deployed site.

| # | Area | Test case | Expected outcome | Result |
| --- | --- | --- | --- | --- |
| 1 | Navigation | Click every link in the navbar and footer | Each opens the correct page; no 404s; external links open in a new tab | Not yet run |
| 2 | Navigation | Shrink the browser below 992px and use the menu button | Menu collapses behind a toggle and opens when pressed | Not yet run |
| 3 | Catalogue | Open the home page | Hero, category tabs and a grid of active products are shown | Not yet run |
| 4 | Catalogue | Choose a category tab | Only that category's products are listed; the tab is highlighted | Not yet run |
| 5 | Search | Type "bottle" slowly in the search box | Suggestions appear after two letters; choosing one opens the product | Not yet run |
| 6 | Search | Search for "zzzz" | "No products match your search" with a link back to all products | Not yet run |
| 7 | Catalogue | Change the sort order and tick "In stock only" | The list re-orders; out-of-stock items disappear; filters survive paging | Not yet run |
| 8 | Product | Open a product with a photo and hover over it | The image zooms and follows the pointer | Not yet run |
| 9 | Product | Open an out-of-stock product | "Out of stock" is shown and there is no add-to-cart button | Not yet run |
| 10 | Cart | Add a product from the grid | Success message appears; cart badge increases; no page reload | Not yet run |
| 11 | Cart | Enter a quantity above the stock level | Quantity is reduced to the stock available with a warning message | Not yet run |
| 12 | Cart | Type `0`, `-1` or letters as a quantity | The browser or server rejects it with a clear error; cart is unchanged | Not yet run |
| 13 | Cart | Change a quantity in the cart | Line total, subtotal, delivery and total update immediately | Not yet run |
| 14 | Cart | Press Remove on a line | A confirmation modal appears; confirming removes the line | Not yet run |
| 15 | Cart | Bring the subtotal to £50 or more | Delivery changes to "Free" | Not yet run |
| 16 | Cart | Repeat tests 10 to 14 with JavaScript disabled | Everything still works through page reloads | Not yet run |
| 17 | Auth | Register with mismatched or weak passwords | Field-level errors; no account created | Not yet run |
| 18 | Auth | Register with valid details | Account created, signed in, welcome message, dashboard shown | Not yet run |
| 19 | Auth | Sign in with a wrong password | Error shown; not signed in | Not yet run |
| 20 | Auth | Open `/orders/checkout/` while signed out | Redirected to sign in, then back to checkout; the cart is kept | Not yet run |
| 21 | Checkout | Submit with an empty phone number and invalid postcode | Errors next to those fields; no order created | Not yet run |
| 22 | Checkout | Place a valid order | Confirmation page with reference; cart empty; stock reduced | Not yet run |
| 23 | Orders | Open the dashboard | The new order is listed with status "Pending" | Not yet run |
| 24 | Orders | Cancel a pending order | Status becomes "Cancelled"; stock is restored | Not yet run |
| 25 | Orders | Paste another customer's order URL | 403 page is shown | Not yet run |
| 26 | Reviews | Submit a review with no rating | "Please choose a star rating." and nothing is saved | Not yet run |
| 27 | Reviews | Submit a valid review, then edit it | Review appears; average rating updates; editing replaces it | Not yet run |
| 28 | Reviews | Delete your own review | Confirmation modal, then the review disappears | Not yet run |
| 29 | Profile | Update name, address and postcode | Success message; checkout form is pre-filled next time | Not yet run |
| 30 | Wishlist | Save and then remove a product | Button text toggles; dashboard wishlist updates | Not yet run |
| 31 | Staff | Visit `/manage/` as a customer | 403 page is shown | Not yet run |
| 32 | Staff | Add a product with a 3 MB image | Rejected with "2 MB or smaller" | Not yet run |
| 33 | Staff | Add, edit and delete a product | Messages confirm each step; delete asks for confirmation first | Not yet run |
| 34 | Staff | Set a product to "Draft" | It disappears from the shop but remains in the management table | Not yet run |
| 35 | Staff | Change an order to "Shipped" | Badge updates; the customer can no longer cancel it | Not yet run |
| 36 | Errors | Visit `/no-such-page/` | Custom 404 page with links back to the shop | Not yet run |
| 37 | Responsive | View every page at 360px, 768px and 1280px wide | No horizontal scrolling; content reflows to 1, 2 and 4 columns | Not yet run |
| 38 | Accessibility | Tab through the home page with the keyboard only | Skip link appears first; focus is always visible; all controls reachable | Not yet run |

### Bugs found and fixed during development

| # | Bug | Cause | Fix |
| --- | --- | --- | --- |
| 1 | The site failed to start when `.env` contained an empty `DATABASE_URL=` line | An empty string was passed to the database URL parser instead of falling back to SQLite | `settings.py` now uses `os.environ.get("DATABASE_URL") or <sqlite url>` |
| 2 | Changing a cart quantity and pressing Enter sent two requests and showed two messages | The browser fires both `change` and `submit` | `main.js` ignores a submission while one for the same form is in flight |
| 3 | After a rejected profile edit, the navbar showed the rejected first name | The form was bound to `request.user`, so invalid input was copied onto the object the template reads | `profile_edit` binds the form to a separate copy of the user |
| 4 | `HEAD` requests (used by uptime checkers) returned 405 on read-only pages | Views used `require_GET` | Replaced with `require_safe`, which allows `GET` and `HEAD` |
| 5 | Every anonymous page view created a session row | The cart wrote an empty dictionary to the session on first access | `Cart` only writes to the session when its contents change |
| 6 | The star-rating tag raised an error on wishlist cards | The review count is not available there and an empty value was converted to a number | The tag treats a missing count as "unknown" |

### Known limitations

- Payment is simulated; integrating a provider such as Stripe is the natural next step.
- No emails are sent (order confirmation, password reset).
- Bootstrap and the web fonts are loaded from public CDNs without Subresource Integrity hashes.

---

## 10. Deployment

The steps below deploy to [Heroku](https://www.heroku.com/) with a PostgreSQL database. Any platform that runs a `Procfile` (Render, Railway, Fly.io) follows the same pattern: set the environment variables, run migrations, collect static files, start gunicorn.

### Files that make the project deployable

| File | Purpose |
| --- | --- |
| `requirements.txt` | Packages installed at build time |
| `runtime.txt` | Python version (`python-3.12`). Heroku now also accepts a `.python-version` file containing `3.12`; use whichever the platform asks for, not both. |
| `Procfile` | `release:` runs migrations on every deploy; `web:` starts gunicorn |
| `joy2buy/settings.py` | Reads all configuration from config vars; WhiteNoise serves static files |

### Step by step

1. **Push the code to GitHub.**

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/joy2buy.git
   git push -u origin main
   ```

   Check that `.env` and `db.sqlite3` are **not** in the repository.

2. **Create the Heroku app and database.**

   ```bash
   heroku login
   heroku create your-app-name
   heroku addons:create heroku-postgresql:essential-0
   ```

   The add-on sets the `DATABASE_URL` config var automatically.

3. **Set the config vars** (Settings > Reveal Config Vars, or the CLI).

   ```bash
   heroku config:set SECRET_KEY="<a long random string>"
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
   heroku config:set CSRF_TRUSTED_ORIGINS=https://your-app-name.herokuapp.com
   heroku config:set DATABASE_SSL_REQUIRE=True
   ```

   Use the exact host name Heroku shows for your app; newer apps have a random suffix.

   | Variable | Required | Example |
   | --- | --- | --- |
   | `SECRET_KEY` | Yes | 50+ random characters |
   | `DEBUG` | Yes | `False` |
   | `ALLOWED_HOSTS` | Yes | `your-app-name.herokuapp.com` |
   | `CSRF_TRUSTED_ORIGINS` | Yes | `https://your-app-name.herokuapp.com` |
   | `DATABASE_URL` | Set by the add-on | `postgres://...` |
   | `DATABASE_SSL_REQUIRE` | Recommended | `True` |
   | `USE_AWS` and `AWS_*` | Only for product photo uploads | See below |

4. **Deploy.**

   ```bash
   git push heroku main
   ```

   During the build Heroku installs the requirements and runs `python manage.py collectstatic --noinput` itself. The `release` line in the `Procfile` then runs `python manage.py migrate`.

5. **Run the one-off commands.**

   ```bash
   heroku run python manage.py migrate          # only if the release phase was skipped
   heroku run python manage.py collectstatic --noinput   # only if DISABLE_COLLECTSTATIC was set
   heroku run python manage.py seed_store
   heroku run python manage.py createsuperuser
   ```

6. **Check the live site.**

   ```bash
   heroku open
   heroku logs --tail
   heroku run python manage.py check --deploy
   ```

### Uploaded images in production

Heroku's file system is temporary: files uploaded through the product form disappear when the app restarts. To keep product photos, create an Amazon S3 bucket with public read access for objects and set:

```bash
heroku config:set USE_AWS=True AWS_STORAGE_BUCKET_NAME=<bucket> AWS_S3_REGION_NAME=eu-west-2
heroku config:set AWS_ACCESS_KEY_ID=<key> AWS_SECRET_ACCESS_KEY=<secret>
```

Without S3 the store still works: products without a photo show a coloured tile with their initials.

---

## 11. Attribution and code ownership

### Project code

Everything in the following locations was written for this project and is not copied from a tutorial or template:

- `joy2buy/`, `products/`, `cart/`, `orders/`, `profiles/` (models, forms, views, URLs, admin, tests, template tags, management command)
- `templates/` (all HTML templates)
- `static/css/style.css`, `static/js/main.js`, `static/images/favicon.svg`
- This `README.md`, including wireframes and schema tables
- Product names, descriptions and specifications in `seed_store.py` are original, fictional catalogue entries written for this project. No third-party product photos are included.

**Development tools.** An AI assistant (Claude, by Anthropic) was used to help write and review the code and documentation. All of it was read, run and tested by the developer, who is responsible for the submitted work.

### External libraries and frameworks

These are used unmodified and are not the developer's own work.

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

### Patterns adapted from documentation

- The session-based cart follows the general approach described in the Django documentation on [sessions](https://docs.djangoproject.com/en/5.2/topics/http/sessions/); the implementation in `cart/cart.py` is original.
- Production settings follow the Django [deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) and the WhiteNoise documentation.
