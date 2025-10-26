#!/usr/bin/env python3
"""
Test script for email service with MailHog

Run this after starting docker-compose to test email functionality.

Usage:
    python test_email.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.email import EmailService


async def test_email_service():
    """Test the email service with MailHog"""

    print("=" * 60)
    print("BC Legal Tech - Email Service Test")
    print("=" * 60)
    print()

    email_service = EmailService()

    print(f"SMTP Configuration:")
    print(f"  Host: {email_service.smtp_host}")
    print(f"  Port: {email_service.smtp_port}")
    print(f"  From: {email_service.from_email}")
    print()

    # Test 1: Password Reset Email
    print("Test 1: Sending Password Reset Email...")
    success = await email_service.send_password_reset_email(
        to_email="testuser@example.com",
        reset_token="abc123xyz789",
        user_name="John Doe"
    )
    if success:
        print("  ✓ Password reset email sent successfully")
    else:
        print("  ✗ Failed to send password reset email")
    print()

    # Test 2: User Invitation Email
    print("Test 2: Sending User Invitation Email...")
    success = await email_service.send_user_invitation_email(
        to_email="newuser@example.com",
        invited_by="Jane Smith",
        company_name="Smith & Associates Law Firm",
        invitation_token="invite123abc"
    )
    if success:
        print("  ✓ User invitation email sent successfully")
    else:
        print("  ✗ Failed to send user invitation email")
    print()

    # Test 3: Welcome Email
    print("Test 3: Sending Welcome Email...")
    success = await email_service.send_welcome_email(
        to_email="welcomeuser@example.com",
        user_name="Alice Johnson",
        company_name="Johnson Legal Services"
    )
    if success:
        print("  ✓ Welcome email sent successfully")
    else:
        print("  ✗ Failed to send welcome email")
    print()

    # Test 4: Custom Email
    print("Test 4: Sending Custom Email...")
    success = await email_service.send_email(
        to_email="custom@example.com",
        subject="Test Email from BC Legal Tech",
        html_body="<h1>Hello!</h1><p>This is a <strong>test email</strong>.</p>",
        text_body="Hello! This is a test email."
    )
    if success:
        print("  ✓ Custom email sent successfully")
    else:
        print("  ✗ Failed to send custom email")
    print()

    print("=" * 60)
    print("Testing Complete!")
    print()
    print("View emails in MailHog:")
    print("  → http://localhost:8025")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_email_service())
