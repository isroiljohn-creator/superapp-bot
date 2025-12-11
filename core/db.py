from backend.database import get_sync_db, init_db_sync
from backend.models import User, DailyLog, Plan, Transaction, Feedback, Order, ActivityLog, CalorieLog, WorkoutCache, MenuCache, AdminLog, MenuTemplate, UserMenuLink
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import json

class Database:
    def __init__(self):
        init_db_sync()

    def init_db(self):
        init_db_sync()
        self.check_schema()

    def check_schema(self):
        """Auto-migration to add missing columns"""
        from sqlalchemy import inspect, text
        from backend.database import sync_engine
        
        inspector = inspect(sync_engine)
        columns = [c['name'] for c in inspector.get_columns('users')]
        
        with sync_engine.connect() as conn:
            if 'onboarding_state' not in columns:
                print("Migrating: Adding onboarding_state to users...")
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN onboarding_state INTEGER DEFAULT 0"))
                    conn.commit()
                except Exception as e:
                    print(f"Migration error (onboarding_state): {e}")
            
            if 'onboarding_data' not in columns:
                print("Migrating: Adding onboarding_data to users...")
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN onboarding_data TEXT"))
                    conn.commit()
                except Exception as e:
                    print(f"Migration error (onboarding_data): {e}")

            if 'menu_templates' not in inspector.get_table_names():
                print("Migrating: Creating menu_templates table...")
                MenuTemplate.__table__.create(bind=sync_engine)

            if 'user_menu_links' not in inspector.get_table_names():
                print("Migrating: Creating user_menu_links table...")
                UserMenuLink.__table__.create(bind=sync_engine)

    def reset_db(self):
        from backend.database import sync_engine, Base
        from sqlalchemy import text
        
        # Try to drop with CASCADE for Postgres
        try:
            with sync_engine.connect() as conn:
                conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
                conn.commit()
            print("DEBUG: Schema reset via CASCADE")
        except Exception as e:
            print(f"DEBUG: CASCADE drop failed (likely SQLite), using drop_all: {e}")
            Base.metadata.drop_all(bind=sync_engine)
            
        Base.metadata.create_all(bind=sync_engine)

    def _get_user_pk(self, session, telegram_id):
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        return user.id if user else None

    def log_activity(self, user_id, type, payload):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if pk:
                log = ActivityLog(user_id=pk, type=type, payload=payload)
                session.add(log)

    def get_weight_history(self, user_id, limit=30):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return []
            
            logs = session.query(ActivityLog.ts, ActivityLog.payload)\
                .filter(ActivityLog.user_id == pk, ActivityLog.type == 'weight_update')\
                .order_by(ActivityLog.ts.asc())\
                .all()
            return logs

    def get_checkin_history(self, user_id, days=7):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return []
            
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            logs = session.query(DailyLog.date, DailyLog.workout_done)\
                .filter(DailyLog.user_id == pk, DailyLog.date >= start_date)\
                .order_by(DailyLog.date.asc())\
                .all()
            return logs

    def add_user(self, telegram_id, username, phone, referral_code=None, referrer_id=None):
        with get_sync_db() as session:
            if session.query(User).filter(User.telegram_id == telegram_id).first():
                return True # Already exists
                
            ref_code = referral_code if referral_code else f"r{telegram_id}"
            
            # Resolve referrer_id (telegram_id) to PK
            referrer_pk = None
            if referrer_id:
                referrer_pk = self._get_user_pk(session, referrer_id)
            
            new_user = User(
                telegram_id=telegram_id,
                username=username,
                phone=phone,
                referral_code=ref_code,
                referrer_id=referrer_pk,
                active=True
            )
            session.add(new_user)
            return True

    def update_user_profile(self, user_id, **kwargs):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)

    def get_user(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                # Convert to dict for compatibility
                return {c.name: getattr(user, c.name) for c in user.__table__.columns}
            return None

    def add_points(self, user_id, points):
        with get_sync_db() as session:
            # Atomic update
            session.query(User).filter(User.telegram_id == user_id).update(
                {"points": User.points + points},
                synchronize_session=False
            )

    def get_daily_log(self, user_id, date_str):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return None
            
            log = session.query(DailyLog).filter(DailyLog.user_id == pk, DailyLog.date == date_str).first()
            if log:
                return {c.name: getattr(log, c.name) for c in log.__table__.columns}
            return None

    def update_daily_log(self, user_id, date_str, **kwargs):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return
            
            log = session.query(DailyLog).filter(DailyLog.user_id == pk, DailyLog.date == date_str).first()
            if not log:
                log = DailyLog(user_id=pk, date=date_str)
                session.add(log)
            
            for key, value in kwargs.items():
                if hasattr(log, key):
                    setattr(log, key, value)

    def get_referral_count(self, user_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return 0
            return session.query(User).filter(User.referrer_id == pk).count()

    def set_premium(self, user_id, days):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user: return
            
            now = datetime.now()
            current_until = user.premium_until
            
            if current_until and current_until > now:
                new_until = current_until + timedelta(days=days)
            else:
                new_until = now + timedelta(days=days)
            
            user.premium_until = new_until
            user.is_premium = True

    def is_premium(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user or not user.premium_until:
                return False
            return user.premium_until > datetime.now()

    def get_premium_status(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user: return {"active": False, "type": "none"}
            
            is_active = user.premium_until and user.premium_until > datetime.now()
            
            status_type = "none"
            if is_active:
                if user.auto_renew:
                    status_type = "subscription"
                elif user.trial_used and user.trial_start:
                    try:
                        start = datetime.fromisoformat(user.trial_start) if isinstance(user.trial_start, str) else user.trial_start
                        if datetime.now() < start + timedelta(days=6):
                            status_type = "trial"
                        else:
                            status_type = "paid_fixed"
                    except:
                        status_type = "paid_fixed"
                else:
                    status_type = "paid_fixed"
                    
            return {
                "active": is_active,
                "type": status_type,
                "until": user.premium_until.isoformat() if user.premium_until else None,
                "auto_renew": user.auto_renew
            }

    def remove_premium(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.is_premium = False
                user.premium_until = None

    def add_feedback(self, user_id, message):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if pk:
                fb = Feedback(user_id=pk, message=message)
                session.add(fb)

    def create_order(self, order_id, user_id, days, amount, currency='UZS'):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if pk:
                order = Order(
                    order_id=order_id, user_id=pk, days=days, 
                    amount=amount, currency=currency, status='pending'
                )
                session.add(order)

    def update_order_status(self, order_id, status):
        with get_sync_db() as session:
            order = session.query(Order).filter(Order.order_id == order_id).first()
            if order:
                order.status = status

    def get_order(self, order_id):
        with get_sync_db() as session:
            order = session.query(Order).filter(Order.order_id == order_id).first()
            if order:
                return {c.name: getattr(order, c.name) for c in order.__table__.columns}
            return None

    def get_all_users(self):
        with get_sync_db() as session:
            users = session.query(User.telegram_id, User.full_name).all()
            return users

    def get_active_users(self):
        with get_sync_db() as session:
            users = session.query(User.telegram_id, User.full_name, User.username).filter(User.active == True).all()
            return users

    def get_users_paginated(self, page=1, page_size=20):
        with get_sync_db() as session:
            offset = (page - 1) * page_size
            
            # Get total count
            total_count = session.query(User).count()
            
            # Get paginated users
            # Order by ID desc (newest first)
            users = session.query(User).order_by(User.id.desc()).limit(page_size).offset(offset).all()
            
            # Convert to dicts for safety
            users_list = []
            for user in users:
                users_list.append({
                    "id": user.id,
                    "telegram_id": user.telegram_id,
                    "full_name": user.full_name,
                    "username": user.username,
                    "phone": user.phone,
                    "goal": user.goal,
                    "premium_until": user.premium_until
                })
                
            return users_list, total_count

    def get_users_by_segment(self, gender=None, goal=None, activity_level=None, age_min=None, age_max=None, is_premium=None):
        with get_sync_db() as session:
            query = session.query(User.telegram_id, User.full_name, User.username).filter(User.active == True)
            
            if gender: query = query.filter(User.gender == gender)
            if goal: query = query.filter(User.goal.like(f"%{goal}%"))
            if activity_level: query = query.filter(User.activity_level == activity_level)
            if age_min is not None: query = query.filter(User.age >= age_min)
            if age_max is not None: query = query.filter(User.age <= age_max)
            
            if is_premium is not None:
                now = datetime.now()
                if is_premium:
                    query = query.filter(User.premium_until > now)
                else:
                    query = query.filter(or_(User.premium_until == None, User.premium_until <= now))
            
            return query.all()

    def get_top_users(self, limit=20):
        with get_sync_db() as session:
            users = session.query(User.full_name, User.points)\
                .order_by(User.points.desc())\
                .limit(limit).all()
            return users
            
    def get_top_referrals(self, limit=10):
        with get_sync_db() as session:
            # Group by referrer_id and count
            # referrer_id is a PK to User.id
            # We want to show the referrer's name
            
            # Subquery to count referrals
            stmt = session.query(
                User.referrer_id, func.count('*').label('count')
            ).filter(User.referrer_id != None).group_by(User.referrer_id).subquery()
            
            # Join with User to get name
            results = session.query(User.full_name, User.telegram_id, stmt.c.count)\
                .join(stmt, User.id == stmt.c.referrer_id)\
                .order_by(stmt.c.count.desc())\
                .limit(limit).all()
                
            return [{"name": r[0], "id": r[1], "count": r[2]} for r in results]

    def set_user_active(self, user_id, active=True):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.active = active
            
    def export_csv(self):
        with get_sync_db() as session:
            users = session.query(User).all()
            if not users: return ""
            
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            
            columns = [c.name for c in User.__table__.columns]
            writer.writerow(columns)
            
            for user in users:
                writer.writerow([getattr(user, c) for c in columns])
                
            return output.getvalue()

    def get_stats(self):
        with get_sync_db() as session:
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.active == True).count()
            
            gender_stats = dict(session.query(User.gender, func.count(User.id)).group_by(User.gender).all())
            goal_stats = dict(session.query(User.goal, func.count(User.id)).group_by(User.goal).all())
            activity_stats = dict(session.query(User.activity_level, func.count(User.id)).group_by(User.activity_level).all())
            
            premium_users = session.query(User).filter(User.premium_until > datetime.now()).count()
            
            return {
                "total": total_users,
                "active": active_users,
                "gender": gender_stats,
                "goal": goal_stats,
                "activity": activity_stats,
                "premium": premium_users
            }

    def check_calorie_limit(self, user_id):
        if self.is_premium(user_id):
            return True, "premium"
            
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user: return False, "user_not_found"
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            if user.calorie_last_use_date != today:
                return True, "free_daily"
            
            uses = user.calorie_daily_uses or 0
            if uses < 3:
                return True, "free_daily"
                
            return False, "limit_reached"

    def increment_calorie_usage(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user: return
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            if user.calorie_last_use_date != today:
                user.calorie_last_use_date = today
                user.calorie_daily_uses = 1
            else:
                user.calorie_daily_uses = (user.calorie_daily_uses or 0) + 1

    def log_calorie_check(self, user_id, total_kcal, json_data):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if pk:
                log = CalorieLog(user_id=pk, total_kcal=total_kcal, json_data=json_data)
                session.add(log)

    def complete_onboarding(self, telegram_id, username, profile_data, referrer_id=None):
        with get_sync_db() as session:
            try:
                # 1. Create or Get User
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if not user:
                    ref_code = f"r{telegram_id}"
                    
                    # Resolve referrer
                    referrer_pk = None
                    if referrer_id:
                        ref_user = session.query(User).filter(User.telegram_id == referrer_id).first()
                        if ref_user:
                            referrer_pk = ref_user.id

                    user = User(
                        telegram_id=telegram_id,
                        username=username,
                        referral_code=ref_code,
                        referrer_id=referrer_pk,
                        active=True,
                        created_at=datetime.utcnow()
                    )
                    session.add(user)
                    session.flush() # Ensure user is attached
                
                # 2. Update Profile Data
                for key, value in profile_data.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                # 3. Activate Trial (5 days)
                now = datetime.now()
                user.premium_until = now + timedelta(days=5)
                user.is_premium = True
                user.trial_start = now.isoformat()
                user.trial_used = 1
                
                # 4. Award Referral Points
                if user.referrer_id:
                    referrer = session.query(User).filter(User.id == user.referrer_id).first()
                    if referrer:
                        referrer.points = (referrer.points or 0) + 1
                        
                return True
            except Exception as e:
                print(f"DB Error in complete_onboarding: {e}")
                raise e

    def get_weekly_stats(self, user_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return None
            
            # 1. Get User Streaks
            user = session.query(User).filter(User.id == pk).first()
            streaks = {
                "water": user.streak_water or 0,
                "sleep": user.streak_sleep or 0,
                "mood": user.streak_mood or 0
            }
            
            # 2. Get Last 7 Days Logs
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            logs = session.query(DailyLog).filter(DailyLog.user_id == pk, DailyLog.date >= start_date).all()
            
            if not logs:
                return {"has_data": False}
                
            # 3. Aggregate Data
            stats = {
                "has_data": True,
                "days_tracked": len(logs),
                "water_days": sum(1 for log in logs if log.water_drank),
                "workouts": sum(1 for log in logs if log.workout_done),
                "avg_sleep": 0,
                "moods": {},
                "streaks": streaks
            }
            
            total_sleep = sum(log.sleep_hours for log in logs if log.sleep_hours)
            sleep_count = sum(1 for log in logs if log.sleep_hours > 0)
            if sleep_count > 0:
                stats["avg_sleep"] = round(total_sleep / sleep_count, 1)
                
            for log in logs:
                if log.mood:
                    stats["moods"][log.mood] = stats["moods"].get(log.mood, 0) + 1
                    
            return stats

    def get_todays_points_breakdown(self, user_id):
        default_breakdown = {
            "water": 0,
            "steps": 0,
            "sleep": 0,
            "mood": 0,
            "total": 0
        }
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return default_breakdown
            
            today = datetime.now().strftime("%Y-%m-%d")
            log = session.query(DailyLog).filter(DailyLog.user_id == pk, DailyLog.date == today).first()
            
            breakdown = default_breakdown.copy()
            
            if log:
                # Re-calculate points based on log data (since we don't store points per log item explicitly yet)
                # This is an approximation based on rules
                if log.water_drank or (log.water_ml and log.water_ml >= 2500):
                    breakdown["water"] = 1
                
                if log.steps and log.steps >= 10000:
                    breakdown["steps"] = (log.steps // 10000) * 5
                    
                if log.sleep_hours and log.sleep_hours >= 8:
                    breakdown["sleep"] = 2
                    
                if log.mood == 'good':
                    breakdown["mood"] = 1
                    
            breakdown["total"] = sum(breakdown.values())
            return breakdown

    def redeem_points(self, user_id, cost, reward_type, reward_value):
        with get_sync_db() as session:
            # Atomic check and deduct
            # Returns number of rows updated (1 if success, 0 if condition failed)
            rows = session.query(User).filter(
                User.telegram_id == user_id, 
                User.points >= cost
            ).update(
                {"points": User.points - cost}, 
                synchronize_session=False
            )
            
            if rows == 0:
                return False, "Ballar yetarli emas"
            
            # Fetch user to grant reward (points already deducted in DB, but session object might be stale if we used synchronize_session=False)
            # We need to refresh or just query again
            user = session.query(User).filter(User.telegram_id == user_id).first()
            
            # Grant Reward
            if reward_type == "premium_days":
                days = int(reward_value)
                now = datetime.now()
                current_until = user.premium_until
                
                if current_until and current_until > now:
                    new_until = current_until + timedelta(days=days)
                else:
                    new_until = now + timedelta(days=days)
                
                user.premium_until = new_until
                user.is_premium = True
                
            return True, "Muvaffaqiyatli"

    def update_streak(self, user_id, type):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                if type == 'water':
                    user.streak_water = (user.streak_water or 0) + 1
                elif type == 'sleep':
                    user.streak_sleep = (user.streak_sleep or 0) + 1
                elif type == 'mood':
                    user.streak_mood = (user.streak_mood or 0) + 1

    # --- Persistent Onboarding Methods ---
    def get_onboarding_state(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                return user.onboarding_state or 0
            return 0

    def set_onboarding_state(self, user_id, state):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.onboarding_state = state
            else:
                # Create user if not exists (partial user for onboarding)
                # We need to be careful here. Usually we create user on /start or first contact.
                # Let's assume user exists or create minimal user.
                # For now, let's assume user is created at start_onboarding.
                pass

    def get_onboarding_data(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user and user.onboarding_data:
                try:
                    return json.loads(user.onboarding_data)
                except:
                    return {}
            return {}

    def update_onboarding_data(self, user_id, key, value):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                data = {}
                if user.onboarding_data:
                    try:
                        data = json.loads(user.onboarding_data)
                    except:
                        pass
                data[key] = value
                user.onboarding_data = json.dumps(data)

    def clear_onboarding_state(self, user_id):
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.onboarding_state = 0
                user.onboarding_data = "{}"

    def ensure_user_exists(self, user_id, username=None):
        """Ensures a user record exists for onboarding."""
        with get_sync_db() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                user = User(telegram_id=user_id, username=username, active=True)
                session.add(user)
                return True
            return False

    # --- Monthly Menu Logic ---

    def get_menu_template(self, profile_key):
        with get_sync_db() as session:
            template = session.query(MenuTemplate).filter(MenuTemplate.profile_key == profile_key).first()
            if template:
                return {
                    "id": template.id,
                    "menu_json": template.menu_json,
                    "shopping_list_json": template.shopping_list_json
                }
            return None

    def delete_menu_template(self, profile_key):
        from sqlalchemy import text
        try:
            with self.ensure_sync_connection() as conn:
                # 1. Find Template ID first
                res = conn.execute(
                    text("SELECT id FROM menu_templates WHERE profile_key = :pk"),
                    {"pk": profile_key}
                ).fetchone()
                
                if res:
                    template_id = res[0]
                    # 2. Delete Manual Links (Manual Cascade)
                    conn.execute(
                        text("DELETE FROM user_menu_links WHERE menu_template_id = :tid"),
                        {"tid": template_id}
                    )
                    
                    # 3. Delete Template
                    conn.execute(
                        text("DELETE FROM menu_templates WHERE id = :tid"),
                        {"tid": template_id}
                    )
                    conn.commit()
                    return True
                return False
        except Exception as e:
            print(f"Error deleting menu template: {e}")
            return False

    def update_menu_template_content(self, profile_key, menu_json, shopping_list_json):
        from backend.models import MenuTemplate
        try:
            with get_sync_db() as session:
                template = session.query(MenuTemplate).filter(MenuTemplate.profile_key == profile_key).first()
                if template:
                    template.menu_json = menu_json
                    template.shopping_list_json = shopping_list_json
                    # Update timestamp if you had updated_at column, but we don't.
                    session.commit()
                    return template.id
                return None
        except Exception as e:
            print(f"Error updating menu template: {e}")
            return None

    def create_menu_template(self, profile_key, menu_json, shopping_list_json):
        with get_sync_db() as session:
            template = MenuTemplate(
                profile_key=profile_key,
                menu_json=menu_json,
                shopping_list_json=shopping_list_json
            )
            session.add(template)
            session.commit()
            return template.id

    def get_user_menu_link(self, user_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return None
            
            link = session.query(UserMenuLink).filter(
                UserMenuLink.user_id == pk,
                UserMenuLink.is_active == True
            ).first()
            
            if link:
                menu = session.query(MenuTemplate).filter(MenuTemplate.id == link.menu_template_id).first()
                if not menu: return None
                
                return {
                    "id": link.id,
                    "menu_template_id": link.menu_template_id,
                    "current_day_index": link.current_day_index,
                    "start_date": link.start_date,
                    "menu_json": menu.menu_json,
                    "shopping_list_json": menu.shopping_list_json
                }
            return None

    def create_user_menu_link(self, user_id, template_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return
            
            # Deactivate old links
            session.query(UserMenuLink).filter(UserMenuLink.user_id == pk).update({"is_active": False})
            
            link = UserMenuLink(
                user_id=pk,
                menu_template_id=template_id,
                current_day_index=1,
                is_active=True
            )
            session.add(link)
            session.commit()

    def update_menu_day(self, user_id, new_day_index):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return 1
            
            link = session.query(UserMenuLink).filter(
                UserMenuLink.user_id == pk,
                UserMenuLink.is_active == True
            ).first()
            
            if link:
                new_day_index = max(1, min(30, new_day_index))
                link.current_day_index = new_day_index
                session.commit()
                return new_day_index
            return 1

db = Database()

