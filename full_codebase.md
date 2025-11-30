# YASHA Fitness Bot - Full Codebase

## bot_runner.py
```python
import os
import telebot
from dotenv import load_dotenv
from core.db import db
from bot.handlers import register_all_handlers
from bot.reminders import start_reminder_thread

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("Error: BOT_TOKEN not found in .env file.")
    exit(1)

# Initialize Bot
bot = telebot.TeleBot(BOT_TOKEN)

def main():
    print("🚀 Fitness AI Bot ishga tushmoqda...")
    
    # Initialize Database
    db.init_db()
    print("✅ Database ulandi.")
    
    # Register Handlers
    register_all_handlers(bot)
    print("✅ Handlerlar yuklandi.")
    
    # Start Reminder Thread
    start_reminder_thread(bot)
    print("✅ Eslatmalar xizmati ishga tushdi.")
    
    # Start Polling
    print("🤖 Bot ishlamoqda...")

    # Set Chat Menu Button (Mini App)
    webapp_url = os.getenv("WEBAPP_URL")
    if webapp_url:
        try:
            bot.set_chat_menu_button(
                menu_button=telebot.types.MenuButtonWebApp(
                    type="web_app", 
                    text="📱 Ilova", 
                    web_app=telebot.types.WebAppInfo(url=webapp_url)
                )
            )
            print(f"✅ Menu tugmasi o'rnatildi: {webapp_url}")
        except Exception as e:
            print(f"⚠️ Menu tugmasini o'rnatishda xatolik: {e}")
    else:
        print("⚠️ WEBAPP_URL topilmadi. Mini App tugmasi o'rnatilmadi.")

    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot to‘xtadi: {e}")

if __name__ == "__main__":
    main()

```

## requirements.txt
```python
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pyTelegramBotAPI==4.14.0
google-generativeai>=0.8.3
sqlalchemy==2.0.23
aiosqlite==0.19.0
asyncpg==0.29.0
pydantic-settings==2.1.0
pyjwt==2.8.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
schedule==1.2.1
Pillow==10.0.0

```

## Procfile
```python
# Railway uses this file to determine how to run your app
web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
worker: python bot_runner.py

```

## core/db.py
```python
import sqlite3
import threading
from datetime import datetime, timedelta
import os

DB_PATH = "fitness_bot.db"

class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    full_name TEXT,
                    phone TEXT,
                    referral_code TEXT UNIQUE,
                    age INTEGER,
                    gender TEXT,
                    height INTEGER,
                    weight REAL,
                    target_weight REAL,
                    goal TEXT,
                    activity_level TEXT,
                    allergies TEXT,
                    points INTEGER DEFAULT 0,
                    last_checkin TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_premium INTEGER DEFAULT 0,
                    premium_until TEXT,
                    referrer_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Daily logs table for gamification
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date DATE,
                    water_drank BOOLEAN DEFAULT 0,
                    workout_done BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, date)
                )
            """)

            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            # Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE,
                    user_id INTEGER,
                    days INTEGER,
                    amount INTEGER,
                    currency TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Activity Logs table (generic)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    payload TEXT,
                    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            # Migrations
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN last_checkin DATE")
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN active BOOLEAN DEFAULT 1")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE orders ADD COLUMN days INTEGER")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP")
            except sqlite3.OperationalError:
                pass
                
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN activity_level TEXT")
            except sqlite3.OperationalError:
                pass

            # Calorie Logs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS calorie_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_kcal INTEGER,
                json_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Workout Cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workout_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    plan_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            # Menu Cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS menu_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    menu_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            # Admin Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    action TEXT,
                    target_id INTEGER,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            conn.close()

    # ... (keep existing methods) ...

    def log_activity(self, user_id, type, payload):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO activity_logs (user_id, type, payload) VALUES (?, ?, ?)", (user_id, type, payload))
            conn.commit()
            conn.close()

    def get_weight_history(self, user_id, limit=30):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Get from activity_logs where type='weight_update'
            # Payload is expected to be like '{"weight": 75.5}' or just '75.5' depending on implementation
            # For simplicity, let's assume we log it as JSON or simple string.
            # We'll return raw rows and parse in app.
            cursor.execute("""
                SELECT ts, payload FROM activity_logs 
                WHERE user_id = ? AND type = 'weight_update' 
                ORDER BY ts ASC
            """, (user_id,))
            logs = cursor.fetchall()
            conn.close()
            return logs

    def get_checkin_history(self, user_id, days=7):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Get from daily_logs
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT date, workout_done FROM daily_logs 
                WHERE user_id = ? AND date >= ? 
                ORDER BY date ASC
            """, (user_id, start_date))
            logs = cursor.fetchall()
            conn.close()
            return logs

    def add_user(self, telegram_id, username, phone, referral_code=None):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            ref_code = referral_code if referral_code else f"r{telegram_id}"
            try:
                print(f"DEBUG: Attempting to add user {telegram_id}")
                cursor.execute(
                    "INSERT OR IGNORE INTO users (telegram_id, username, phone, referral_code) VALUES (?, ?, ?, ?)",
                    (telegram_id, username, phone, ref_code)
                )
                conn.commit()
                print(f"DEBUG: User {telegram_id} added/ignored successfully.")
                return True
            except Exception as e:
                print(f"ERROR adding user {telegram_id}: {e}")
                return False
            finally:
                conn.close()

    def update_user_profile(self, user_id, **kwargs):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
                values = list(kwargs.values())
                values.append(user_id)
                
                # FIX: Use telegram_id instead of id
                cursor.execute(f"""
                    UPDATE users SET {set_clause} WHERE telegram_id = ?
                """, values)
                conn.commit()
            except Exception as e:
                print(f"Error updating profile: {e}")
            finally:
                conn.close()

    def get_user(self, user_id):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            # FIX: Use telegram_id instead of id
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, user))
            return None

    def add_points(self, user_id, points):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET points = points + ? WHERE id = ?", (points, user_id))
            conn.commit()
            conn.close()

    def get_daily_log(self, user_id, date_str):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_logs WHERE user_id = ? AND date = ?", (user_id, date_str))
            log = cursor.fetchone()
            conn.close()
            if log:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, log))
            return None

    def update_daily_log(self, user_id, date_str, **kwargs):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                # Ensure record exists
                cursor.execute("""
                    INSERT OR IGNORE INTO daily_logs (user_id, date) VALUES (?, ?)
                """, (user_id, date_str))
                
                set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
                values = list(kwargs.values())
                values.append(user_id)
                values.append(date_str)
                
                cursor.execute(f"""
                    UPDATE daily_logs SET {set_clause} WHERE user_id = ? AND date = ?
                """, values)
                conn.commit()
            except Exception as e:
                print(f"Error updating daily log: {e}")
            finally:
                conn.close()

    def get_referral_count(self, user_id):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count

    def set_premium(self, user_id, days):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get current premium status
            cursor.execute("SELECT premium_until FROM users WHERE telegram_id = ?", (user_id,))
            result = cursor.fetchone()
            current_until = result[0] if result else None
            
            now = datetime.now()
            if current_until:
                try:
                    current_until_dt = datetime.fromisoformat(current_until)
                    if current_until_dt > now:
                        new_until = current_until_dt + timedelta(days=days)
                    else:
                        new_until = now + timedelta(days=days)
                except ValueError:
                    new_until = now + timedelta(days=days)
            else:
                new_until = now + timedelta(days=days)
            
            cursor.execute("UPDATE users SET premium_until = ?, is_premium = 1 WHERE telegram_id = ?", (new_until.isoformat(), user_id))
            conn.commit()
            conn.close()

    def is_premium(self, user_id):
        user = self.get_user(user_id)
        if not user or not user.get('premium_until'):
            return False
        
        try:
            until = datetime.fromisoformat(user['premium_until'])
            return until > datetime.now()
        except ValueError:
            return False

    def remove_premium(self, user_id):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_premium = 0, premium_until = NULL WHERE telegram_id = ?", (user_id,))
            conn.commit()
            conn.close()

    def add_feedback(self, user_id, message):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO feedback (user_id, message) VALUES (?, ?)", (user_id, message))
            conn.commit()
            conn.close()

    def create_order(self, order_id, user_id, days, amount, currency='UZS'):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (order_id, user_id, days, amount, currency, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (order_id, user_id, days, amount, currency))
            conn.commit()
            conn.close()

    def update_order_status(self, order_id, status):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
            conn.commit()
            conn.close()

    def get_order(self, order_id):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            order = cursor.fetchone()
            conn.close()
            
            if order:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, order))
            return None

    def get_all_users(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id, full_name FROM users")
            users = cursor.fetchall()
            conn.close()
            return users

    def get_active_users(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id, full_name, username FROM users WHERE active = 1")
            users = cursor.fetchall()
            conn.close()
            return users

    def get_users_by_segment(self, gender=None, goal=None, activity_level=None, age_min=None, age_max=None, is_premium=None):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = "SELECT telegram_id, full_name FROM users WHERE active = 1"
            params = []
            if gender:
                query += " AND gender = ?"
                params.append(gender)
            if goal:
                query += " AND goal LIKE ?"
                params.append(f"%{goal}%")
            if activity_level:
                query += " AND activity_level = ?"
                params.append(activity_level)
            if age_min is not None:
                query += " AND age >= ?"
                params.append(age_min)
            if age_max is not None:
                query += " AND age <= ?"
                params.append(age_max)
            
            # Premium filter is complex because it depends on timestamp
            # We'll filter in python for simplicity or use complex SQL
            cursor.execute(query, params)
            users = cursor.fetchall()
            
            if is_premium is not None:
                filtered_users = []
                now = datetime.now()
                for u in users:
                    # Check premium status
                    # This is inefficient for large DBs but fine for MVP
                    # Better to do in SQL but requires parsing ISO string
                    cursor.execute("SELECT premium_until FROM users WHERE telegram_id = ?", (u[0],))
                    res = cursor.fetchone()
                    until = res[0]
                    is_prem = False
                    if until:
                        try:
                            if datetime.fromisoformat(until) > now:
                                is_prem = True
                        except:
                            pass
                    
                    if is_prem == is_premium:
                        filtered_users.append(u)
                users = filtered_users

            conn.close()
            return users

    def get_top_users(self, limit=20):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT full_name, points FROM users ORDER BY points DESC LIMIT ?", (limit,))
            users = cursor.fetchall()
            conn.close()
            return users
            
    def get_top_referrals(self, limit=10):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            # We need to count referrals manually or use a join
            # Since we don't have a separate referrals table, we count occurrences in users table
            cursor.execute("""
                SELECT referrer_id, COUNT(*) as count 
                FROM users 
                WHERE referrer_id IS NOT NULL 
                GROUP BY referrer_id 
                ORDER BY count DESC 
                LIMIT ?
            """, (limit,))
            top_referrers = cursor.fetchall()
            
            results = []
            for ref_id, count in top_referrers:
                cursor.execute("SELECT full_name FROM users WHERE id = ?", (ref_id,))
                res = cursor.fetchone()
                name = res[0] if res else "Noma'lum"
                results.append({"name": name, "id": ref_id, "count": count})
                
            conn.close()
            return results

    def set_user_active(self, user_id, active=True):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET active = ? WHERE id = ?", (1 if active else 0, user_id))
            conn.commit()
            conn.close()
            
    def export_csv(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            conn.close()
            
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(rows)
            return output.getvalue()

    def get_stats(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE active = 1")
            active_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT gender, COUNT(*) FROM users GROUP BY gender")
            gender_stats = dict(cursor.fetchall())
            
            cursor.execute("SELECT goal, COUNT(*) FROM users GROUP BY goal")
            goal_stats = dict(cursor.fetchall())
            
            cursor.execute("SELECT activity_level, COUNT(*) FROM users GROUP BY activity_level")
            activity_stats = dict(cursor.fetchall())
            
            # Premium count
            cursor.execute("SELECT COUNT(*) FROM users WHERE premium_until > ?", (datetime.now().isoformat(),))
            premium_users = cursor.fetchone()[0]
            
            conn.close()
            return {
                "total": total_users,
                "active": active_users,
                "gender": gender_stats,
                "goal": goal_stats,
                "activity": activity_stats,
                "premium": premium_users
            }

    def log_calorie_check(self, user_id, total_kcal, json_data):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO calorie_logs (user_id, total_kcal, json_data)
            VALUES (?, ?, ?)
            """, (user_id, total_kcal, json_data))
            conn.commit()
            conn.close()

db = Database()

```

