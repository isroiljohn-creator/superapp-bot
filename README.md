# SuperApp Bot

Telegram SuperApp — CRM, Sales Funnel, Subscription, Referral, Analytics.

## Arxitektura

```
Instagram → Telegram Bot (CRM + Funnel) → Mini App (Payment + Course) → Subscription → Referral loop
```

## Tezkor boshlash

### 1. Muhitni sozlash

```bash
cp .env.example .env
# .env faylini o'z ma'lumotlaringiz bilan to'ldiring
```

### 2. Docker bilan ishga tushirish

```bash
docker-compose up -d
```

Bu quyidagilarni ishga tushiradi:
- **PostgreSQL** — ma'lumotlar bazasi
- **Redis** — navbat va FSM saqlash
- **Bot** — Telegram bot
- **API** — FastAPI (port 8000)
- **Worker** — ARQ delayed tasks

### 3. Lokal rivojlantirish (Docker'siz)

```bash
pip install -r requirements.txt

# Bot
python -m bot.main

# API
uvicorn api.main:app --reload --port 8000

# Worker
arq queue.worker.WorkerSettings
```

## Buyruqlar

| Buyruq | Tavsif |
|--------|--------|
| `/start` | Ro'yxatdan o'tish |
| `/profile` | Profil |
| `/referral` | Taklif havolasi |
| `/help` | Yordam |
| `/stats` | Statistika (admin) |
| `/broadcast` | Xabar yuborish (admin) |
| `/referral_settings` | Taklif sozlamalari (admin) |
| `/set <key> <value>` | Sozlama o'rnatish (admin) |

## API Endpointlar

| Endpoint | Tavsif |
|----------|--------|
| `GET /user/profile` | Foydalanuvchi profili |
| `GET /referral/stats` | Taklif statistikasi |
| `POST /payment/init` | To'lovni boshlash |
| `POST /payment/webhook/click` | Click webhook |
| `POST /payment/webhook/payme` | Payme webhook |
| `GET /course/modules` | Kurs modullari |
| `POST /course/progress` | Progress yangilash |

## Texnologiyalar

- **Bot**: Python + aiogram 3
- **API**: FastAPI
- **DB**: PostgreSQL + SQLAlchemy
- **Queue**: Redis + ARQ
- **Payment**: Click.uz + Payme
