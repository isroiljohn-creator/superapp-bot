# Hirely Links

Contact landing, click tracking, analytics and ads admin for Hirely job posts.
A Telegram post's **"Bog'lanish"** button opens `https://<domain>/j/<slug>` (currently `hrly.uz`); the visitor already saw the vacancy
in the post, so the page only offers the employer's contact methods and one ad. Every meaningful action is
recorded server-side, then the visitor is redirected.

Stack (matches the rest of the repo): Python 3.12, FastAPI, SQLAlchemy 2 (async) + asyncpg, Alembic, Postgres, Redis.
Frontend is server-rendered Jinja2 + ~4 KB of vanilla JS — no bundler, no runtime dependency, first paint needs
two CSS files and two subsetted woff2 fonts (≈70 KB total).

```
Telegram bot ──POST /api/jobs──▶  hirely-links ──▶ Postgres (schema "hirely")
Telegram post ──button──▶ /j/K7X92P ──▶ /r/K7X92P/phone|telegram|external ──302──▶ tel: / t.me / job URL
                                   └──▶ /t/i (ad seen) ,  /a/<token> (ad click) ──302──▶ advertiser
Admin  ──▶ /admin  (dashboard, jobs, ads, channels, admins)
```

## Data model (schema `hirely`)

| Table | Purpose |
|---|---|
| `channels` | Where jobs are published (`code`, `prefix`, `market`, `platform`). Add Hirely Freelance or more Telegram channels in **Admin → Kanallar** — no code change. |
| `jobs` | A vacancy: label, category, source, contacts (`phone` / `telegram` / `external_url`). Public id `JOB-XXXXXXXX` (random). |
| `distributions` | One publication of a job in one channel. Owns the public `slug` (`/j/K7X92P`) and code (`UZ-A7K2M9`). A job can have many. Also holds the idempotency key. |
| `visitors`, `sessions` | Anonymous cookie identities. No IP, no fingerprint, nothing personal is stored. |
| `events` | Append-only log of `page_view`, `unique_visitor`, `session_start`, `phone_click`, `telegram_click`, `external_job_click`, `ad_impression`, `ad_click`. Dimensions (job, distribution, channel, ad, campaign, visitor, session, category, source, referrer, device, browser, OS, time) are denormalised, so any group-by is one table scan. |
| `advertisers`, `ad_campaigns`, `ad_targets`, `ad_creatives` | Ads: campaign (period, limits, status), targeting rows (channel / category / market; none = all traffic), creatives (banner, title, text, CTA, URL, weight). |
| `ad_impressions`, `ad_clicks` | Ad fact tables; impressions are unique per one-time nonce. |
| `admins` | Panel users (bcrypt). |

Scale notes: `events` has a BRIN index on `occurred_at` plus covering btrees for the dashboard's access paths.
When it reaches hundreds of millions of rows, partition it by month (`PARTITION BY RANGE (occurred_at)`) and/or
add a daily roll-up table; the queries in `app/analytics.py` are the only readers.

## Bot API

Authenticate with `Authorization: Bearer <token>` (tokens = `HIRELY_BOT_API_TOKENS`, comma-separated for rotation).
From the bot container use the internal URL: `http://hirely-links:8081`.

```bash
curl -X POST http://hirely-links:8081/api/jobs \
  -H "Authorization: Bearer $HIRELY_BOT_TOKEN" \
  -H "Idempotency-Key: tgpost-<your-vacancy-id>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Backend developer","phone":"+998901234567","telegram":"@hr_person",
       "external_url":"https://example.com/apply","channel":"hirely_uz","category":"it","source":"bot"}'
# 201 {"job_id":"JOB-…","distribution_id":"UZ-…","public_url":"https://hrly.uz/j/K7X92P","idempotent_replay":false}
```

* `title` **or** `internal_reference` is required; at least one of `phone`, `telegram`, `external_url`.
  Phones are normalised to `+998…`, Telegram to a bare username, URLs must be public `http(s)`.
