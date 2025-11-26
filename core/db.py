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
            cursor.execute("SELECT telegram_id, full_name FROM users WHERE active = 1")
            users = cursor.fetchall()
            conn.close()
            return users

    def get_users_by_segment(self, gender=None, goal=None, age_min=None, age_max=None, is_premium=None):
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
            
            # Premium count
            cursor.execute("SELECT COUNT(*) FROM users WHERE premium_until > ?", (datetime.now().isoformat(),))
            premium_users = cursor.fetchone()[0]
            
            conn.close()
            return {
                "total": total_users,
                "active": active_users,
                "gender": gender_stats,
                "goal": goal_stats,
                "premium": premium_users
            }

db = Database()
