#!/usr/bin/env python3
"""
Test script for user profile update endpoints

Tests:
1. Get user profile (GET /api/v1/users/me)
2. Update user profile (PATCH /api/v1/users/me)
3. Avatar upload (POST /api/v1/users/me/avatar)
"""

import requests
import json
from pathlib import Path
import io
from PIL import Image

BASE_URL = "http://localhost:8000/api/v1"

def create_test_image():
    """Create a simple test image in memory"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def test_user_profile():
    """Test user profile endpoints"""

    print("=" * 60)
    print("USER PROFILE UPDATE TEST")
    print("=" * 60)

    # Step 1: Login to get access token
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "admin@testcompany.com",
            "password": "TestPass123"
        }
    )

    if login_response.status_code != 200:
        print(f"   ❌ Login failed!")
        print(f"   Status: {login_response.status_code}")
        print(f"   Response: {json.dumps(login_response.json(), indent=2)}")
        return

    login_data = login_response.json()
    access_token = login_data['token']['access_token']
    print(f"   ✅ Login successful!")
    print(f"   User: {login_data['user']['email']}")
    print(f"   Token: {access_token[:50]}...")

    # Headers with authorization
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Step 2: Get current profile
    print("\n2. Getting current profile...")
    profile_response = requests.get(
        f"{BASE_URL}/users/me",
        headers=headers
    )

    print(f"   Status: {profile_response.status_code}")
    if profile_response.status_code == 200:
        profile = profile_response.json()
        print(f"   ✅ Profile retrieved!")
        print(f"   Email: {profile['email']}")
        print(f"   Name: {profile.get('first_name', 'N/A')} {profile.get('last_name', 'N/A')}")
        print(f"   Is Admin: {profile['is_admin']}")
        print(f"   Is Active: {profile['is_active']}")
    else:
        print(f"   ❌ Failed to get profile!")
        print(f"   Response: {json.dumps(profile_response.json(), indent=2)}")
        return

    # Step 3: Update profile
    print("\n3. Updating profile...")
    update_response = requests.patch(
        f"{BASE_URL}/users/me",
        headers=headers,
        json={
            "first_name": "Updated",
            "last_name": "Name"
        }
    )

    print(f"   Status: {update_response.status_code}")
    if update_response.status_code == 200:
        updated_profile = update_response.json()
        print(f"   ✅ Profile updated!")
        print(f"   New Name: {updated_profile['first_name']} {updated_profile['last_name']}")
    else:
        print(f"   ❌ Failed to update profile!")
        print(f"   Response: {json.dumps(update_response.json(), indent=2)}")

    # Step 4: Try to update email to existing one (should fail)
    print("\n4. Testing email validation (should fail)...")
    bad_email_response = requests.patch(
        f"{BASE_URL}/users/me",
        headers=headers,
        json={
            "email": "admin@testcompany.com"  # Same email
        }
    )

    print(f"   Status: {bad_email_response.status_code}")
    if bad_email_response.status_code == 400:
        print(f"   ✅ Correctly rejected duplicate email")
    else:
        print(f"   ⚠️  Unexpected response")
        print(f"   Response: {json.dumps(bad_email_response.json(), indent=2)}")

    # Step 5: Upload avatar
    print("\n5. Uploading avatar image...")

    # Create a test image
    test_image = create_test_image()

    files = {
        'file': ('test_avatar.png', test_image, 'image/png')
    }

    avatar_response = requests.post(
        f"{BASE_URL}/users/me/avatar",
        headers=headers,
        files=files
    )

    print(f"   Status: {avatar_response.status_code}")
    if avatar_response.status_code == 200:
        avatar_data = avatar_response.json()
        print(f"   ✅ Avatar uploaded!")
        print(f"   Message: {avatar_data['message']}")
        print(f"   Avatar URL length: {len(avatar_data['avatar_url'])} characters")
        print(f"   Avatar URL preview: {avatar_data['avatar_url'][:100]}...")
    else:
        print(f"   ❌ Failed to upload avatar!")
        print(f"   Response: {json.dumps(avatar_response.json(), indent=2)}")

    # Step 6: Try invalid file type
    print("\n6. Testing file type validation (should fail)...")

    bad_file = io.BytesIO(b"This is not an image")
    files = {
        'file': ('test.txt', bad_file, 'text/plain')
    }

    bad_avatar_response = requests.post(
        f"{BASE_URL}/users/me/avatar",
        headers=headers,
        files=files
    )

    print(f"   Status: {bad_avatar_response.status_code}")
    if bad_avatar_response.status_code == 400:
        print(f"   ✅ Correctly rejected invalid file type")
        print(f"   Error: {bad_avatar_response.json()['detail']}")
    else:
        print(f"   ⚠️  Unexpected response")

    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_user_profile()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server")
        print("   Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