## core/ai.py
```python
import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Using 1.5 Flash as requested (fastest and most cost-effective)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("DEBUG: Gemini AI initialized successfully.")
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
else:
    print("DEBUG: GEMINI_API_KEY not found in environment variables.")

def get_offline_workout(user_profile):
    goal = user_profile.get('goal', 'Sog‘liq')
    name = user_profile.get('name', 'Foydalanuvchi')
    
    header = f"⚠️ <b>AI hozircha band, {name}!</b>\nAmmo sizning maqsadingiz ({goal}) uchun maxsus offline rejani tayyorlab berdim:"
    
    if "Ozish" in goal:
        return f"""{header}

<b>Dushanba (Butun tana):</b>
1. Yugurish (15 daqiqa)
2. O‘tirib turish (Squats) - 3x15
3. Jim yotib gantel ko‘tarish - 3x12
4. Plank - 3x45 soniya

<b>Chorshanba (Kardio + Press):</b>
1. Arqon sakrash - 10 daqiqa
2. Velosiped mashqi (press) - 3x20
3. Burpee - 3x10
4. Oyoq ko‘tarish (turnikda) - 3x12

<b>Juma (Oyoq va Yelka):</b>
1. Zina mashqi (10 daqiqa)
2. Lunges (Odimlash) - 3x15
3. Yelka pressi - 3x12
4. Yon tomonga gantel ko‘tarish - 3x15
"""
    elif "Massa" in goal:
        return f"""{header}

<b>Dushanba (Ko‘krak va Triceps):</b>
1. Jim yotib shtanga ko‘tarish - 4x8-10
2. Brusda ishlash - 3xMax
3. Gantel bilan pulover - 3x12
4. Triceps blokda - 3x12

<b>Chorshanba (Orqa va Biceps):</b>
1. Turnikda tortilish - 3xMax
2. Shtanga tortish (belga) - 4x8-10
3. Biceps shtanga - 3x10
4. Hammer (bolg‘a) usuli - 3x12

<b>Juma (Oyoq va Yelka):</b>
1. Shtanga bilan o‘tirib turish - 4x8-10
2. Oyoq pressi - 3x12
3. Yelka pressi (shtanga) - 3x10
4. Trapetsiya (shrugs) - 3x15
"""
    else: # Sog'liq / Umumiy
        return f"""{header}

<b>Dushanba:</b>
1. Yengil yugurish - 10 daqiqa
2. O‘tirib turish - 3x12
3. Otjimaniya - 3x10
4. Press mashqi - 3x15

<b>Chorshanba:</b>
1. Tez yurish - 20 daqiqa
2. Turnikda osilish - 3x30 soniya
3. Planka - 3x30 soniya
4. Cho‘zilish mashqlari

<b>Juma:</b>
1. Velosiped yoki Ellips - 15 daqiqa
2. Yengil gantel mashqlari - 3x12
3. Bel mashqlari (Gipertenziya) - 3x12
4. Nafas mashqlari
"""

def get_offline_menu(user_profile):
    goal = user_profile.get('goal', 'Sog‘liq')
    name = user_profile.get('name', 'Foydalanuvchi')
    
    header = f"⚠️ <b>AI hozircha band, {name}!</b>\nAmmo sizning maqsadingiz ({goal}) uchun maxsus offline rejani tayyorlab berdim:"
    
    if "Ozish" in goal:
        return f"""{header}

<b>Nonushta:</b>
- 2 ta qaynatilgan tuxum
- Yarimta avokado yoki 10 ta bodom
- Ko‘k choy (shakarsiz)

<b>Tushlik:</b>
- 150g tovuq ko‘krak go‘shti (qaynatilgan)
- Grechka (yog‘siz)
- Karam va sabzi salati

<b>Kechki ovqat:</b>
- 150g baliq yoki tvorog
- Yashil sabzavotlar
- 1 stakan kefir
"""
    elif "Massa" in goal:
        return f"""{header}

<b>Nonushta:</b>
- 3 ta tuxum (qovurilgan)
- Suli yormasi (sut bilan, banan va asal qo‘shilgan)
- Tost non (pishloq bilan)

<b>Tushlik:</b>
- 200g mol go‘shti yoki tovuq
- Guruch yoki makaron
- Sabzavotli salat (zaytun moyi bilan)

<b>Kechki ovqat:</b>
- 150g baliq yoki tovuq
- Kartoshka pyure
- Tvorog (smetana bilan)
"""
    else:
        return f"""{header}

<b>Nonushta:</b>
- Suli yormasi (mevalar bilan)
- 1 ta qaynatilgan tuxum
- Choy yoki qahva

<b>Tushlik:</b>
- Tovuq sho‘rva
- 100g go‘sht va garnir
- Salat

<b>Kechki ovqat:</b>
- Yengil hazm bo‘ladigan taom (dimlama)
- Salat
- Olma yoki nok
"""

def call_gemini(prompt):
    """Sends prompt to Gemini with fallback."""
    if not GEMINI_API_KEY:
        print("DEBUG: No API Key")
        return None

    models_to_try = [
        'gemini-2.5-flash',
        'gemini-2.5-flash-preview-09-2025',
        'gemini-2.5-flash-lite',
        'gemini-2.0-flash-exp', 
        'gemini-1.5-flash'
    ]
    
    for model_name in models_to_try:
        try:
            print(f"DEBUG: Trying model {model_name}...")
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response.text:
                print(f"DEBUG: Success with {model_name}")
                return response.text
        except Exception as e:
            print(f"DEBUG: Failed with {model_name}: {e}")
            
    return None

def format_ai_text(raw_text, title):
    """Cleans and formats AI output."""
    if not raw_text:
        return ""
    
    # Clean up Markdown
    text = raw_text.replace("**", "").replace("##", "").replace("#", "")
    
    # Ensure no dangerous HTML
    text = text.replace("<script>", "").replace("</script>", "")
    
    # Limit length (soft limit)
    if len(text) > 2000:
        text = text[:2000] + "..."
        
    # Add Title
    formatted = f"🍽 <b>{title}</b>\n\n{text.strip()}"
    return formatted

def ai_generate_workout(user_profile):
    """Generates a weekly workout plan using Gemini or fallback."""
    prompt = f"""
Siz Telegram uchun qisqa, silliq, tushunarli mashq rejalari tuzadigan professional fitness trenerisiz.

Foydalanuvchi profili:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Maqsad: {user_profile.get('goal')}
Bo‘y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Faollik darajasi: {user_profile.get('activity_level', 'Belgilanmagan')}

🎯 Vazifa:
Foydalanuvchiga uy sharoitida bajariladigan 4 kunlik mashq rejasi tuzing.

📌 FORMAT TALABLARI:
- HTML ishlatma (<p>, <ul>, <li> yo‘q).
- Faqat oddiy matn + <b>qalin</b> joylar.
- Emojilarni minimal ishlat (faqat bo‘lim sarlavhalarida).
- Har bir kun quyidagicha struktura bo‘lsin:

<b>1-kun: Ko‘krak & Triceps</b>  
- Mashq 1 — takrorlar  
- Mashq 2 — takrorlar  
- Mashq 3 — takrorlar  

<b>2-kun: Oyoq & Yelka</b>  
- ...

<b>3-kun: Dam olish</b>  
- Qisqa maslahat yozing (1–2 jumla)

<b>4-kun: Orqa & Core</b>  
- ... 

🧩 Matn juda uzun chiqmasin. Maksimal 1500 belgi.
🧩 Har bir mashq sodda va uyda qilinadigan bo‘lsin.
🧩 Javob faqat matn ko‘rinishida bo‘lsin, HTML teglarsiz.
"""
    
    response_text = call_gemini(prompt)
    if response_text and len(response_text) > 50: # Ensure meaningful response
        return format_ai_text(response_text, "Sizning mashg‘ulot rejangiz")
        
    print(f"DEBUG: AI failed or returned empty. Using fallback for user {user_profile.get('name')}")
    return get_offline_workout(user_profile)

def ai_generate_menu(user_profile):
    """Generates a weekly meal plan using Gemini or fallback."""
    
    # Build allergy warning if present
    allergy_text = user_profile.get('allergies')
    allergy_section = ""
    if allergy_text and allergy_text.lower() not in ['yo\'q', 'no', 'none', 'yoq']:
        allergy_section = f"\n\n⚠️ ⚠️ ⚠️ JUDA MUHIM ⚠️ ⚠️ ⚠️\nFoydalanuvchida {allergy_text} ga ALLERGIYA BOR!\nTavsiya qilingan ovqatlarda BU MAHSULOTLAR BO'LMASLIGI KERAK!\nAlternativ mahsulotlar tavsiya qiling.\n"
    
    prompt = f"""
Siz Telegram uchun ovqatlanish bo'yicha qisqa, silliq, o'qilishi oson matn yozadigan dietologsiz.

Foydalanuvchi profili:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Bo'y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Faollik darajasi: {user_profile.get('activity_level', 'Belgilanmagan')}
Maqsad: {user_profile.get('goal')}{allergy_section}

🎯 Vazifa:
Foydalanuvchiga 7 kunlik ovqatlanish rejasi tuzing. Juda uzun bo'lmasin — odam Telegramda o'rtacha 700–900 belgi o'qiydi.

📌 MUHIM FORMAT TALABLARI:
- Hech qanday HTML (<p>, <br>, <ul>, <li>) ishlatma.
- Faqat matn + <b>qalin</b> joylar.
- Emojilarni kam ishlat — faqat kun nomlarida yoki sarlavhalarda.
- Har kun quyidagicha bo'lsin:

<b>1-kun</b>
- Nonushta: ...
- Tushlik: ...
- Kechki: ...
- Snack: ...

- 7 kunda ham struktura bir xil bo'lsin.
- Oxirida alohida blokda:

<b>Xarid ro'yxati</b>
- ...

🧩 Matn juda uzun chiqmasin. Maksimal 1500 belgi.

📢 Javob faqat matn ko'rinishida bo'lsin, HTML teglarsiz!
"""

    response_text = call_gemini(prompt)
    if response_text and len(response_text) > 50:
        return format_ai_text(response_text, "Sizning ovqatlanish rejangiz")

    print(f"DEBUG: AI failed or returned empty. Using fallback for user {user_profile.get('name')}")
    return get_offline_menu(user_profile)

def ai_answer_question(question):
    """Answers a general fitness question using Gemini."""
    response_text = call_gemini(f"Siz fitnes murabbiyisiz. Savolga qisqa va aniq javob bering (o'zbek tilida): {question}")
    if response_text:
        return format_ai_text(response_text, "Savolingizga javob")
            
    return "⚠️ AI hozircha band. Iltimos, keyinroq urinib ko‘ring."

def analyze_food_image(image_data):
    """
    Analyzes food image using Gemini Vision and returns JSON with calorie info.
    image_data: bytes of the image
    """
    if not GEMINI_API_KEY:
        print("DEBUG: No API key for vision")
        return '{"error": "GEMINI_API_KEY topilmadi. Admin bilan bog\'laning."}'

    prompt = """
    You are an expert food recognition and calorie estimation model.
    Your job is to:
    1. Identify all foods in this image.
    2. Estimate grams for each item.
    3. Calculate calories per item.
    4. Calculate total calories.

    You must return the result STRICTLY in this JSON format:

    {
      "items": [
        {"name": "food name", "grams": 0, "calories": 0}
      ],
      "total_calories": 0
    }

    If the image is unclear or contains no food, return:
    {"error": "Image unclear or no food detected"}
    """

    # Try vision capable models
    models_to_try = [
        'gemini-2.5-flash',
        'gemini-2.0-flash-exp',
        'gemini-1.5-flash'
    ]

    import PIL.Image
    import io

    try:
        image = PIL.Image.open(io.BytesIO(image_data))
    except Exception as e:
        print(f"DEBUG: Image open error: {e}")
        return None

    for model_name in models_to_try:
        try:
            print(f"DEBUG: Trying vision with {model_name}...")
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(model_name)
            
            response = model.generate_content([prompt, image])
            
            if response.text:
                # Clean up json block if present
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text.replace("```json", "").replace("```", "")
                elif text.startswith("```"):
                    text = text.replace("```", "")
                
                return text.strip()
                
        except Exception as e:
            print(f"DEBUG: Failed with {model_name}: {e}")
            
    return None