* `channel` is a channel **code** (`hirely_uz`).
* **Idempotency**: send `Idempotency-Key` (8–100 chars). A replay returns `200` with the same ids and
  `idempotent_replay:true`; the same key with a different body returns `409`. Without the header, an identical
  payload sent within the same UTC day is collapsed into one distribution.
* `POST /api/jobs/{job_id}/distributions` `{"channel":"…"}` publishes an existing job to another channel with its own link and stats.
* Rate limit: 600 req/min per token. Put `public_url` into the post's inline button.

Python (httpx) sketch for the existing bot:

```python
async def tracking_url(vacancy) -> str:
    async with httpx.AsyncClient(base_url=os.environ["HIRELY_LINKS_URL"], timeout=5) as c:
        r = await c.post("/api/jobs", headers={"Authorization": f"Bearer {os.environ['HIRELY_LINKS_TOKEN']}",
                                               "Idempotency-Key": f"vac-{vacancy.id}"},
                         json={...})
        r.raise_for_status()
        return r.json()["public_url"]
```

## Tracking semantics

* `page_view`: a real browser GET of `/j/<slug>`. Link-preview bots (TelegramBot, WhatsApp, crawlers, curl…) get the page
  but are never counted and never receive cookies.
* `unique_visitor` / `session_start` are derived by the writer from what the database has actually seen, so reloading a
  page 10 times is 10 page views and **one** visitor. Identity = random `hv` cookie (400 days) and `hs` session cookie (30 min sliding).
* Contact buttons are `<a href="/r/<slug>/phone|telegram|external">`. The handler puts the event on an in-memory queue
  and answers `302` immediately; a background writer batches inserts. Tracking can never block or break the redirect
  (if the queue is full the event is dropped and counted in `/healthz`; if Postgres is down the writer retries).
  Over the per-IP limit (60/min) the user is still redirected, the click just isn't recorded.
* **Ad impression** is *not* "page loaded". `landing.js` reports it only after ≥50 % of the ad has been visible for one
  continuous second in a visible tab; the server additionally checks the signed token (HMAC, 24 h), that the token is ≥1 s old,
  and de-duplicates by one-time nonce. Ad click = `/a/<token>` (recorded, then `302` to the advertiser).
* Ad selection: active campaign, inside its period, under impression/click limits, matching targeting (channel / market /
  category, none = everyone); several eligible creatives rotate least-served-first weighted by `weight`.
* Timezone of "today / yesterday / 7 d / 30 d" and chart buckets: `HIRELY_DISPLAY_TZ` (Asia/Tashkent).

## Admin

`/admin` — email + password (bcrypt), signed HttpOnly session cookie, CSRF token on every POST, same-origin check,
login rate limit (20/15 min per IP, 8/15 min per email).

* **Bosh sahifa**: Bugun / Kecha / 7 kun / 30 kun / Oraliq / Butun davr, all KPIs with the change vs the previous period,
  time-series chart, and a breakdown by channel, job, category, job source, traffic source, device, browser, OS, campaign or ad; filters for channel, device, category, source.
* **Vakansiyalar**: every job with its own stats and conversion; detail page with per-distribution links (copy button), chart and breakdowns.
* **Reklamalar**: create / edit / pause / activate / archive / delete (campaigns with statistics are archived instead of deleted),
  banner upload (validated by decoding, re-encoded to WebP 1200 px + 600 px), period, impression & click limits, targeting, per-creative stats
  (impressions, unique impressions, clicks, unique clicks, CTR).
* **Kanallar**, **Adminlar** (invite admins, change password).

First admin: set `HIRELY_BOOTSTRAP_ADMIN_EMAIL` / `HIRELY_BOOTSTRAP_ADMIN_PASSWORD` (used only while the table is empty),
or `docker exec -it hirely-links python -m app.cli create-admin you@example.com`.

## Configuration

See `.env.example`. Required: `HIRELY_DATABASE_URL`, `HIRELY_SECRET_KEY`, `HIRELY_BOT_API_TOKENS`. Nothing secret lives in the repo;
in production they are GitHub Actions secrets (`HIRELY_SECRET_KEY`, `HIRELY_BOT_API_TOKENS`, `HIRELY_ADMIN_EMAIL`, `HIRELY_ADMIN_PASSWORD`)
that `deploy.yml` passes to `docker-compose up`.

