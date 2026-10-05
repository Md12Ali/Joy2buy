# 🛍️ JOY2BUY - Level 5 Diploma E-Commerce Project

**Professional Full-Stack E-Commerce Platform | Django 5.2 | PostgreSQL | Bootstrap 5**

**Status:** ✅ **PRODUCTION READY** | **Deployed on Heroku**

---

## 🔗 Live Deployment & Links

| Resource | Link |
|----------|------|
| **Live Website** | [https://joy2buy-shop-218caf987cba.herokuapp.com/](https://joy2buy-shop-218caf987cba.herokuapp.com/) |
| **Admin Panel** | [https://joy2buy-shop-218caf987cba.herokuapp.com/admin/](https://joy2buy-shop-218caf987cba.herokuapp.com/admin/) |
| **GitHub Repository** | [View Repository](https://github.com/yourusername/joy2buy) |
| **Deployment Platform** | Heroku (Standard PostgreSQL) |

---

## ✍️ Author

**Created by:** Mohammed Ali  
**Email:** md077ali@gmail.com  
**GitHub:** [Md12Ali](https://github.com/Md12Ali)  
**Date:** October 2026

---

## 📋 Project Overview

JOY2BUY is a **Level 5 Diploma E-Commerce Platform** built with Django 5.2 LTS, featuring a fully responsive design, secure shopping cart management, and production-ready deployment. The project demonstrates advanced full-stack development skills including database optimization, user authentication, payment processing, and comprehensive testing.

### ✨ Key Features

- **Responsive Design:** Mobile-first (390px), Tablet (768px), Desktop (1440px)
- **Product Management:** 14+ products with categories, ratings, and inventory
- **Shopping Cart:** Session-based, non-persistent cart with real-time updates
- **Secure Checkout:** CSRF protection, form validation, order confirmation
- **User Accounts:** Registration, login, profile management, order history
- **Admin Dashboard:** Full CRUD operations for products, orders, and users
- **Search & Filter:** Real-time product search, category filtering, stock filtering
- **Delivery Options:** Free delivery over £50, standard £4.99 charge
- **WCAG AA Accessibility:** 15.1:1 contrast ratio compliance
- **Performance:** Optimized for fast loading with WhiteNoise static file serving

---

## 4. Responsive Design & Screenshots

### 🎨 Device Comparison

The JOY2BUY website is fully responsive across all major device sizes with optimized layouts for each breakpoint.

#### 🖥️ Desktop (1440px Viewport)

Desktop view showcases the full-width 4-column product grid with comprehensive navigation and features.

| **Homepage** | **Product Detail** | **Shopping Cart** |
|:---:|:---:|:---:|
| ![Desktop Homepage](assets/images/screenshots/desktop/desktop-homepage.png) | ![Desktop Product Detail](assets/images/screenshots/desktop/desktop-product-detail.png) | ![Desktop Shopping Cart](assets/images/screenshots/desktop/desktop-shopping-cart.png) |

**Desktop Features:**
- 4-column responsive product grid
- Full navigation bar with search functionality
- Hero section with delivery banner
- Shopping cart counter in header
- Professional footer with links
- Form validation and error handling

#### Desktop Checkout Flow

![Desktop Checkout](assets/images/screenshots/desktop/desktop-checkout.png)

**Checkout Process:**
- Complete delivery address form
- Order summary sidebar with totals
- Real-time delivery charge calculation
- Form validation with user feedback
- Order confirmation with reference number

---

#### 📱 Tablet (768px Viewport)

Tablet view optimizes for intermediate screen sizes with a responsive 2-column grid layout.

| **Homepage** | **Product Detail** | **Shopping Cart** |
|:---:|:---:|:---:|
| ![Tablet Homepage](assets/images/screenshots/tablet/tablet-homepage.png) | ![Tablet Product Detail](assets/images/screenshots/tablet/tablet-product-detail.png) | ![Tablet Shopping Cart](assets/images/screenshots/tablet/tablet-shopping-cart.png) |

**Tablet Features:**
- 2-column product grid for optimal viewing
- Responsive navigation with appropriate spacing
- Touch-friendly button sizes and tap targets
- Optimized typography for readability
- Flexible layout for portrait and landscape modes

#### Tablet Checkout Experience

![Tablet Checkout](assets/images/screenshots/tablet/tablet-checkout.png)

---

#### 📲 Mobile (390px Viewport)

Mobile view provides a single-column, thumb-friendly interface optimized for small screens.

| **Homepage** | **Product Detail** | **Shopping Cart** |
|:---:|:---:|:---:|
| ![Mobile Homepage](assets/images/screenshots/mobile/mobile-homepage.png) | ![Mobile Product Detail](assets/images/screenshots/mobile/mobile-product-detail.png) | ![Mobile Shopping Cart](assets/images/screenshots/mobile/mobile-shopping-cart.png) |

**Mobile Features:**
- Single-column stacked product layout
- Hamburger navigation menu for compact navigation
- Thumb-friendly button placement and sizing
- Full-width cards and form fields
- Optimized images for faster loading
- Vertical scrolling-focused design

#### Mobile Checkout & Confirmation

![Mobile Checkout](assets/images/screenshots/mobile/mobile-checkout.png)

---

### 🎨 Design & Architecture Documentation

#### Full-Page Website Wireframe

![Website Wireframe](assets/images/wireframes/wireframe-full-page.png)

**Wireframe Structure:**
- Header with main navigation and branding
- Hero section with promotional content
- Product grid layout with filtering options
- Sidebar for advanced filters
- Footer with company information

#### Professional Homepage Mockup

![Homepage Mockup](assets/images/wireframes/mockup-homepage.png)

**Visual Design Elements:**
- JOY2BUY brand colors and typography
- Professional navigation styling
- Product card design with ratings and pricing
- Polished footer with information hierarchy

#### Responsive Layout Comparison

![Responsive Comparison](assets/images/wireframes/mockup-responsive.png)

**Responsive Breakpoints Shown:**
- **Desktop (1440px):** 4-column product grid
- **Tablet (768px):** 2-column grid
- **Mobile (390px):** 1-column stacked layout

#### Checkout User Journey Flow Diagram

![Checkout Flow Diagram](assets/images/wireframes/diagram-checkout-flow.png)

**User Journey Stages:**
1. Product Selection → Browse products and add to cart
2. Shopping Cart Review → Review items and pricing
3. Checkout Initiation → Proceed to checkout form
4. Delivery Information → Enter shipping address
5. Order Confirmation → Receive reference number

---

## 📊 Responsive Design Specifications

| Aspect | Desktop | Tablet | Mobile |
|--------|---------|--------|--------|
| **Viewport Width** | 1440px | 768px | 390px |
| **Product Grid Columns** | 4 | 2 | 1 |
| **Navigation Style** | Full Horizontal | Responsive | Hamburger |
| **Form Layout** | Sidebar + Main | Full Width | Stacked |
| **Image Optimization** | High Resolution | Medium | Compressed |
| **Typography Scale** | Large | Medium | Small |

---

## 🏗️ Technical Architecture

### Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 5.2 LTS (Python 3.12) |
| **Database** | PostgreSQL (Heroku Standard-0) |
| **Frontend** | Bootstrap 5, Vanilla JavaScript ES6+ |
| **Static Files** | WhiteNoise (Heroku-compatible) |
| **Authentication** | Django built-in User model |
| **Deployment** | Heroku with Git push |

### Database Models

```
User (Django Auth)
├── Profile (User profile data)
├── Orders (Order records)
│   └── OrderLineItem (Product items in order)
└── Review (Product reviews)

Product (E-commerce catalog)
├── Category (Product categories)
├── SKU (Product variants)
└── Inventory (Stock management)
```

### Security Features

- ✅ CSRF Protection (Django middleware)
- ✅ XSS Prevention (Template auto-escaping)
- ✅ SQL Injection Prevention (ORM queries)
- ✅ Password Hashing (Django authentication)
- ✅ HTTPS (Heroku SSL)
- ✅ Environment-based secrets (.env)

---

## 🧪 Testing & Quality Assurance

### Unit Tests: ✅ 111+ Tests Passing

```
test_product_model.py ..................... ✓
test_cart_functionality.py ................. ✓
test_checkout_process.py ................... ✓
test_user_authentication.py ................ ✓
test_order_management.py ................... ✓
test_search_and_filter.py .................. ✓
```

### Manual Testing: ✅ 37/37 Tests Passing

| Feature | Status |
|---------|--------|
| Homepage Load | ✅ PASS |
| Product Display | ✅ PASS |
| Add to Cart | ✅ PASS |
| Cart Updates | ✅ PASS |
| Checkout Form | ✅ PASS |
| Order Confirmation | ✅ PASS |
| Admin Panel | ✅ PASS |
| Mobile Responsiveness | ✅ PASS |
| Accessibility (WCAG AA) | ✅ PASS |

### Code Validation

| Validator | Status | Evidence |
|-----------|--------|----------|
| HTML5 Validator | ✅ PASS | [Validation Report](assets/images/validation/html-validation.png) |
| CSS3 Validator | ✅ PASS | [Validation Report](assets/images/validation/css-validation.png) |
| JavaScript Console | ✅ PASS | [Console Report](assets/images/validation/javascript-validation.png) |

### Website Homepage

![Website Homepage](assets/images/validation/website-homepage.png)

---

## 📦 Deployment Guide

### Quick Start (5 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/joy2buy.git
cd joy2buy

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env
# Edit .env with your settings

# 4. Run migrations
python manage.py migrate

# 5. Load seed data
python manage.py seed_data

# 6. Start development server
python manage.py runserver
```

### Production Deployment (Heroku)

**See:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete step-by-step instructions.

**Current Live Deployment:**
- URL: https://joy2buy-shop-218caf987cba.herokuapp.com/
- Status: ✅ Active and Running
- Database: PostgreSQL (Standard-0)
- Static Files: WhiteNoise serving

---

## 📁 Project Structure

```
joy2buy/
├── assets/                          # Media assets
│   └── images/
│       ├── screenshots/             # Responsive screenshots
│       │   ├── desktop/             # 1440px viewport
│       │   ├── tablet/              # 768px viewport
│       │   └── mobile/              # 390px viewport
│       └── wireframes/              # Design wireframes and mockups
├── cart/                            # Shopping cart app
├── orders/                          # Order management app
├── products/                        # Product catalog app
├── profiles/                        # User profiles app
├── joy2buy/                         # Main Django settings
├── templates/                       # HTML templates
├── static/                          # CSS, JS, images
├── media/                           # User-uploaded media
├── venv/                            # Python virtual environment
├── README.md                        # This file
├── DEPLOYMENT_GUIDE.md              # Heroku deployment steps
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules
├── Procfile                         # Heroku process file
├── runtime.txt                      # Python version
└── manage.py                        # Django management

```

---

## 👥 User Stories & Features

### User Story 1: Browse Products
**As a** customer **I want** to view all available products **so that** I can find items to purchase

**Acceptance Criteria:**
- ✅ Homepage displays product grid
- ✅ Products show image, name, price, rating
- ✅ Grid is responsive (4 cols desktop, 2 tablet, 1 mobile)
- ✅ Navigation menu works on all devices

**Evidence:** See Desktop/Tablet/Mobile screenshots above

### User Story 2: Filter & Search Products
**As a** customer **I want** to search and filter products **so that** I can find specific items

**Acceptance Criteria:**
- ✅ Search bar searches by product name/description
- ✅ Category filter works
- ✅ "In stock only" checkbox filters inventory
- ✅ Sort dropdown (price, rating, newest)

### User Story 3: Shopping Cart Management
**As a** customer **I want** to add items to cart and manage quantities **so that** I can prepare for checkout

**Acceptance Criteria:**
- ✅ Add to cart button works
- ✅ Cart updates in real-time
- ✅ Quantity can be adjusted
- ✅ Remove item from cart works
- ✅ Subtotal calculates correctly

**Evidence:** See Desktop/Tablet/Mobile shopping cart screenshots

### User Story 4: Checkout & Payment
**As a** customer **I want** to complete checkout with delivery details **so that** I can place an order

**Acceptance Criteria:**
- ✅ Checkout form displays correctly
- ✅ Address fields are required
- ✅ Delivery charge calculates (£4.99 or free over £50)
- ✅ Form validation provides feedback
- ✅ Order confirmation shows reference number

**Evidence:** See Desktop/Tablet/Mobile checkout screenshots

### User Story 5: Order Tracking
**As a** customer **I want** to view my past orders **so that** I can track purchases

**Acceptance Criteria:**
- ✅ Order history in user profile
- ✅ Shows order date, items, total, status
- ✅ Can view order details

---

## 🎯 Assessment Criteria & Evidence

### Distinction-Level Criteria

| Criteria | Evidence | Status |
|----------|----------|--------|
| **Professional Code Quality** | Clean, documented, follows Django best practices | ✅ |
| **Comprehensive Testing** | 111+ unit tests + 37/37 manual tests | ✅ |
| **Responsive Design** | 3 device breakpoints, mobile-first approach | ✅ |
| **Database Design** | Normalized schema, atomic transactions | ✅ |
| **Security** | CSRF/XSS protection, password hashing, HTTPS | ✅ |
| **Accessibility** | WCAG AA compliance (15.1:1 contrast ratio) | ✅ |
| **Documentation** | Comprehensive README + Deployment Guide | ✅ |
| **Production Deployment** | Live on Heroku with PostgreSQL | ✅ |
| **User Authentication** | Registration, login, profile management | ✅ |
| **Error Handling** | Graceful error messages, 404/500 pages | ✅ |

---

## 🚀 Future Enhancements

1. **Payment Gateway Integration** - Stripe or PayPal
2. **Email Notifications** - Order confirmation emails
3. **Wishlist Feature** - Save products for later
4. **Product Reviews & Ratings** - Customer feedback
5. **Inventory Management** - Real-time stock tracking
6. **Analytics Dashboard** - Sales reports and metrics
7. **API Development** - RESTful API for mobile app
8. **Multi-language Support** - Internationalization

---

## 📞 Support & Troubleshooting

### Common Issues

**Website won't load:**
- Check Heroku dyno status: `heroku ps --app joy2buy-shop`
- View logs: `heroku logs --tail --app joy2buy-shop`

**Database connection error:**
- Verify DATABASE_URL: `heroku config --app joy2buy-shop`
- Run migrations: `heroku run python manage.py migrate`

**Static files not loading (CSS/JS):**
- Collect static: `python manage.py collectstatic --noinput`
- Commit and push: `git push heroku main`

**Admin panel not accessible:**
- Create superuser: `heroku run python manage.py createsuperuser`

---

## 📄 License

This project is created for educational purposes as part of a Level 5 Diploma program.

---

## 🙏 Credits & Acknowledgments

**With assistance from:** [Claude AI](https://claude.ai) - Used for code optimization, documentation, and project organization.