```

## bot/handlers.py
```python
from bot import onboarding, menu, gamification, admin, feedback, premium, profile, templates
from bot.calories import handle_calorie_button, handle_food_photo, STATE_CALORIE_PHOTO
from bot.keyboards import main_menu_keyboard

def register_all_handlers(bot):
    # Calorie Handlers
    @bot.message_handler(func=lambda message: message.text == "📸 Kaloriyani aniqlash")
    def calorie_handler(message):
        handle_calorie_button(message, bot, onboarding.manager)

    @bot.message_handler(content_types=['photo'])
    def photo_handler(message):
        if onboarding.manager.get_state(message.from_user.id) == STATE_CALORIE_PHOTO:
            handle_food_photo(message, bot, onboarding.manager)

    # EMERGENCY PROFILE HANDLER - High Priority
            
    @bot.message_handler(func=lambda message: message.text == "👤 Profil")
    def profile_handler(message):
        print(f"DEBUG: EMERGENCY PROFILE HANDLER triggered by {message.from_user.id}")
        from bot.profile import handle_profile
        handle_profile(message, bot)

    @bot.message_handler(commands=['profile_debug'])
    def debug_profile_command(message):
        print(f"DEBUG: /profile_debug triggered")
        from bot.profile import handle_profile
        handle_profile(message, bot)

    # Register all module handlers
    onboarding.register_handlers(bot)
    menu.register_handlers(bot)
    gamification.register_handlers(bot)
    admin.register_handlers(bot)
    feedback.register_handlers(bot)
    premium.register_handlers(bot)
    profile.register_handlers(bot)
    templates.register_handlers(bot)
    
    # General utility handlers
    @bot.message_handler(commands=['menu'])
    def handle_menu_command(message):
        bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=main_menu_keyboard())

    @bot.message_handler(commands=['ping'])
    def handle_ping(message):
        bot.reply_to(message, "Pong! 🏓 Bot ishlamoqda.")

    @bot.message_handler(commands=['myid'])
    def handle_myid(message):
        bot.reply_to(message, f"🆔 Sizning ID raqamingiz: `{message.from_user.id}`", parse_mode="Markdown")

    @bot.message_handler(commands=['reset'])
    def handle_reset(message):
        """Force reset user state"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Clear onboarding state
        onboarding.manager.clear_user(user_id)
        
        # Clear Telebot next step handlers (CRITICAL FIX)
        try:
            bot.clear_step_handler_by_chat_id(chat_id)
        except Exception as e:
            print(f"Error clearing step handler: {e}")
            
        bot.reply_to(message, "🔄 Holat to'liq tozalandi (Step Handlers + State). /start ni bosing.")

    @bot.message_handler(commands=['version'])
    def handle_version(message):
        bot.reply_to(message, "🤖 Bot Version: v2.5 - DEBUG MODE\n\nAgar bu xabarni ko'rayotgan bo'lsangiz, demak bot yangilangan!")

    # Debug callback LAST (as fallback)
    @bot.callback_query_handler(func=lambda call: True)
    def debug_callback(call):
        print(f"DEBUG: Unhandled callback: {call.data} from {call.from_user.id}")
        bot.answer_callback_query(call.id, "⚠️ Bu tugma hali ishlamayapti")
        
    # Debug message handler (catch-all for debugging)
    @bot.message_handler(func=lambda m: True)
    def debug_message(message):
        print(f"DEBUG: Unhandled message: {message.text} from {message.from_user.id}")
        # Only reply if it looks like a command or button press failed
        if message.text.startswith("/") or message.text in ["👤 Profil", "Profil"]:
             bot.reply_to(message, f"⚠️ DEBUG: Men '{message.text}' xabarini oldim, lekin unga javob beradigan handler topilmadi.\n\nIltimos /reset ni bosing.")


```

## bot/keyboards.py
```python
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

def phone_request_keyboard():
    """Request phone number from user"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    return markup

def gender_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Erkak 👨", callback_data="gender_male"),
        InlineKeyboardButton("Ayol 👩", callback_data="gender_female")
    )
    return markup

def goal_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Ozish 🏃‍♂️", callback_data="goal_weight_loss"))
    markup.add(InlineKeyboardButton("Massa olish 💪", callback_data="goal_muscle_gain"))
    markup.add(InlineKeyboardButton("Sog‘liqni tiklash 🧘", callback_data="goal_health"))
    return markup

def activity_level_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Kam harakat (Sedentary) 🪑", callback_data="activity_sedentary"),
        InlineKeyboardButton("Yengil faol (Lightly Active) 🚶‍♂️", callback_data="activity_light"),
        InlineKeyboardButton("O'rtacha faol (Moderately Active) 🏃‍♂️", callback_data="activity_moderate"),
        InlineKeyboardButton("Juda faol (Very Active) 🏋️‍♂️", callback_data="activity_active"),
        InlineKeyboardButton("Atlet (Athlete) 🔥", callback_data="activity_athlete")
    )
    return markup

def allergy_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Yo‘q ❌", callback_data="allergy_no"),
        InlineKeyboardButton("Ha ✅", callback_data="allergy_yes")
    )
    return markup

def main_menu_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    markup.add(
        KeyboardButton("Mashqlar 🏋️"),
        KeyboardButton("Menyu 🍏")
    )
    markup.add(
        KeyboardButton("Vazifalar ✅"),
        KeyboardButton("Vazifalar ✅")
    )
    markup.add(
        KeyboardButton("💎 Premium"),
        KeyboardButton("📞 Qayta aloqa")
    )
    markup.add(KeyboardButton("👤 Profil"))
    markup.add(KeyboardButton("📸 Kaloriyani aniqlash"))
    return markup

def gamification_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Mashq qildim ✅", callback_data="daily_workout_done"))
    markup.add(InlineKeyboardButton("Suv ichdim 💧", callback_data="daily_water_done"))
    return markup

```

## bot/menu.py
```python
from bot.workout import handle_workout_plan, handle_meal_plan
from bot.referral import handle_referral
from bot.gamification import handle_tasks
from bot.keyboards import main_menu_keyboard
from bot.feedback import handle_feedback_start
from bot.premium import handle_premium_menu

def register_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == "Mashqlar 🏋️")
    def menu_workout(message):
        handle_workout_plan(message, bot)

    @bot.message_handler(commands=['menu'])
    def handle_menu_command(message):
        bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=main_menu_keyboard())

    @bot.message_handler(func=lambda message: message.text == "Menyu 🍏")
    def menu_meal(message):
        handle_meal_plan(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🔗 Referal")
    def menu_referral(message):
        handle_referral(message, bot)

    @bot.message_handler(func=lambda message: message.text == "Vazifalar ✅")
    def menu_tasks(message):
        handle_tasks(message, bot)

    @bot.message_handler(func=lambda message: message.text == "💎 Premium")
    def menu_premium(message):
        handle_premium_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📞 Qayta aloqa")
    def menu_feedback(message):
        handle_feedback_start(message, bot)

    @bot.message_handler(func=lambda message: "Profil" in message.text)
    def menu_profile(message):
        print(f"DEBUG: Menu Profile button clicked by {message.from_user.id}")
        from bot.profile import handle_profile
        handle_profile(message, bot)

```

## bot/onboarding.py
```python
from telebot import types
from core.db import db
from core.utils import generate_referral_code, get_referrer_id_from_code
from bot.keyboards import (
    phone_request_keyboard, gender_keyboard, goal_keyboard, 
    allergy_keyboard, main_menu_keyboard, activity_level_keyboard
)

# States
STATE_NONE = 0
STATE_PHONE = 1
STATE_NAME = 2
STATE_AGE = 3
STATE_GENDER = 4
STATE_HEIGHT = 5
STATE_WEIGHT = 6
STATE_ACTIVITY = 9 # New state
STATE_GOAL = 7
STATE_ALLERGY = 8

class OnboardingManager:
    def __init__(self):
        self.user_states = {}
        self.user_data = {}

    def get_state(self, user_id):
        return self.user_states.get(user_id, STATE_NONE)

    def set_state(self, user_id, state):
        self.user_states[user_id] = state

    def update_data(self, user_id, key, value):
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id][key] = value

    def get_data(self, user_id):
        return self.user_data.get(user_id, {})

    def clear_user(self, user_id):
        if user_id in self.user_states:
            del self.user_states[user_id]
        if user_id in self.user_data:
            del self.user_data[user_id]

