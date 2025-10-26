# Email Service - Quick Start Guide

## 1. Start MailHog

```bash
docker-compose up -d mailhog
```

## 2. Verify It's Running

Open http://localhost:8025 in your browser. You should see the MailHog interface.

## 3. Test Email Sending

```bash
cd backend
python test_email.py
```

## 4. View Emails

Refresh http://localhost:8025 - you'll see 4 test emails!

## 5. Use in Your Code

```python
from app.services.email import EmailService

email_service = EmailService()

# Send password reset
await email_service.send_password_reset_email(
    to_email="user@example.com",
    reset_token="abc123",
    user_name="John Doe"
)

# Send invitation
await email_service.send_user_invitation_email(
    to_email="newuser@example.com",
    invited_by="Jane Smith",
    company_name="Smith Law",
    invitation_token="invite123"
)

# Send welcome email
await email_service.send_welcome_email(
    to_email="user@example.com",
    user_name="Alice",
    company_name="Johnson Legal"
)
```

## That's It!

All emails go to MailHog at http://localhost:8025

For full documentation, see [email-service-setup.md](./email-service-setup.md)
