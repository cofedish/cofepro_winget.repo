"""
Create admin user automatically with default credentials
Run: python create_admin_auto.py
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.config import settings
from app.models import User, UserRole
from app.security import hash_password


async def create_admin_user():
    """Create admin user with default credentials"""
    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # Check if admin already exists
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("Admin user already exists!")
            print(f"Username: {existing_admin.username}")
            print(f"Email: {existing_admin.email}")
            print(f"Role: {existing_admin.role.value}")
            return

        # Create admin with default credentials
        username = "admin"
        email = "admin@example.com"
        password = "admin123"

        print(f"Creating admin user: {username}")
        print(f"Password length: {len(password)} chars, {len(password.encode('utf-8'))} bytes")
        print(f"Password repr: {repr(password)}")

        # Create admin user
        admin = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print("\n" + "=" * 50)
        print("Admin user created successfully!")
        print("=" * 50)
        print(f"Username: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role.value}")
        print(f"ID: {admin.id}")
        print(f"\nPassword: {password}")
        print("\nYou can now login with these credentials.")

    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(create_admin_user())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