manager = OnboardingManager()

def start_onboarding(message, bot):
    """Step 0: Check if user exists, if not request phone number FIRST"""
    user_id = message.from_user.id
    
    # Check if user already exists in database
    existing_user = db.get_user(user_id)
    if existing_user:
        bot.send_message(
            user_id, 
            "Asosiy menyuga qaytdingiz, pastdagi tugmalar orqali keyingi qadamni tanlang👇🏻", 
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Handle start parameters
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        code = args[1]
        
        # Handle premium shortcut
        if code == 'premium':
            from bot.premium import handle_premium_menu
            handle_premium_menu(message, bot)
            return
            
        referrer_id = get_referrer_id_from_code(code)
        
        # Prevent self-referral
        if referrer_id == user_id:
            referrer_id = None
    
    # Initialize onboarding
    manager.clear_user(user_id)
    manager.set_state(user_id, STATE_PHONE)
    manager.update_data(user_id, 'referrer_id', referrer_id)
    
    bot.send_message(
        user_id,
        "🎉 Assalomu alaykum! YASHA botiga xush kelibsiz.\n\n"
        "Davom etish uchun telefon raqamingizni yuboring 👇",
        reply_markup=phone_request_keyboard()
    )

def process_phone(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_PHONE:
        return

    if not message.contact:
        bot.send_message(
            user_id,
            "❌ Iltimos, telefon raqamingizni kontakt sifatida yuboring 👇\n\n"
            "Pastdagi tugmani bosing:",
            reply_markup=phone_request_keyboard()
        )
        return
    
    phone = message.contact.phone_number
    manager.update_data(user_id, 'phone', phone)
    manager.set_state(user_id, STATE_NAME)
    
    bot.send_message(
        user_id, 
        f"✅ Rahmat!\n\n"
        f"Endi ismingizni kiriting:",
        reply_markup=types.ReplyKeyboardRemove()
    )

def process_name(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_NAME:
        return
    
    name = message.text.strip()
    manager.update_data(user_id, 'name', name)
    manager.set_state(user_id, STATE_AGE)
    
    bot.send_message(user_id, f"Rahmat, {name}! Yoshingiz nechida? (faqat raqam)")

def process_age(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_AGE:
        return
    
    if not message.text.isdigit():
        bot.send_message(user_id, "Iltimos, yoshingizni raqamda kiriting:")
        return
    
    age = int(message.text)
    if age < 10 or age > 120:
        bot.send_message(user_id, "Yoshingizni to'g'ri kiriting (10-120 oralig'ida):")
        return
    
    manager.update_data(user_id, 'age', age)
    manager.set_state(user_id, STATE_GENDER)
    
    bot.send_message(user_id, "Jinsingizni tanlang:", reply_markup=gender_keyboard())

def process_gender(call, bot):
    user_id = call.from_user.id
    print(f"DEBUG: process_gender called for {user_id}, state: {manager.get_state(user_id)}")
    
    if manager.get_state(user_id) != STATE_GENDER:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
        except:
            pass
        return
    
    gender = call.data
    manager.update_data(user_id, 'gender', gender)
    manager.set_state(user_id, STATE_HEIGHT)
    print(f"DEBUG: State updated to STATE_HEIGHT for {user_id}")
    
    try:
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"DEBUG: Error answering callback: {e}")
        
    msg = bot.send_message(user_id, "Bo'yingizni kiriting (sm):")
    # Explicitly register next step handler as a backup for FSM
    # bot.register_next_step_handler(msg, process_height, bot) 
    # Actually, FSM should handle this via the generic handler in register_handlers
    # But let's make sure the generic handler is catching it.

def process_height(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_HEIGHT:
        return
    
    if not message.text.isdigit():
        bot.send_message(user_id, "Iltimos, bo'yingizni raqamda kiriting (sm):")
        return
    
    height = int(message.text)
    if height < 50 or height > 250:
        bot.send_message(user_id, "Bo'yingizni to'g'ri kiriting (50-250 sm):")
        return
    
    manager.update_data(user_id, 'height', height)
    manager.set_state(user_id, STATE_WEIGHT)
    
    bot.send_message(user_id, "Vazningizni kiriting (kg):")

def process_weight(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_WEIGHT:
        return
    
    try:
        weight = float(message.text)
        if weight < 20 or weight > 300:
            raise ValueError
    except ValueError:
        bot.send_message(user_id, "Vazningizni to'g'ri kiriting (20-300 kg):")
        return
    
    manager.update_data(user_id, 'weight', weight)
    manager.set_state(user_id, STATE_ACTIVITY)
    
    bot.send_message(user_id, "Jismoniy faollik darajangizni tanlang:", reply_markup=activity_level_keyboard())

def process_activity(call, bot):
    user_id = call.from_user.id
    
    if manager.get_state(user_id) != STATE_ACTIVITY:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
        except:
            pass
        return
    
    activity = call.data.replace("activity_", "")
    manager.update_data(user_id, 'activity_level', activity)
    manager.set_state(user_id, STATE_GOAL)
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
        
    bot.send_message(user_id, "Maqsadingizni tanlang:", reply_markup=goal_keyboard())

def process_goal(call, bot):
    user_id = call.from_user.id
    
    if manager.get_state(user_id) != STATE_GOAL:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
        except:
            pass
        return
    
    goal = call.data
    manager.update_data(user_id, 'goal', goal)
    manager.set_state(user_id, STATE_ALLERGY)
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
        
    bot.send_message(user_id, "Hastaligingiz yoki allergiyangiz mavjudmi?", reply_markup=allergy_keyboard())

def process_allergy(call, bot):
    user_id = call.from_user.id
    
    if manager.get_state(user_id) != STATE_ALLERGY:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
        except:
            pass
        return
    
    allergy_choice = call.data
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    
    if allergy_choice == "allergy_yes":
        # Ask for allergy details
        manager.set_state(user_id, STATE_NONE)  # Temporarily exit FSM for text input
        msg = bot.send_message(
            user_id,
            "📝 Qanday hastalik yoki nima mahsulotlarga allergiyangiz bor?\n\n"
            "Masalan: yong'oq, sut, tuxum, gluten, dengiz mahsulotlari",
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(msg, process_allergy_details, bot)
    else:
        # No allergy
        manager.update_data(user_id, 'allergies', None)
        finish_onboarding(user_id, message=call.message, bot=bot)

def process_allergy_details(message, bot):
    """Process allergy details text input"""
    user_id = message.from_user.id
    allergy_details = message.text.strip()
    
    manager.update_data(user_id, 'allergies', allergy_details)
    
    # Finish Onboarding
    finish_onboarding(user_id, message=message, bot=bot)

def finish_onboarding(user_id, message, bot):
    data = manager.get_data(user_id)
    referrer_id = data.get('referrer_id')
    
    # Add user to database
    db.add_user(
        telegram_id=user_id,
        username=message.chat.username or f"user_{user_id}",
        phone=data.get('phone')
    )
    
    # Update profile
    db.update_user_profile(
        user_id=user_id,
        age=data.get('age'),
        gender=data.get('gender'),
        height=data.get('height'),
        weight=data.get('weight'),
        activity_level=data.get('activity_level'),
        goal=data.get('goal'),
        allergies=data.get('allergies')
    )
    
    # Handle referral rewards
    if referrer_id:
        db.add_points(referrer_id, 5)
        try:
            bot.send_message(
                referrer_id,
                f"🎉 Yangi do'st ro'yxatdan o'tdi! +5 ball olasiz.\n"
                f"Jami ballar: {db.get_user(referrer_id)['points']}"
            )
        except:
            pass
    
    # Clear state
    manager.clear_user(user_id)
    
    # Send welcome message
    bot.send_message(
        user_id,
        f"✅ Ro'yxatdan o'tdingiz!\n\n"
        f"YASHA ga xush kelibsiz. Pastdagi tugmalar orqali botdan foydalanishingiz mumkin 👇",
        reply_markup=main_menu_keyboard()
    )

def register_handlers(bot):
    """Register all onboarding-related handlers"""
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        start_onboarding(message, bot)
    
    @bot.message_handler(content_types=['contact'])
    def handle_contact(message):
        process_phone(message, bot)
        
    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_NAME)
    def handle_name_step(message):
        process_name(message, bot)

    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_AGE)
    def handle_age_step(message):
        process_age(message, bot)
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
    def handle_gender_step(call):
        try:
            # Extract actual gender value (male/female) from gender_male/gender_female
            gender_val = call.data.split('_')[1]
            
            # Answer callback immediately to stop loading animation
            bot.answer_callback_query(call.id)
            
            # Update state and data
            user_id = call.from_user.id
            manager.update_data(user_id, 'gender', gender_val)
            manager.set_state(user_id, STATE_HEIGHT)
            
            # Send next step message
            msg = bot.send_message(user_id, "Bo'yingizni kiriting (sm):")
            
            # Explicitly register next step just in case FSM generic handler misses it
            # (Though generic handler should catch it if state is set correctly)
            # bot.register_next_step_handler(msg, process_height, bot)
            
        except Exception as e:
            print(f"ERROR in handle_gender_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi. Qaytadan urining.")
            except:
                pass

    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_HEIGHT)
    def handle_height_step(message):
        process_height(message, bot)

    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_WEIGHT)
    def handle_weight_step(message):
        process_weight(message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('activity_'))
    def handle_activity_step(call):
        try:
            bot.answer_callback_query(call.id)
            process_activity(call, bot)
        except Exception as e:
            print(f"ERROR in handle_activity_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi.")
            except:
                pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith('goal_'))
    def handle_goal_step(call):
        try:
            # Extract goal value (weight_loss/muscle_gain/health)
            goal_val = call.data.split('_', 1)[1] # Split only on first underscore
            
            bot.answer_callback_query(call.id)
            
            user_id = call.from_user.id
            manager.update_data(user_id, 'goal', goal_val)
            manager.set_state(user_id, STATE_ALLERGY)
            
            bot.send_message(user_id, "Qandaydir hastalik yoki biror mahsulotga allergiyangiz bormi?", reply_markup=allergy_keyboard())
            
        except Exception as e:
            print(f"ERROR in handle_goal_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi.")
            except:
                pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith('allergy_'))
    def handle_allergy_step(call):
        try:
            bot.answer_callback_query(call.id)
            # Call the actual process_allergy function that handles the logic
            process_allergy(call, bot)
        except Exception as e:
            print(f"ERROR in handle_allergy_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi.")
            except:
                pass


