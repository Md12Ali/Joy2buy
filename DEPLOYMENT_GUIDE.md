# JOY2BUY deployment guide

How to deploy JOY2BUY to [Heroku](https://www.heroku.com/) with PostgreSQL, keep uploaded images, and confirm that the deployment matches the live site at <https://joy2buy-shop-218caf987cba.herokuapp.com/>.

Any platform that runs a `Procfile` (Render, Railway, Fly.io) follows the same pattern: set the environment variables, run migrations, collect static files, start gunicorn.

## 1. Files that make the project deployable

| File | Purpose |
| --- | --- |
| `requirements.txt` | Packages installed at build time (Django 5.2, gunicorn, psycopg2, WhiteNoise, dj-database-url, Pillow, python-dotenv, django-storages) |
| `runtime.txt` | Python version: `python-3.12` |
| `Procfile` | `release: python manage.py migrate --noinput` runs on every deploy; `web: gunicorn joy2buy.wsgi` serves the site |
| `joy2buy/settings.py` | Reads all configuration from environment variables; WhiteNoise serves compressed static files |
| `.env.example` | Lists every variable; copy to `.env` for local use only |

## 2. Prerequisites

- A Heroku account and the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) (`heroku --version`).
- Git, with this repository cloned: `git clone https://github.com/Md12Ali/Joy2buy.git`.
- Check that `.env` and `db.sqlite3` are **not** tracked: `git ls-files | grep -E '^\.env$|sqlite3'` must print nothing.

## 3. Create the app and database

```bash
heroku login
heroku create <app-name>                                   # e.g. joy2buy-shop
heroku addons:create heroku-postgresql:essential-0 --app <app-name>
```

The add-on sets `DATABASE_URL` automatically. (The old `hobby-dev` plan no longer exists.) Heroku shows the app's host name, for example `joy2buy-shop-218caf987cba.herokuapp.com`; newer apps have a random suffix, so copy it exactly.

## 4. Set the config vars

```bash
APP=<app-name>
HOST=<app-host>                                            # e.g. joy2buy-shop-218caf987cba.herokuapp.com

heroku config:set --app $APP \
    SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key as k; print(k())')" \
    DEBUG=False \
    ALLOWED_HOSTS=$HOST \
    CSRF_TRUSTED_ORIGINS=https://$HOST \
    DATABASE_SSL_REQUIRE=True
```

| Variable | Required | Value |
| --- | --- | --- |
| `SECRET_KEY` | Yes | 50+ random characters, generated as above; never reuse the local one |
| `DEBUG` | Yes | `False` |
| `ALLOWED_HOSTS` | Yes | The exact app host (comma-separate several, e.g. a custom domain) |
| `CSRF_TRUSTED_ORIGINS` | Yes | `https://` plus each host |
| `DATABASE_URL` | Set by the add-on | `postgres://...` |
| `DATABASE_SSL_REQUIRE` | Recommended | `True` |
| `SECURE_SSL_REDIRECT` | No | Leave **unset** in production (defaults to `True`) |
| `USE_AWS`, `AWS_*` | For persistent uploads | See section 6 |
| `FREE_DELIVERY_THRESHOLD`, `STANDARD_DELIVERY_COST` | No | Defaults `50.00` and `4.99` |

### Production HTTPS settings

With `DEBUG=False` and `SECURE_SSL_REDIRECT` left unset, `joy2buy/settings.py` turns on:

| Setting | Value | Effect |
| --- | --- | --- |
| `SECURE_PROXY_SSL_HEADER` | `("HTTP_X_FORWARDED_PROTO", "https")` | Trusts Heroku's router to say a request arrived over HTTPS (without it the redirect would loop) |
| `SECURE_SSL_REDIRECT` | `True` | Every `http://` request is redirected to `https://` |
| `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` | `True` | Cookies are never sent over plain HTTP |
| `SECURE_HSTS_SECONDS` | 2,592,000 (30 days) | Browsers refuse plain HTTP for this site for 30 days |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` | |
| `X_FRAME_OPTIONS` | `DENY` | No framing (clickjacking protection) |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True` | |
| `SECURE_REFERRER_POLICY` | `same-origin` | |

`SECURE_HSTS_PRELOAD` is deliberately left off: a `*.herokuapp.com` subdomain cannot be submitted to the browser preload list, so `check --deploy` reports warning W021 and nothing else (see [TESTING.md](TESTING.md#6-production-settings)).

## 5. Deploy

```bash
git push heroku main
```

During the build Heroku installs `requirements.txt` and runs `python manage.py collectstatic --noinput` automatically. The `release` line of the `Procfile` then runs the migrations before the new version starts. Then load the catalogue and create the staff account:

```bash
heroku run python manage.py seed_store --app $APP          # 6 categories, 18 products; safe to re-run
heroku run python manage.py createsuperuser --app $APP
heroku open --app $APP
```

`seed_store` creates no users, reviews or orders. Use a strong, unique password for the superuser and do not write it in the repository.

## 6. Persistent image storage (Amazon S3)

Heroku dynos have an ephemeral file system: images uploaded through the product or category forms are lost on the next restart or deploy. To keep them:

1. **Create a bucket** in the AWS console (S3 > Create bucket), e.g. `joy2buy-media`, region `eu-west-2`. Under *Block public access*, untick "Block public access granted through new public bucket or access point policies" (and the matching "any public bucket policies" option) so the bucket policy below can allow public reads.
2. **Allow public reads of images** (Permissions > Bucket policy):

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Sid": "PublicReadMedia",
       "Effect": "Allow",
       "Principal": "*",
       "Action": "s3:GetObject",
       "Resource": "arn:aws:s3:::joy2buy-media/*"
     }]
   }
   ```

3. **Create an IAM user** for the app (IAM > Users), with no console access, and attach a policy that only allows this bucket:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {"Effect": "Allow", "Action": ["s3:ListBucket"], "Resource": "arn:aws:s3:::joy2buy-media"},
       {"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"], "Resource": "arn:aws:s3:::joy2buy-media/*"}
     ]
   }
   ```

   Create an access key for that user.
