import asyncio
from db.database import engine
from sqlalchemy import text

async def main():
    try:
        async with engine.connect() as conn:
            print("Successfully connected to DB!")
            
            # Count users
            res = await conn.execute(text("SELECT COUNT(*) FROM users"))
            print(f"Total Users in DB: {res.scalar()}")
            
            # Find duplicate telegram_ids
            res = await conn.execute(text("""
                SELECT telegram_id, COUNT(*) 
                FROM users 
                GROUP BY telegram_id 
                HAVING COUNT(*) > 1
            """))
            dupes = res.fetchall()
            print(f"\nNumber of duplicate telegram_ids: {len(dupes)}")
            for d in dupes:
                print(f"Duplicate TG ID: {d[0]}, Count: {d[1]}")
                
            # Find duplicate phone numbers
            res = await conn.execute(text("""
                SELECT phone, COUNT(*) 
                FROM users 
                WHERE phone IS NOT NULL
                GROUP BY phone 
                HAVING COUNT(*) > 1
            """))
            phone_dupes = res.fetchall()
            print(f"\nNumber of duplicate phones: {len(phone_dupes)}")
            for pd in phone_dupes:
                print(f"Duplicate Phone: {pd[0]}, Count: {pd[1]}")
                
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