```

## bot/profile.py
```python
from telebot import types
from core.db import db
from bot.keyboards import main_menu_keyboard, gender_keyboard, goal_keyboard, allergy_keyboard, activity_level_keyboard

import traceback

def handle_profile(message, bot):
    """Show user profile with edit options"""
    try:
        user_id = message.from_user.id
        print(f"DEBUG: handle_profile called for user {user_id}")
        
        # Test message to confirm handler reached
        # bot.send_message(user_id, "DEBUG: Profil yuklanmoqda...") 
        
        user = db.get_user(user_id)
        
        if not user:
            bot.send_message(user_id, "Siz hali ro'yxatdan o'tmagansiz. /start ni bosing.")
            return

        # Format profile text
        text = (
            f"👤 Sizning Profilingiz\n\n"
            f"Ism: {user.get('full_name', 'Noma’lum')}\n"
            f"Yosh: {user.get('age', '-')} yosh\n"
            f"Jins: {user.get('gender', '-')}\n"
            f"Bo'y: {user.get('height', '-')} sm\n"
            f"Vazn: {user.get('weight', '-')} kg\n"
            f"Faollik: {user.get('activity_level', 'Belgilanmagan')}\n"
            f"Maqsad: {user.get('goal', '-')}\n"
            f"Allergiya: {user.get('allergies') or 'Yo‘q'}\n\n"
            f"⚙️ Qaysi qismni o'zgartirmoqchisiz?"
        )
        
        # Create inline keyboard for editing
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("Ism", callback_data="edit_full_name"),
            types.InlineKeyboardButton("Yosh", callback_data="edit_age"),
            types.InlineKeyboardButton("Jins", callback_data="edit_gender"),
            types.InlineKeyboardButton("Bo'y", callback_data="edit_height"),
            types.InlineKeyboardButton("Vazn", callback_data="edit_weight"),
            types.InlineKeyboardButton("Faollik", callback_data="edit_activity"),
            types.InlineKeyboardButton("Maqsad", callback_data="edit_goal"),
            types.InlineKeyboardButton("Allergiya", callback_data="edit_allergies"),
            types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")
        ]
        markup.add(*buttons)
        
        bot.send_message(user_id, text, reply_markup=markup)
        
    except Exception as e:
        error_msg = f"❌ Profil xatolik berdi:\n\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            bot.send_message(message.from_user.id, error_msg[:4000]) # Telegram limit
        except:
            pass