4. **Set the config vars** (never commit the keys):

   ```bash
   heroku config:set --app $APP USE_AWS=True AWS_STORAGE_BUCKET_NAME=joy2buy-media AWS_S3_REGION_NAME=eu-west-2
   heroku config:set --app $APP AWS_ACCESS_KEY_ID=<key id> AWS_SECRET_ACCESS_KEY=<secret>
   ```

With `USE_AWS=True`, uploads are stored by `storages.backends.s3.S3Storage` (file names are never overwritten) and served from `https://<bucket>.s3.<region>.amazonaws.com/`. Static files (CSS, JS) are still served by WhiteNoise. To test: upload a product photo, run `heroku restart --app $APP`, and confirm the photo still loads.

Without S3 the store still works: products without a photo show a coloured tile with their initials.

## 7. Confirming the deployment matches this repository

Run these after every deploy. Record the outputs in [TESTING.md](TESTING.md#8-deployment-verification).

1. **The live code is this commit.**

   ```bash
   git rev-parse --short HEAD
   heroku releases --app $APP -n 3        # the latest "Deploy" entry shows the same short hash
   ```

2. **The config vars are set** (prints names only, not values):

   ```bash
   heroku config --app $APP --json | python -c "import json,sys; print(sorted(json.load(sys.stdin)))"
   ```

   Expect at least `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_SSL_REQUIRE`, `DATABASE_URL`, `DEBUG`, `SECRET_KEY`, and `USE_AWS` plus the `AWS_*` names if S3 is used. `SECURE_SSL_REDIRECT` should be absent.

3. **Django's production audit passes:**

   ```bash
   heroku run python manage.py check --deploy --app $APP
   ```

   Expected: only W021 (HSTS preload, deliberately off).

4. **Migrations are applied:** `heroku run python manage.py showmigrations --app $APP` shows `[X]` everywhere.

5. **End-to-end check with controlled test records.** Create two dedicated QA accounts on the live site: a customer (register normally) and a staff user (`heroku run python manage.py createsuperuser`, or tick *Staff status* in `/admin/`). Then, from your own computer:

   ```bash
   export JOY2BUY_STAFF_USER=<qa staff username>   JOY2BUY_STAFF_PASSWORD=<password>
   export JOY2BUY_CUSTOMER_USER=<qa customer username> JOY2BUY_CUSTOMER_PASSWORD=<password>
   python tools/deployment_check.py --base-url https://$HOST/
   ```

   The script creates, edits and deletes a "QA test" category and draft product, checking that each step shows its success message immediately and is still there in a fresh session. It runs a customer cart flow and checks the HTTPS redirect, HSTS, security headers, Secure cookies and the custom 404 page. It deletes everything it created. It exits with status 1 if anything fails.

6. **Validation and accessibility on the live site:**

   ```bash
   python tools/validate_site.py --base-url https://$HOST/
   npm pack axe-core@4.10.2 && tar xzf axe-core-4.10.2.tgz
   pip install playwright==1.56.0 && playwright install chromium
   python tools/browser_checks.py --base-url https://$HOST/ --axe package/axe.min.js
   ```

Afterwards, delete or deactivate the QA accounts in `/admin/` if they are no longer needed.

## 8. Troubleshooting

| Symptom | Check |
| --- | --- |
| "Application error" | `heroku logs --tail --app $APP`. `ImproperlyConfigured: The SECRET_KEY environment variable must be set` means step 4 was skipped. |
| 400 Bad Request | The host is missing from `ALLOWED_HOSTS`. |
| 403 "CSRF verification failed" on forms | `CSRF_TRUSTED_ORIGINS` must be `https://` plus the exact host. |
| Redirect loop | `SECURE_PROXY_SSL_HEADER` is set automatically when `DEBUG=False`; make sure `DEBUG` is really `False`. |
| Unstyled pages | Look for the `collectstatic` step in the build log; it must not be disabled with `DISABLE_COLLECTSTATIC`. |
| Uploaded images disappear | Configure S3 (section 6). |
| Admin login fails | Create the superuser on Heroku (step 5); local accounts are in a different database. |
| Database errors after a deploy | `heroku run python manage.py migrate --app $APP` (normally done by the release phase). |