## Deploy

`docker-compose.yml` service `hirely-links` (port `127.0.0.1:8081`, volume `hirely_media` for banners). Alembic runs on container start.
Route the domain (currently `hrly.uz`) to it with the `server` block in the repo's `nginx.conf`:
`/j /r /a /t /admin /static /media /healthz` are proxied; `/api` is internal-only by design.
nginx **must set** `X-Real-IP` (the app trusts it for rate limits). Behind Cloudflare set `HIRELY_CLIENT_IP_HEADER=cf-connecting-ip`
and only accept traffic from Cloudflare. Serve over HTTPS (cookies are `Secure`). DNS and TLS for the domain are outside this repo (A record → the EC2 IP, certificate via certbot).

## Operations

* **Two-factor login (TOTP):** Admin → *Xavfsizlik* → enable, scan/enter the key in any authenticator app, confirm a code.
  After that every login needs password + code (each code works once; 6 wrong codes / 10 min lock the step).
  Lost phone: `docker exec -it hirely-links python -m app.cli reset-2fa admin@hirely.uz`.
* **Backups:** the `nuvi-db-backup` container dumps the whole Postgres every 6 h (custom format, verified with `pg_restore -l`),
  keeps 14 days in the `db_backups` volume and sends a Telegram alert if a dump fails. Restore:
  `docker exec -i nuvi-academy-db pg_restore -U postgres -d railway --clean --if-exists < dump` (copy the file out of the volume first:
  `docker cp nuvi-db-backup:/backups/<file>.dump .`). The volume lives on the same disk as the database — copy dumps off the
  server (S3/rclone) if you need disaster recovery; that needs credentials this repo does not hold.
* **CI:** `.github/workflows/ci.yml` runs the Hirely Links suite (real Postgres, migrations from scratch) and the bot-client tests on every
  pull request and **before every deploy** — a red suite blocks the deploy.
* **Monitoring:** `.github/workflows/monitor.yml` checks every 10 min: `hrly.uz/healthz` (and that no events are being dropped), the admin page,
  `nuvi.uz`, and that @HirelyUz got a post in the last 6 h (09:00-22:00 Tashkent). It messages the owner on Telegram only when the state changes
  (down / recovered). Secrets: `ALERT_BOT_TOKEN`, `ALERT_CHAT_ID`.
* **Deleting test links:** links whose source is `manual`/`test` (or category `test`) have a delete button on the job page; it also removes
  their events and rolls the ad counters back. Real (bot) links cannot be deleted because live Telegram posts point at them.
* **Load test** (laptop, 2 workers, embedded Postgres, single client on the same machine): ~530 req/s, p95 166 ms at concurrency 30,
  0 errors, every event persisted, writer queue drained 0.2 s after the last response. It caught (and fixed) a DB-pool stall when the
  slug cache expired under a burst — see `test_cold_cache_burst_does_not_exhaust_the_db_pool`.

## Security summary

Admin: bcrypt, optional TOTP 2FA, signed cookies scoped to `/admin`, CSRF + Origin check, rate-limited login, open-redirect-safe `next`.
API: constant-time bearer compare, per-token rate limit, strict pydantic (unknown fields rejected), URL/phone/username validation
(no `javascript:`, credentials, private IPs), idempotency. Public IDs are random (`JOB-…`, `UZ-…`, slugs), never sequential DB ids.
All SQL is parameterised (dimension names come from a whitelist). Jinja autoescaping + a strict CSP (`default-src 'self'`, no inline script/style),
`X-Frame-Options: DENY`, `nosniff`, `noindex`. Uploads are decoded, size- and pixel-limited and re-encoded (EXIF dropped). No IPs or PII are stored.

## Tests

```bash
pip install -r requirements-dev.txt
pytest          # spins up an embedded Postgres, applies the migrations, exercises API, landing, tracking, ads, admin
```
