#!/usr/bin/env python3
"""
Test authentication flow to debug login issues
Run: docker compose exec backend python test_auth.py
"""
import asyncio
from sqlalchemy import select
from app.database import engine
from app.models import User
from app.security import create_access_token, decode_token, authenticate_user, hash_password, verify_password
from app.config import settings
from datetime import timedelta


async def test_authentication():
    """Test full authentication flow"""
    print("=" * 60)
    print("AUTHENTICATION FLOW TEST")
    print("=" * 60)

    # Check settings
    print(f"\n1. Configuration:")
    print(f"   JWT_SECRET (first 10 chars): {settings.jwt_secret[:10]}...")
    print(f"   JWT_SECRET length: {len(settings.jwt_secret)} chars")
    print(f"   JWT_ALGORITHM: {settings.jwt_algorithm}")
    print(f"   Environment: {settings.environment}")

    # Get user
    print(f"\n2. Fetching admin user...")
    async with engine.connect() as conn:
        result = await conn.execute(select(User).where(User.username == 'admin'))
        row = result.fetchone()

        if not row:
            print("   ❌ Admin user not found in database!")
            return

        user_id, username, email, password_hash, role, is_active = row.id, row.username, row.email, row.password_hash, row.role, row.is_active
        print(f"   ✓ User found:")
        print(f"     - ID: {user_id}")
        print(f"     - Username: {username}")
        print(f"     - Email: {email}")
        print(f"     - Role: {role}")
        print(f"     - Active: {is_active}")
        print(f"     - Password hash (first 20 chars): {password_hash[:20]}...")

    # Test password verification
    print(f"\n3. Testing password verification...")
    test_password = "admin123"
    is_valid = verify_password(test_password, password_hash)
    print(f"   Password '{test_password}' is valid: {'✓ YES' if is_valid else '❌ NO'}")

    if not is_valid:
        print(f"   Testing what the password hash was generated from...")
        test_hash = hash_password(test_password)
        print(f"   New hash for same password: {test_hash[:20]}...")
        print(f"   Note: Hashes are different each time (bcrypt salt)")

    # Create token
    print(f"\n4. Creating JWT token...")
    token = create_access_token(
        data={"sub": user_id, "role": str(role)},
        expires_delta=timedelta(minutes=30)
    )
    print(f"   Token (first 50 chars): {token[:50]}...")
    print(f"   Full token length: {len(token)} chars")

    # Decode token
    print(f"\n5. Decoding JWT token...")
    try:
        payload = decode_token(token)
        print(f"   ✓ Token decoded successfully:")
        print(f"     - Subject (user_id): {payload.get('sub')}")
        print(f"     - Role: {payload.get('role')}")
        print(f"     - Expiration: {payload.get('exp')}")
    except Exception as e:
        print(f"   ❌ Error decoding token: {e}")
        return

    # Test authenticate_user
    print(f"\n6. Testing authenticate_user()...")
    async with engine.begin() as conn:
        # Create a session-like object
        from sqlalchemy.ext.asyncio import AsyncSession
        session = AsyncSession(bind=conn, expire_on_commit=False)

        try:
            authenticated_user = await authenticate_user(session, 'admin', 'admin123')
            if authenticated_user:
                print(f"   ✓ Authentication successful:")
                print(f"     - User: {authenticated_user.username}")
                print(f"     - Role: {authenticated_user.role}")
            else:
                print(f"   ❌ Authentication failed (returned None)")
        except Exception as e:
            print(f"   ❌ Authentication error: {e}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_authentication())
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