def register_handlers(bot):
    """Register profile related handlers"""
    
    @bot.message_handler(commands=['profile'])
    def command_profile(message):
        handle_profile(message, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
    def back_to_main(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "Asosiy menyu", reply_markup=main_menu_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
    def handle_edit_callback(call):
        field = call.data.replace("edit_", "")
        user_id = call.from_user.id
        
        bot.answer_callback_query(call.id)
        
        # Define prompts for each field
        prompts = {
            "full_name": "Yangi ismingizni kiriting:",
            "age": "Yangi yoshingizni kiriting (raqamda):",
            "gender": "Jinsingizni tanlang:",
            "height": "Yangi bo'yingizni kiriting (sm):",
            "weight": "Yangi vazningizni kiriting (kg):",
            "goal": "Yangi maqsadingizni tanlang:",
            "allergies": "Allergiyangiz bormi? (Ha/Yo'q yoki mahsulot nomlari):"
        }
        
        prompt = prompts.get(field, "Yangi qiymatni kiriting:")
        
        # Handle fields that need keyboards
        if field == "gender":
            bot.send_message(user_id, prompt, reply_markup=gender_keyboard())
        elif field == "goal":
            bot.send_message(user_id, prompt, reply_markup=goal_keyboard())
        elif field == "activity":
            bot.send_message(user_id, "Yangi faollik darajasini tanlang:", reply_markup=activity_level_keyboard())
        elif field == "allergies":
             # For allergies, we can use text input or the simple Yes/No keyboard.
             # Given the requirement "Yangi ... kiriting", text is more flexible for editing details.
             # But let's offer the keyboard first for simplicity, or just text if they want to list details.
             # Let's stick to text for editing to allow detailed input easily.
             msg = bot.send_message(user_id, "Yangi allergiya ma'lumotlarini yozing (yoki 'Yo'q' deb yozing):")
             bot.register_next_step_handler(msg, process_edit_input, bot, field)
             return
        else:
            msg = bot.send_message(user_id, prompt)
            bot.register_next_step_handler(msg, process_edit_input, bot, field)

    # Handlers for keyboard-based edits (Gender, Goal)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
    def process_gender_edit(call):
        user_id = call.from_user.id
        new_gender = call.data.split("_")[1] # male/female
        # Map to display text if needed, or store as is. DB stores 'male'/'female' usually or localized.
        # Let's verify what DB expects. onboarding.py uses 'male'/'female'.
        # Let's map to Uzbek for display consistency if DB stores raw.
        # Actually onboarding stores raw 'male'/'female'.
        
        db.update_user_profile(user_id, gender=new_gender)
        bot.answer_callback_query(call.id, "Jins yangilandi ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("goal_"))
    def process_goal_edit(call):
        user_id = call.from_user.id
        new_goal = call.data # e.g. goal_weight_loss
        # We might want to strip 'goal_' prefix or store full string.
        # onboarding stores 'weight_loss'.
        # Let's strip 'goal_' to be consistent with onboarding.
        if new_goal.startswith("goal_"):
             new_goal = new_goal.replace("goal_", "")
             
        db.update_user_profile(user_id, goal=new_goal)
        bot.answer_callback_query(call.id, "Maqsad yangilandi ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("activity_"))
    def process_activity_edit(call):
        user_id = call.from_user.id
        new_activity = call.data.replace("activity_", "")
        
        db.update_user_profile(user_id, activity_level=new_activity)
        bot.answer_callback_query(call.id, "Faollik darajasi yangilandi ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot)

def process_edit_input(message, bot, field):
    """Process text input for profile editing"""
    user_id = message.from_user.id
    value = message.text
    
    try:
        # Validation and conversion
        if field == "age":
            if not value.isdigit() or not (10 <= int(value) <= 100):
                bot.send_message(user_id, "❌ Iltimos, to'g'ri yosh kiriting (10-100).")
                return
            value = int(value)
            
        elif field == "height":
            if not value.isdigit() or not (100 <= int(value) <= 250):
                bot.send_message(user_id, "❌ Iltimos, to'g'ri bo'y kiriting (100-250 sm).")
                return
            value = int(value)
            
        elif field == "weight":
            try:
                val = float(value)
                if not (30 <= val <= 300):
                    raise ValueError
                value = val
            except ValueError:
                bot.send_message(user_id, "❌ Iltimos, to'g'ri vazn kiriting (30-300 kg).")
                return
        
        # Update DB
        kwargs = {field: value}
        db.update_user_profile(user_id, **kwargs)
        
        bot.send_message(user_id, f"{field.capitalize()} yangilandi ✅")
        handle_profile(message, bot)
        
    except Exception as e:
        print(f"Error updating profile: {e}")
        bot.send_message(user_id, "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")


```

## bot/calories.py
```python
import json
from telebot import types
from core.db import db
from core.ai import analyze_food_image
from datetime import datetime

# State for calorie photo
STATE_CALORIE_PHOTO = 10

def handle_calorie_button(message, bot, onboarding_manager):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    # Check premium
    is_premium = False
    if user and user.get('premium_until'):
        try:
            premium_until = datetime.fromisoformat(user['premium_until'])
            if premium_until > datetime.now():
                is_premium = True
        except:
            pass
            
    if not is_premium:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 Premium olish", callback_data="buy_premium"))
        bot.send_message(
            user_id,
            "🔒 **Bu funksiya faqat Premium foydalanuvchilar uchun.**\n\n"
            "Premium obuna orqali siz ovqat rasmini yuborib, uning kaloriyasini aniqlashingiz mumkin.",
            parse_mode="Markdown",
            reply_markup=markup
        )
        return

    # Set state and ask for photo
    onboarding_manager.set_state(user_id, STATE_CALORIE_PHOTO)
    bot.send_message(user_id, "📸 **Ovqat rasmini yuboring.**\n\nMen uni tahlil qilib, kaloriyasini hisoblab beraman.", parse_mode="Markdown")

def handle_food_photo(message, bot, onboarding_manager):
    user_id = message.from_user.id
    
    if onboarding_manager.get_state(user_id) != STATE_CALORIE_PHOTO:
        return

    if not message.photo:
        bot.send_message(user_id, "❌ Iltimos, faqat rasm yuboring.")
        return

    status_msg = bot.send_message(user_id, "⏳ **Tahlil qilinmoqda...**", parse_mode="Markdown")
    
    try:
        # Download photo
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Analyze
        json_result = analyze_food_image(downloaded_file)
        
        if not json_result:
            bot.edit_message_text("❌ Tizimda xatolik yuz berdi. Keyinroq urinib ko'ring.", user_id, status_msg.message_id)
            onboarding_manager.set_state(user_id, 0) # Reset state
            return
            
        try:
            data = json.loads(json_result)
        except json.JSONDecodeError:
            bot.edit_message_text("❌ Noto'g'ri formatdagi javob olindi.", user_id, status_msg.message_id)
            onboarding_manager.set_state(user_id, 0)
            return
            
        if "error" in data:
            bot.edit_message_text("❌ Rasm noto‘g‘ri yoki ovqat aniqlanmadi. Qayta urinib ko‘ring.", user_id, status_msg.message_id)
            # Keep state to allow retry
            return

        # Format output
        items_text = ""
        for item in data.get("items", []):
            items_text += f"• {item.get('name')} — {item.get('grams')} g → {item.get('calories')} kcal\n"
            
        total_calories = data.get("total_calories", 0)
        
        response_text = (
            f"🍽 <b>Kaloriya hisobi:</b>\n\n"
            f"{items_text}\n"
            f"<b>Jami:</b> {total_calories} kcal"
        )
        
        bot.edit_message_text(response_text, user_id, status_msg.message_id, parse_mode="HTML")
        
        # Log to DB
        db.log_calorie_check(user_id, total_calories, json_result)
        
        # Reset state
        onboarding_manager.set_state(user_id, 0)
        
    except Exception as e:
        print(f"ERROR in handle_food_photo: {e}")
        bot.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}", user_id, status_msg.message_id)
        onboarding_manager.set_state(user_id, 0)

```

## bot/admin.py
```python
import os
from telebot import types
from core.db import db
from dotenv import load_dotenv

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
print(f"DEBUG: Loaded ADMIN_ID: {ADMIN_ID}")

def register_handlers(bot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id != ADMIN_ID:
            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton("📊 Statistika"),
            types.KeyboardButton("👥 Foydalanuvchilar ro‘yxati"),
            types.KeyboardButton("📨 Umumiy xabar"),
            types.KeyboardButton("🎯 Segment xabar"),
            types.KeyboardButton("💎 Premium foydalanuvchilar"),
            types.KeyboardButton("🏷 Referallar"),
            types.KeyboardButton("💳 Obunalar")
        )
        bot.send_message(message.chat.id, "👨‍💼 **Admin Panel**", reply_markup=markup, parse_mode="Markdown")
        
    # Register sub handlers
    register_subscription_handlers(bot)

    @bot.message_handler(func=lambda message: "Statistika" in message.text and message.from_user.id == ADMIN_ID)
    def admin_stats(message):
        try:
            stats = db.get_stats()
            
            # Safe retrieval with defaults
            total = stats.get('total', 0)
            active = stats.get('active', 0)
            premium = stats.get('premium', 0)
            gender_stats = stats.get('gender', {})
            goal_stats = stats.get('goal', {})
            
            text = (
                f"📊 **Statistika**\n\n"
                f"👥 Jami foydalanuvchilar: {total}\n"
                f"✅ Faol foydalanuvchilar: {active}\n"
                f"💎 Premium foydalanuvchilar: {premium}\n\n"
                f"👨 Erkaklar: {gender_stats.get('male', 0) + gender_stats.get('Erkak', 0)}\n"
                f"👩 Ayollar: {gender_stats.get('female', 0) + gender_stats.get('Ayol', 0)}\n\n"
                f"⚖️ Ozish: {goal_stats.get('weight_loss', 0) + goal_stats.get('Ozish', 0)}\n"
                f"💪 Massa: {goal_stats.get('mass_gain', 0) + goal_stats.get('Massa olish', 0)}\n"
                f"❤️ Sog‘liq: {goal_stats.get('health', 0) + goal_stats.get('Sog‘liqni tiklash', 0)}\n\n"
                f"🏃 Faollik:\n"
                f"- Kam harakat: {stats.get('activity', {}).get('sedentary', 0)}\n"
                f"- Yengil: {stats.get('activity', {}).get('light', 0)}\n"
                f"- O'rtacha: {stats.get('activity', {}).get('moderate', 0)}\n"
                f"- Faol: {stats.get('activity', {}).get('active', 0)}\n"
                f"- Atlet: {stats.get('activity', {}).get('athlete', 0)}"
            )
            bot.send_message(message.chat.id, text, parse_mode="Markdown")
            
        except Exception as e:
            print(f"ERROR in admin_stats: {e}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)}")

    @bot.message_handler(func=lambda message: "Foydalanuvchilar ro‘yxati" in message.text)
    def admin_user_list(message):
        if message.from_user.id != ADMIN_ID:
            print(f"DEBUG: Unauthorized admin access attempt by {message.from_user.id}")
            return
        
        try:
            # Get last 20 users (assuming ID order roughly correlates with time)
            users = db.get_active_users() # Returns list of (id, name)
            
            if not users:
                bot.send_message(message.chat.id, "👥 Foydalanuvchilar topilmadi.")
                return

            # Sort by ID desc to get newest first
            users.sort(key=lambda x: x[0], reverse=True)
            recent_users = users[:20]
            
            text = "👥 Oxirgi 20 ta foydalanuvchi:\n\n"
            for uid, name in recent_users:
                user_data = db.get_user(uid)
                if not user_data:
                    continue
                    
                is_prem = "💎" if db.is_premium(uid) else ""
                phone = user_data.get('phone', 'N/A')
                goal = user_data.get('goal', 'N/A')
                
                # Clean name to avoid issues
                clean_name = name if name else "Noma'lum"
                
                text += f"🆔 {uid} | {clean_name} | 📱 {phone} | {goal} {is_prem}\n"
                
            bot.send_message(message.chat.id, text)
            
        except Exception as e:
            print(f"Error in admin_user_list: {e}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.message_handler(func=lambda message: "Premium foydalanuvchilar" in message.text)
    def admin_premium_list(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        # This is a bit expensive without a direct DB query, but fine for MVP
        users = db.get_users_by_segment(is_premium=True)
        
        text = f"💎 **Premium Foydalanuvchilar ({len(users)}):**\n\n"
        for uid, name in users[:20]:
            text += f"🆔 `{uid}` | {name}\n"
            
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    @bot.message_handler(func=lambda message: "Referallar" in message.text)
    def admin_referrals(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        top_referrers = db.get_top_referrals(10)
        
        text = "🏷 **TOP 10 Referallar:**\n\n"
        for item in top_referrers:
            text += f"👤 {item['name']} (ID: `{item['id']}`) — {item['count']} ta taklif\n"
            
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    @bot.message_handler(func=lambda message: "Umumiy xabar" in message.text)
    def admin_broadcast_start(message):
        if message.from_user.id != ADMIN_ID:
            return
        
        print(f"DEBUG: Admin broadcast started by {message.from_user.id}")
        try:
            msg = bot.send_message(message.chat.id, "Xabarni yuboring (matn, rasm, video, ovozli xabar):", reply_markup=types.ForceReply())
            bot.register_next_step_handler(msg, process_broadcast, bot, "all")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.message_handler(func=lambda message: "Segment xabar" in message.text)
    def admin_segment_start(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("👨 Erkaklar", callback_data="seg_gender_Erkak"))
        markup.add(types.InlineKeyboardButton("👩 Ayollar", callback_data="seg_gender_Ayol"))
        markup.add(types.InlineKeyboardButton("⚖️ Ozish", callback_data="seg_goal_Ozish"))
        markup.add(types.InlineKeyboardButton("💪 Massa", callback_data="seg_goal_Massa"))
        markup.add(types.InlineKeyboardButton("💎 Premium", callback_data="seg_premium_True"))
        markup.add(types.InlineKeyboardButton("👤 Oddiy", callback_data="seg_premium_False"))
        markup.add(types.InlineKeyboardButton("🪑 Kam harakat", callback_data="seg_activity_sedentary"))
        markup.add(types.InlineKeyboardButton("🏃 O'rtacha", callback_data="seg_activity_moderate"))
        markup.add(types.InlineKeyboardButton("🔥 Atlet", callback_data="seg_activity_athlete"))
        
        bot.send_message(message.chat.id, "Segmentni tanlang:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.reply_to_message and message.from_user.id == ADMIN_ID)
    def admin_reply_to_user(message):
        """Handle admin replying to a user's feedback"""
        try:
            original_text = message.reply_to_message.text or message.reply_to_message.caption
            if not original_text:
                return
            
            # Extract User ID from the original message text
            # Format expected: "👤 Foydalanuvchi: Name (ID: 12345)"
            import re
            match = re.search(r"\(ID: (\d+)\)", original_text)
            
            if match:
                user_id = int(match.group(1))
                reply_text = message.text or "Rasm/Video"
                
                # Send to user
                try:
                    bot.copy_message(user_id, message.chat.id, message.message_id)
                    bot.reply_to(message, f"✅ Xabar foydalanuvchiga (ID: {user_id}) yuborildi.")
                except Exception as e:
                    bot.reply_to(message, f"❌ Yuborishda xatolik: {e}")
            else:
                bot.reply_to(message, "⚠️ Foydalanuvchi ID si topilmadi. Xabar formatini tekshiring.")
                
        except Exception as e:
            print(f"Error in admin reply: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("seg_"))
    def admin_segment_select(call):
        if call.from_user.id != ADMIN_ID:
            return
            
        segment = call.data.split("_")[1:] # ['gender', 'Erkak'] or ['premium', 'True']
        msg = bot.send_message(call.message.chat.id, f"Tanlangan segment: {segment[0]}={segment[1]}. Xabarni yuboring:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_broadcast, bot, segment)

def process_broadcast(message, bot, segment):
    try:
        # Check if user cancelled
        if message.text and message.text.startswith("/"):
            bot.send_message(message.chat.id, "❌ Bekor qilindi.")
            return

        users = []
        if segment == "all":
            users = db.get_active_users()
        else:
            key, value = segment[0], segment[1]
            if key == "gender":
                users = db.get_users_by_segment(gender=value)
            elif key == "goal":
                # Simple fuzzy match for goal
                users = db.get_users_by_segment(goal=value)
            elif key == "premium":
                is_prem = (value == "True")
                users = db.get_users_by_segment(is_premium=is_prem)
            elif key == "activity":
                users = db.get_users_by_segment(activity_level=value)
        
        if not users:
            bot.send_message(message.chat.id, "❌ Foydalanuvchilar topilmadi.")
            return

        count = 0
        blocked = 0
        
        status_msg = bot.send_message(message.chat.id, f"🚀 Xabar yuborish boshlandi... (Jami: {len(users)})")
        
        for i, user in enumerate(users):
            try:
                bot.copy_message(user[0], message.chat.id, message.message_id)
                count += 1
            except Exception as e:
                # If blocked, mark inactive
                if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                    db.set_user_active(user[0], False)
                    blocked += 1
                # print(f"Failed to send to {user[0]}: {e}")
            
            # Update status every 20 users
            if i % 20 == 0:
                try:
                    bot.edit_message_text(f"🚀 Yuborilmoqda... {i}/{len(users)}", message.chat.id, status_msg.message_id)
                except:
                    pass
        
        bot.send_message(message.chat.id, f"✅ Xabar yuborish yakunlandi.\n\n✅ Muvaffaqiyatli: {count}\n🚫 Bloklaganlar: {blocked}")
        
    except Exception as e:
        print(f"Error in process_broadcast: {e}")
        try:
            bot.send_message(message.chat.id, f"❌ Xabar yuborishda xatolik: {e}")
        except:
            pass

# === Subscription Management ===

def register_subscription_handlers(bot):
    @bot.message_handler(func=lambda message: "Obunalar" in message.text and message.from_user.id == ADMIN_ID)
    def admin_subs_start(message):
        msg = bot.send_message(message.chat.id, "Foydalanuvchi ID raqamini yuboring:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_subs_user_id, bot)

    def process_subs_user_id(message, bot):
        try:
            if not message.text.isdigit():
                bot.send_message(message.chat.id, "❌ ID raqam bo'lishi kerak.")
                return
            
            target_id = int(message.text)
            user = db.get_user(target_id)
            
            if not user:
                bot.send_message(message.chat.id, f"❌ Foydalanuvchi topilmadi: {target_id}")
                return
            
            is_prem = db.is_premium(target_id)
            status = "✅ Premium" if is_prem else "❌ Oddiy"
            until = user.get('premium_until', 'Yo‘q')
            
            text = (
                f"👤 **Foydalanuvchi:** {user.get('full_name', 'Noma’lum')}\n"
                f"🆔 ID: `{target_id}`\n"
                f"💎 Status: {status}\n"
                f"📅 Tugash: {until}\n\n"
                "Amalni tanlang:"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("➕ Obuna qo'shish", callback_data=f"sub_add_{target_id}"))
            markup.add(types.InlineKeyboardButton("➖ Obunani o'chirish", callback_data=f"sub_remove_{target_id}"))
            
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
            
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
    def handle_sub_action(call):
        if call.from_user.id != ADMIN_ID:
            return
            
        action, target_id = call.data.split("_")[1], int(call.data.split("_")[2])
        
        if action == "remove":
            db.remove_premium(target_id)
            bot.edit_message_text(
                f"✅ Foydalanuvchi ({target_id}) dan Premium olib tashlandi.",
                call.message.chat.id,
                call.message.message_id
            )
            try:
                bot.send_message(target_id, "❌ Sizning Premium obunangiz admin tomonidan bekor qilindi.")
            except:
                pass
                
        elif action == "add":
            msg = bot.send_message(call.message.chat.id, f"Necha kun qo'shmoqchisiz? (masalan: 30)", reply_markup=types.ForceReply())
            bot.register_next_step_handler(msg, process_subs_days, bot, target_id)

    def process_subs_days(message, bot, target_id):
        try:
            days = int(message.text)
            db.set_premium(target_id, days)
            
            bot.send_message(message.chat.id, f"✅ Foydalanuvchi ({target_id}) ga {days} kun Premium qo'shildi.")
            
            try:
                bot.send_message(target_id, f"🎉 Tabriklaymiz! Admin sizga {days} kunlik Premium obuna sovg'a qildi!")
            except:
                pass
                
        except ValueError:
            bot.send_message(message.chat.id, "❌ Son kiritishingiz kerak.")

```

## bot/workout.py
```python
from core.db import db
from core.ai import ai_generate_workout, ai_generate_menu

def handle_workout_plan(message, bot):
    """Entry point for workout plans - show template menu"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # Show template selection menu
    from bot.templates import show_workout_template_menu
    show_workout_template_menu(message, bot)

def handle_meal_plan(message, bot):
    """Entry point for meal plans - show template menu"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # Show template selection menu
    from bot.templates import show_meal_template_menu
    show_meal_template_menu(message, bot)

def generate_ai_workout(message, bot, user_id=None):
    """Generate AI workout plan (for premium users)"""
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # Check premium status
    if not db.is_premium(user_id):
        bot.send_message(
            user_id,
            "⚠️ Individual AI reja faqat Premium foydalanuvchilar uchun mavjud.\n\n"
            "💎 Premium obuna sotib oling va sizga maxsus reja tayyorlanadi!",
            parse_mode="Markdown"
        )
        return

    msg = bot.send_message(user_id, "⏳ Siz uchun maxsus mashqlar rejasi tuzilmoqda... Biroz kuting.")
    
    # Generate plan
    print(f"DEBUG: Generating workout plan for user {user_id}...")
    plan = ai_generate_workout(user)
    print(f"DEBUG: Plan generated. Length: {len(plan) if plan else 0}")
    
    bot.delete_message(user_id, msg.message_id)
    
    header = "🏋️‍♂️ **Sizning Individual Mashq Rejangiz:**\n\n"
    full_text = header + plan
    
    if len(full_text) > 4000:
        # Split into chunks
        chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
        for chunk in chunks:
            try:
                bot.send_message(user_id, chunk, parse_mode="HTML")
            except Exception:
                # Fallback to plain text if HTML fails
                bot.send_message(user_id, chunk)
    else:
        try:
            bot.send_message(user_id, full_text, parse_mode="HTML")
        except Exception:
            bot.send_message(user_id, full_text)

def generate_ai_meal(message, bot, user_id=None):
    """Generate AI meal plan (for premium users)"""
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # Check premium status
    if not db.is_premium(user_id):
        bot.send_message(
            user_id,
            "⚠️ Individual AI reja faqat Premium foydalanuvchilar uchun mavjud.\n\n"
            "💎 Premium obuna sotib oling va sizga maxsus reja tayyorlanadi!",
            parse_mode="Markdown"
        )
        return

    msg = bot.send_message(user_id, "⏳ Siz uchun maxsus ovqatlanish rejasi tuzilmoqda... Biroz kuting.")
    
    # Generate plan
    plan = ai_generate_menu(user)
    
    bot.delete_message(user_id, msg.message_id)
    
    header = "🍏 <b>Sizning Individual Ovqatlanish Rejangiz:</b>\n\n"
    full_text = header + plan
    
    if len(full_text) > 4000:
        chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
        for chunk in chunks:
            try:
                bot.send_message(user_id, chunk,parse_mode="HTML")
            except Exception:
                bot.send_message(user_id, chunk)
    else:
        try:
            bot.send_message(user_id, full_text, parse_mode="HTML")
        except Exception:
            bot.send_message(user_id, full_text)

```

## bot/reminders.py
```python
import time
import threading
import schedule
from core.db import db

def send_daily_reminders(bot):
    users = db.get_active_users()
    count = 0
    for user in users:
        try:
            user_id = user[0]
            full_name = user[1]
            username = user[2]
            
            name = full_name if full_name else (username if username else "Aziz foydalanuvchi")
            
            msg = f"☀️ Salom {name}! Bugun suv ichdingizmi va mashqlarni qildingizmi? 💧💪\n\n/start tugmasini bosib vazifalarni tekshiring!"
            bot.send_message(user_id, msg)
            count += 1
        except Exception as e:
            print(f"Failed to send reminder to {user[0]}: {e}")
            # Optional: Mark as inactive if blocked
            if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                db.set_user_active(user[0], False)
    
    print(f"Daily reminders sent to {count} users.")

def start_reminder_thread(bot):
    # Schedule daily reminder at 09:00
    schedule.every().day.at("09:00").do(send_daily_reminders, bot)
    
    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=run_schedule, daemon=True)
    thread.start()
    print("✅ Eslatmalar xizmati ishga tushdi (09:00).")

```

## bot/gamification.py
```python
from datetime import datetime
from telebot import types
from core.db import db
from bot.keyboards import gamification_keyboard

def handle_tasks(message, bot):
    user_id = message.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")
    
    log = db.get_daily_log(user_id, today)
    
    # Check if already checked in
    user = db.get_user(user_id)
    checked_in = user.get('last_checkin') == today
    
    status_icon = "✅" if checked_in else "❌"
    
    text = (
        f"📅 **Bugungi vazifalar ({today}):**\n\n"
        "1) 6-8 stakan suv ichish\n"
        "2) 10-15 daqiqa yurish\n"
        "3) 1 blok mashq bajarish\n\n"
        f"Status: {status_icon}\n\n"
        "Vazifalarni bajargan bo‘lsangiz, tugmani bosing:"
    )
    
    markup = types.InlineKeyboardMarkup()
    if not checked_in:
        markup.add(types.InlineKeyboardButton("✅ Vazifani bajardim (+1 ball)", callback_data="task_done"))
    else:
        markup.add(types.InlineKeyboardButton("✅ Bajarildi", callback_data="task_already_done"))
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == "task_done")
    def handle_task_done(call):
        user_id = call.from_user.id
        today = datetime.now().strftime("%Y-%m-%d")
        user = db.get_user(user_id)
        
        # Double check
        if user.get('last_checkin') == today:
            bot.answer_callback_query(call.id, "Bugun allaqachon vazifani bajargansiz! 🙂", show_alert=True)
            return

        # Award points
        points_to_add = 1
        db.add_points(user_id, points_to_add)
        db.update_user_profile(user_id, last_checkin=today)
        
        # Log daily activity
        db.update_daily_log(user_id, today, workout_done=True)
        
        bot.answer_callback_query(call.id, f"Zo‘r! Bugungi vazifa bajarildi, ball qo‘shildi 🎉")
        
        # Update message
        handle_tasks(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "task_already_done")
    def handle_already_done(call):
        bot.answer_callback_query(call.id, "Bugun allaqachon belgilagansiz, ertaga yana kutamiz 🙂", show_alert=True)


```

## bot/feedback.py
```python
import os
from telebot import types
from core.db import db
from bot.keyboards import main_menu_keyboard
from dotenv import load_dotenv

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

def handle_feedback_start(message, bot):
    user_id = message.from_user.id
    msg = bot.send_message(user_id, "Fikringizni yozing:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_feedback, bot)

def process_feedback(message, bot):
    user_id = message.from_user.id
    text = message.text
    
    # If user cancels or sends a command
    if text.startswith("/"):
        bot.send_message(user_id, "Bekor qilindi.", reply_markup=main_menu_keyboard())
        return

    # Save to DB
    db.add_feedback(user_id, text)
    
    # Notify User
    bot.send_message(user_id, "✅ Rahmat! Fikringiz qabul qilindi va jamoamizga yuborildi.", reply_markup=main_menu_keyboard())
    
    # Forward to Admin
    if ADMIN_ID:
        print(f"DEBUG: Attempting to forward feedback to ADMIN_ID: {ADMIN_ID}")
        user = db.get_user(user_id)
        user_name = user.get('full_name') or user.get('username') or "Unknown"
        
        import html
        safe_name = html.escape(str(user_name))
        safe_text = html.escape(str(text))
        
        admin_msg = (
            f"🆕 <b>Yangi feedback keldi!</b>\n"
            f"👤 Foydalanuvchi: {safe_name} (ID: {user_id})\n"
            f"📝 Matn:\n{safe_text}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")
            print("DEBUG: Feedback forwarded successfully.")
        except Exception as e:
            print(f"Failed to forward feedback to admin: {e}")
            bot.send_message(user_id, f"DEBUG: Admin send error: {e}") # Temporary for user to see
    else:
        print("DEBUG: ADMIN_ID is not set or 0.")

def register_handlers(bot):
    pass # Implicitly handled via menu


```

## bot/premium.py
```python
import uuid
import time
import os
from telebot import types
from core.db import db
from bot.keyboards import main_menu_keyboard
from dotenv import load_dotenv

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Payment details (Mock)
PAYMENT_CARDS = {
    "click": "8600 0000 0000 0000 (Click)",
    "payme": "9860 0000 0000 0000 (Payme)",
    "uzum": "4400 0000 0000 0000 (Uzum)"
}

def handle_premium_menu(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        return

    points = user['points']
    is_premium = db.is_premium(user_id)
    
    until_date = "Yo‘q"
    if is_premium and user['is_premium_until']:
        until_date = user['is_premium_until'][:10]
        
    premium_status = "✅ Aktiv" if is_premium else "❌ Yo‘q"
    
    text = (
        f"💎 **Premium Bo'limi**\n\n"
        f"💰 Ballaringiz: **{points}**\n"
        f"🌟 Premium holati: {premium_status}\n"
        f"📅 Premium tugash sanasi: {until_date}\n\n"
        "💎 **Premium tariflar:**\n"
        "• 1 oy: 49 000 so'm\n"
        "• 3 oy: 119 000 so'm\n\n"
        "⚠️ **Diqqat**: Premium obuna to'lovdan keyin avtomatik faollashadi.\n\n"
        "👇 Obuna sotib olish uchun pastdagi tugmalardan birini tanlang:"
    )
    
    markup = types.InlineKeyboardMarkup()
    # Removed free redemption option - only paid options now
    markup.add(types.InlineKeyboardButton("💳 1 oy — 49 000 so'm", callback_data="select_30"))
    markup.add(types.InlineKeyboardButton("💳 3 oy — 119 000 so'm", callback_data="select_90"))
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

def register_handlers(bot):
    # Free redemption option removed - premium now requires payment only
    # @bot.callback_query_handler(func=lambda call: call.data in ["redeem_7"])
    # def handle_redemption(call):
    #     ... (removed)

    @bot.callback_query_handler(func=lambda call: call.data in ["select_30", "select_90"])
    def handle_plan_selection(call):
        provider_token = os.getenv("PAYMENT_PROVIDER_TOKEN")
        
        if not provider_token:
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "⚠️ **To'lov tizimi hozircha sozlanmagan.**\n\n"
                "Iltimos, admin bilan bog'laning yoki keyinroq urinib ko'ring.\n\n"
                "📞 Qayta aloqa: @admin",
                parse_mode="Markdown"
            )
            return
        
        days = 30 if call.data == "select_30" else 90
        amount = 4900000 if call.data == "select_30" else 11900000 # Amount in tiyin (100 tiyin = 1 sum)
        title = f"Premium {days} kun"
        description = f"Fitness Bot Premium obunasi ({days} kun). Barcha imkoniyatlardan foydalaning!"
        payload = f"premium_{days}"
        currency = "UZS"
        prices = [types.LabeledPrice(label=title, amount=amount)]

        bot.send_invoice(
            call.message.chat.id,
            title=title,
            description=description,
            invoice_payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
            start_parameter="premium-sub",
            is_flexible=False
        )
        bot.delete_message(call.message.chat.id, call.message.message_id)

    @bot.pre_checkout_query_handler(func=lambda query: True)
    def checkout(pre_checkout_query):
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):
        user_id = message.from_user.id
        payment = message.successful_payment
        payload = payment.invoice_payload # e.g., premium_30
        
        days = int(payload.split("_")[1])
        amount = payment.total_amount / 100 # Convert back to UZS
        currency = payment.currency
        
        # Create order record
        order_id = f"pay_{payment.provider_payment_charge_id}"
        db.create_order(order_id, user_id, days, amount, currency)
        db.update_order_status(order_id, 'paid')
        
        # Activate Premium
        db.set_premium(user_id, days)
        
        bot.send_message(user_id, f"✅ **To'lov muvaffaqiyatli amalga oshirildi!**\n\nSizga {days} kunlik Premium obuna faollashtirildi. 🎉\nBarcha imkoniyatlardan foydalanishingiz mumkin!", parse_mode="Markdown")
        
        # Notify Admin
        if ADMIN_ID:
            try:
                bot.send_message(ADMIN_ID, f"💰 **Yangi To'lov!**\nUser: {message.from_user.first_name} (ID: {user_id})\nSumma: {amount} {currency}\nTarif: {days} kun")
            except Exception:
                pass

    @bot.callback_query_handler(func=lambda call: call.data == "back_premium")
    def back_to_premium(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_premium_menu(call.message, bot)

    # Admin manual confirm kept just in case
    @bot.message_handler(commands=['confirm_premium'])
    def admin_confirm_premium(message):
        if message.from_user.id != ADMIN_ID:
            return
        try:
            parts = message.text.split()
            order_id = parts[1]
            days = int(parts[2])
            
            order = db.get_order(order_id)
            if not order:
                bot.reply_to(message, "❌ Buyurtma topilmadi.")
                return
            
            db.update_order_status(order_id, 'paid')
            db.set_premium(order['user_id'], days)
            
            bot.reply_to(message, f"✅ To'lov tasdiqlandi! User {order['user_id']} ga {days} kun Premium berildi.")
        except Exception:
            pass

```

## bot/templates.py
```python
import json
import os
from telebot import types
from core.db import db

TEMPLATES_DIR = "templates"

def load_template(category, template_id):
    """Load a template from JSON file"""
    filepath = os.path.join(TEMPLATES_DIR, category, f"{template_id}.json")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def get_workout_templates():
    """Get list of available workout templates"""
    return [
        {"id": "beginner_home", "name": "🏠 Uy mashqlari (Boshlang'ich)", "emoji": "🏠"},
        {"id": "weight_loss", "name": "🔥 Vazn yo'qotish rejasi", "emoji": "🔥"},
        {"id": "muscle_gain", "name": "💪 Mushak massa oshirish", "emoji": "💪"}
    ]

def get_meal_templates():
    """Get list of available meal templates"""
    return [
        {"id": "meal_1500", "name": "🍏 Vazn yo'qotish (1500 kcal)", "emoji": "🍏"},
        {"id": "meal_2000", "name": "🥗 Sog'lom ovqatlanish (2000 kcal)", "emoji": "🥗"},
        {"id": "meal_2500", "name": "💪 Mushak oshirish (2500 kcal)", "emoji": "💪"}
    ]

def show_workout_template_menu(message, bot):
    """Show workout template selection menu"""
    user_id = message.from_user.id
    is_premium = db.is_premium(user_id)
    
    text = (
        "📋 **Mashq rejalari**\n\n"
        "Quyidagi shablon rejalardan birini tanlang:\n\n"
    )
    
    if not is_premium:
        text += "💡 *Individual AI reja uchun Premium obuna kerak*"
    
    markup = types.InlineKeyboardMarkup()
    
    # Add template options
    for template in get_workout_templates():
        markup.add(types.InlineKeyboardButton(
            template["name"],
            callback_data=f"workout_template_{template['id']}"
        ))
    
    # Add AI option for premium users
    if is_premium:
        markup.add(types.InlineKeyboardButton(
            "🤖 Individual AI reja",
            callback_data="workout_ai"
        ))
    else:
        # Upsell premium
        markup.add(types.InlineKeyboardButton(
            "💎 Individual AI reja (Premium)",
            callback_data="upgrade_premium"
        ))
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

def show_meal_template_menu(message, bot):
    """Show meal template selection menu"""
    user_id = message.from_user.id
    is_premium = db.is_premium(user_id)
    
    text = (
        "🍽 **Ovqatlanish rejalari**\n\n"
        "Quyidagi shablon rejalardan birini tanlang:\n\n"
    )
    
    if not is_premium:
        text += "💡 *Individual AI reja uchun Premium obuna kerak*"
    
    markup = types.InlineKeyboardMarkup()
    
    # Add template options
    for template in get_meal_templates():
        markup.add(types.InlineKeyboardButton(
            template["name"],
            callback_data=f"meal_template_{template['id']}"
        ))
    
    # Add AI option for premium users
    if is_premium:
        markup.add(types.InlineKeyboardButton(
            "🤖 Individual AI reja",
            callback_data="meal_ai"
        ))
    else:
        # Upsell premium
        markup.add(types.InlineKeyboardButton(
            "💎 Individual AI reja (Premium)",
            callback_data="upgrade_premium"
        ))
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

def send_template_plan(user_id, category, template_id, bot):
    """Load and send a template plan"""
    template = load_template(category, template_id)
    
    if not template:
        bot.send_message(user_id, "❌ Shablon topilmadi. Iltimos, qaytadan urinib ko'ring.")
        return
    
    plan_text = template["plan"]
    
    # Send the plan
    try:
        if len(plan_text) > 4000:
            chunks = [plan_text[i:i+4000] for i in range(0, len(plan_text), 4000)]
            for chunk in chunks:
                bot.send_message(user_id, chunk, parse_mode="HTML")
        else:
            bot.send_message(user_id, plan_text, parse_mode="HTML")
        
        # Add feedback message
        bot.send_message(
            user_id,
            "\n\n✅ Shablon reja yuborildi!\n\n"
            "💡 Sizga maxsus moslashtir ilgan individual reja kerakmi?\n"
            "💎 Premium obuna oling va AI sizga shaxsiy reja tuzadi!",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending template: {e}")
        bot.send_message(user_id, plan_text)

def register_handlers(bot):
    """Register all template-related callback handlers"""
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("workout_template_"))
    def handle_workout_template(call):
        template_id = call.data.replace("workout_template_", "")
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_template_plan(call.from_user.id, "workouts", template_id, bot)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("meal_template_"))
    def handle_meal_template(call):
        template_id = call.data.replace("meal_template_", "")
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_template_plan(call.from_user.id, "meals", template_id, bot)
    
    @bot.callback_query_handler(func=lambda call: call.data == "upgrade_premium")
    def handle_upgrade_button(call):
        print(f"DEBUG: upgrade_premium button clicked by {call.from_user.id}")
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        from bot.premium import handle_premium_menu
        print(f"DEBUG: Redirecting to premium menu")
        handle_premium_menu(call.message, bot, user_id=call.from_user.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "workout_ai")
    def handle_workout_ai_request(call):
        print(f"DEBUG: workout_ai button clicked by {call.from_user.id}")
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # Import here to avoid circular dependency
        from bot.workout import generate_ai_workout
        print(f"DEBUG: Generating AI workout")
        generate_ai_workout(call.message, bot, user_id=call.from_user.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "meal_ai")
    def handle_meal_ai_request(call):
        print(f"DEBUG: meal_ai button clicked by {call.from_user.id}")
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        from bot.workout import generate_ai_meal
        print(f"DEBUG: Generating AI meal")
        generate_ai_meal(call.message, bot, user_id=call.from_user.id)


```

## bot/referral.py
```python
from core.db import db

def handle_referral(message, bot):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return

    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={user['referral_code']}"
    ref_count = db.get_referral_count(user_id)
    
    text = (
        f"🔗 **Sizning referal havolangiz:**\n{ref_link}\n\n"
        f"👥 Taklif qilgan do‘stlaringiz: {ref_count} ta\n"
        f"💎 Ballaringiz: {user['points']}\n\n"
        "Har bir do‘stingiz uchun +1 ball olasiz. 5 ta do‘stingizni taklif qilsangiz, 7 kunlik Premium bepul beriladi!"
    )
    
    bot.send_message(user_id, text)

```

