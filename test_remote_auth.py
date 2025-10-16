#!/usr/bin/env python3
"""
Test authentication on remote server
"""
import requests
import json

BASE_URL = "https://cofemon.online/api"

print("=" * 60)
print("TESTING REMOTE AUTHENTICATION")
print("=" * 60)

# Step 1: Login
print("\n1. Testing login...")
try:
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123"},
        timeout=10
    )
    print(f"   Status: {login_response.status_code}")

    if login_response.status_code == 200:
        login_data = login_response.json()
        print(f"   [OK] Login successful")
        print(f"   Access token (first 50 chars): {login_data['access_token'][:50]}...")
        access_token = login_data['access_token']
    else:
        print(f"   [FAIL] Login failed: {login_response.text}")
        exit(1)
except Exception as e:
    print(f"   [ERROR] Error: {e}")
    exit(1)

# Step 2: Get current user
print("\n2. Testing /auth/me...")
try:
    me_response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    )
    print(f"   Status: {me_response.status_code}")

    if me_response.status_code == 200:
        user_data = me_response.json()
        print(f"   [OK] User info retrieved:")
        print(f"   {json.dumps(user_data, indent=4)}")
    else:
        print(f"   [FAIL] Failed to get user info:")
        print(f"   Response: {me_response.text}")
        print(f"\n   This means backend cannot decode the token!")
        print(f"   Possible reasons:")
        print(f"   - Backend not rebuilt with latest code")
        print(f"   - JWT_SECRET mismatch")
        print(f"   - Error in decode_token() function")
except Exception as e:
    print(f"   [ERROR] Error: {e}")
    exit(1)

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
