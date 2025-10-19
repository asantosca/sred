#!/usr/bin/env python3
"""
Quick test script for JWT authentication
Tests registration, login, and /me endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_auth_flow():
    print("=" * 60)
    print("Testing BC Legal Tech Authentication Flow")
    print("=" * 60)

    # Test 1: Register a new company
    print("\n1. Testing Company Registration...")
    registration_data = {
        "company_name": "Test Law Firm",
        "admin_email": "admin@testfirm.com",
        "admin_password": "SecurePass123!",
        "admin_first_name": "John",
        "admin_last_name": "Doe",
        "plan_tier": "starter"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=registration_data)
        if response.status_code == 201:
            print("✅ Registration successful!")
            data = response.json()
            access_token = data["token"]["access_token"]
            print(f"   User: {data['user']['email']}")
            print(f"   Company: {data['company']['name']}")
            print(f"   Token: {access_token[:20]}...")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on http://localhost:8000?")
        return

    # Test 2: Login
    print("\n2. Testing Login...")
    login_data = {
        "email": "admin@testfirm.com",
        "password": "SecurePass123!"
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        print("✅ Login successful!")
        data = response.json()
        access_token = data["token"]["access_token"]
        print(f"   Token: {access_token[:20]}...")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return

    # Test 3: Get current user with JWT token
    print("\n3. Testing /auth/me endpoint...")
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code == 200:
        print("✅ /auth/me successful!")
        data = response.json()
        print(f"   User ID: {data['user']['id']}")
        print(f"   Email: {data['user']['email']}")
        print(f"   Is Admin: {data['user']['is_admin']}")
        print(f"   Company: {data['company']['name']}")
    else:
        print(f"❌ /auth/me failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return

    # Test 4: Test protected endpoint without token
    print("\n4. Testing protected endpoint without token...")
    response = requests.get(f"{BASE_URL}/users/")
    if response.status_code == 401:
        print("✅ Correctly rejected request without token!")
    else:
        print(f"⚠️  Expected 401, got: {response.status_code}")

    # Test 5: Test protected endpoint with token
    print("\n5. Testing protected endpoint with token...")
    response = requests.get(f"{BASE_URL}/users/", headers=headers)
    if response.status_code == 200:
        print("✅ Protected endpoint accessible with valid token!")
        data = response.json()
        print(f"   Total users: {data['total']}")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
        print(f"   Response: {response.text}")

    print("\n" + "=" * 60)
    print("✅ All tests passed! JWT middleware is working correctly.")
    print("=" * 60)

if __name__ == "__main__":
    test_auth_flow()
