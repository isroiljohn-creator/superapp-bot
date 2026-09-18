"""python -m app.cli create-admin EMAIL   (password is prompted, or read from HIRELY_NEW_ADMIN_PASSWORD)"""
import asyncio
import getpass
import os
import sys

from sqlalchemy import select

from .db import dispose, sessionmaker
from .models import Admin
from .security import hash_password


async def create_admin(email: str, password: str) -> None:
    if len(password) < 10:
        raise SystemExit("password must be at least 10 characters")
    async with sessionmaker()() as db:
        admin = (await db.execute(select(Admin).where(Admin.email == email.lower()))).scalar_one_or_none()
        if admin:
            admin.password_hash, admin.is_active = hash_password(password), True
            print(f"updated {email}")
        else:
            db.add(Admin(email=email.lower(), password_hash=hash_password(password)))
            print(f"created {email}")
        await db.commit()
    await dispose()


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] != "create-admin":
        raise SystemExit(__doc__)
    pw = os.environ.get("HIRELY_NEW_ADMIN_PASSWORD") or getpass.getpass("Password: ")
    asyncio.run(create_admin(sys.argv[2], pw))


if __name__ == "__main__":
    main()
