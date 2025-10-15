"""
Create admin user script
Run: python create_admin.py
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.config import settings
from app.models import User, UserRole
from app.security import hash_password


async def create_admin_user():
    """Create admin user"""
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

        # Get input
        print("Create Admin User")
        print("-" * 50)

        username = input("Username (default: admin): ").strip() or "admin"
        email = input("Email (default: admin@example.com): ").strip() or "admin@example.com"
        password = input("Password (default: admin123): ").strip() or "admin123"

        if len(password) < 8:
            print("Error: Password must be at least 8 characters long")
            return

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
        print("\nYou can now login with these credentials.")

    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(create_admin_user())
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
