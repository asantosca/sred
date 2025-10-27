#!/usr/bin/env python3
"""
Quick test script for password reset flow
Usage: python test_password_reset.py
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_password_reset_flow(email: str):
    """Test the complete password reset flow"""

    print("=" * 60)
    print("Testing Password Reset Flow")
    print("=" * 60)

    # Step 1: Request password reset
    print(f"\n1. Requesting password reset for: {email}")
    response = requests.post(
        f"{BASE_URL}/auth/password-reset/request",
        json={"email": email}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")

    # Step 2: Get token from user (simulate checking email)
    print("\n2. Check MailHog at http://localhost:8025 for the reset email")
    token = input("   Enter the token from the email: ").strip()

    if not token:
        print("   ❌ No token provided. Exiting.")
        return

    # Step 3: Verify token
    print(f"\n3. Verifying token...")
    response = requests.post(
        f"{BASE_URL}/auth/password-reset/verify",
        json={"token": token}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code != 200:
        print("   ❌ Token verification failed!")
        return

    # Step 4: Reset password
    new_password = input("\n4. Enter new password: ").strip() or "NewTestPass123"
    print(f"   Resetting password to: {new_password}")

    response = requests.post(
        f"{BASE_URL}/auth/password-reset/confirm",
        json={
            "token": token,
            "new_password": new_password
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Password reset successful!")
        print(f"   User: {result['user']['email']}")
        print(f"   Access Token: {result['access_token'][:50]}...")
    else:
        print(f"   ❌ Password reset failed!")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return

    # Step 5: Login with new password
    print(f"\n5. Testing login with new password...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": new_password
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Login successful with new password!")
    else:
        print(f"   ❌ Login failed!")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return

    # Step 6: Try to reuse token (should fail)
    print(f"\n6. Testing token reuse (should fail)...")
    response = requests.post(
        f"{BASE_URL}/auth/password-reset/confirm",
        json={
            "token": token,
            "new_password": "AnotherPassword456"
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   ✅ Token reuse correctly prevented!")
    else:
        print(f"   ❌ Token was reused (security issue!)")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


def quick_test_token(token: str, new_password: str = "QuickTest123"):
    """Quick test with an existing token"""

    print(f"\n🔍 Quick Testing Token: {token[:20]}...")

    # Verify
    print("\n1. Verifying token...")
    response = requests.post(
        f"{BASE_URL}/auth/password-reset/verify",
        json={"token": token}
    )
    print(f"   Status: {response.status_code} - {response.json()}")

    if response.status_code != 200:
        return

    # Reset
    print(f"\n2. Resetting password...")
    response = requests.post(
        f"{BASE_URL}/auth/password-reset/confirm",
        json={
            "token": token,
            "new_password": new_password
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Success! New password: {new_password}")
    else:
        print(f"   ❌ Failed: {response.json()}")


if __name__ == "__main__":
    import sys

    print("\n🧪 Password Reset Test Script")
    print("-" * 60)

    # Check if token provided as argument for quick test
    if len(sys.argv) > 1:
        token = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else "QuickTest123"
        quick_test_token(token, password)
    else:
        # Interactive full flow test
        print("\nOptions:")
        print("1. Test full password reset flow")
        print("2. Quick test with existing token")

        choice = input("\nSelect option (1 or 2): ").strip()

        if choice == "1":
            email = input("Enter email address: ").strip()
            if not email:
                print("❌ No email provided")
                sys.exit(1)
            test_password_reset_flow(email)
        elif choice == "2":
            token = input("Enter token: ").strip()
            if not token:
                print("❌ No token provided")
                sys.exit(1)
            password = input("Enter new password (or press Enter for default): ").strip() or "QuickTest123"
            quick_test_token(token, password)
        else:
            print("❌ Invalid choice")
