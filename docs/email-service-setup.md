# Email Service Setup with MailHog

## Overview

SR&ED uses **MailHog** for local email testing during development. MailHog captures all outgoing emails and displays them in a web interface, so you can test email functionality without sending real emails.

## What is MailHog?

MailHog is a local email testing tool that:

- ✅ Runs an SMTP server (port 1025)
- ✅ Provides a web UI to view emails (port 8025)
- ✅ Catches all outgoing emails
- ✅ Requires zero configuration
- ✅ Perfect for development/testing

## Quick Start

### 1. Start MailHog

MailHog is included in the Docker Compose setup:

```bash
docker-compose up -d mailhog
```

Or start all services:

```bash
docker-compose up -d
```

### 2. Verify MailHog is Running

Check that MailHog is running:

```bash
docker ps | grep mailhog
```

You should see:

```
sred-mailhog   mailhog/mailhog:latest   ...   0.0.0.0:1025->1025/tcp, 0.0.0.0:8025->8025/tcp
```

### 3. Access MailHog Web UI

Open in your browser:

```
http://localhost:8025
```

You should see the MailHog interface (it will be empty until you send an email).

### 4. Test Email Service

Run the test script:

```bash
cd backend
python test_email.py
```

This will send 4 test emails:

1. Password reset email
2. User invitation email
3. Welcome email
4. Custom email

### 5. View Test Emails

Go to http://localhost:8025 and you'll see all 4 emails appear in the inbox!

Click on any email to view:

- Subject
- From/To addresses
- HTML preview
- Plain text version
- Email headers
- Raw source

## Email Service Features

### Built-in Email Templates

The email service includes pre-built templates for:

#### 1. Password Reset Email

```python
from app.services.email import EmailService

email_service = EmailService()
await email_service.send_password_reset_email(
    to_email="user@example.com",
    reset_token="abc123",
    user_name="John Doe"
)
```

Features:

- Professional HTML template
- Reset link with token
- Expiration notice (1 hour)
- Plain text fallback

#### 2. User Invitation Email

```python
await email_service.send_user_invitation_email(
    to_email="newuser@example.com",
    invited_by="Jane Smith",
    company_name="Smith Law Firm",
    invitation_token="invite123"
)
```

Features:

- Welcome message from inviter
- Company branding
- Feature highlights
- Invitation link
- Expiration notice (7 days)

#### 3. Welcome Email

```python
await email_service.send_welcome_email(
    to_email="user@example.com",
    user_name="Alice",
    company_name="Johnson Legal"
)
```

Features:

- Personalized welcome
- Getting started guide
- Dashboard link
- Support information

#### 4. Custom Emails

```python
await email_service.send_email(
    to_email="user@example.com",
    subject="Your Subject",
    html_body="<h1>Hello</h1><p>Email body</p>",
    text_body="Plain text version",
    cc=["cc@example.com"],
    bcc=["bcc@example.com"]
)
```

## Configuration

### Development (MailHog)

Default configuration in [backend/app/core/config.py](../backend/app/core/config.py:37-45):

```python
SMTP_HOST: str = "localhost"
SMTP_PORT: int = 1025  # MailHog SMTP port
SMTP_USER: str = ""
SMTP_PASSWORD: str = ""
SMTP_TLS: bool = False
SMTP_SSL: bool = False
EMAIL_FROM: str = "noreply@pendingdomain.com"
EMAIL_FROM_NAME: str = "SR&ED"
```

### Production (Real SMTP)

Override with environment variables:

```bash
# AWS SES Example
SMTP_HOST=email-smtp.ca-central-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your_aws_smtp_username
SMTP_PASSWORD=your_aws_smtp_password
SMTP_TLS=true
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME="Your Company Name"
```

```bash
# SendGrid Example
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_api_key
SMTP_TLS=true
EMAIL_FROM=noreply@yourdomain.com
```

```bash
# Gmail Example (for testing only, not recommended for production)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password  # Use app password, not regular password
SMTP_TLS=true
EMAIL_FROM=your_email@gmail.com
```

## Email Templates

### Customizing Templates

Email templates are in [backend/app/services/email.py](../backend/app/services/email.py).

Each template has:

- **HTML version**: Rich formatting with CSS
- **Plain text version**: Fallback for email clients that don't support HTML

To customize:

1. Edit the template in `email.py`
2. Update both HTML and plain text versions
3. Test with MailHog
4. Commit changes

### Template Best Practices

✅ **DO**:

- Keep HTML simple (many email clients strip complex CSS)
- Always provide plain text fallback
- Use inline CSS (not external stylesheets)
- Test in MailHog before production
- Include unsubscribe links (for marketing emails)
- Use responsive design (mobile-friendly)

❌ **DON'T**:

- Use JavaScript (email clients block it)
- Use external images without fallback text
- Use complex CSS layouts
- Forget to test plain text version
- Include sensitive information in URLs

## Troubleshooting

### MailHog Not Receiving Emails

1. **Check MailHog is running**:

   ```bash
   docker ps | grep mailhog
   ```

2. **Check SMTP connection**:

   ```bash
   telnet localhost 1025
   ```

   Should connect successfully.

3. **Check email service logs**:
   Look for errors in console when sending emails.

4. **Restart MailHog**:
   ```bash
   docker-compose restart mailhog
   ```

### Cannot Access Web UI

1. **Check port 8025 is available**:

   ```bash
   netstat -an | findstr 8025  # Windows
   lsof -i :8025  # Mac/Linux
   ```

2. **Try alternate URL**:

   ```
   http://127.0.0.1:8025
   ```

3. **Check firewall settings**:
   Ensure port 8025 is not blocked.

### Emails Not Formatted Correctly

1. **Check HTML syntax**:
   Use an HTML validator

2. **Test in MailHog**:
   View both HTML and plain text versions

3. **Check inline CSS**:
   Email clients require inline styles

## Production Deployment

### Recommended Email Services

1. **AWS SES** (Amazon Simple Email Service)

   - ✅ Reliable and scalable
   - ✅ Low cost ($0.10 per 1,000 emails)
   - ✅ Good for transactional emails
   - ✅ Requires domain verification

2. **SendGrid**

   - ✅ Easy setup
   - ✅ Good free tier (100 emails/day)
   - ✅ Analytics dashboard
   - ✅ Template management

3. **Postmark**
   - ✅ Fast delivery
   - ✅ Great for transactional emails
   - ✅ Excellent deliverability
   - ✅ Simple API

### Production Checklist

- [ ] Choose email service provider
- [ ] Set up domain verification (SPF, DKIM, DMARC)
- [ ] Configure production SMTP credentials
- [ ] Update email templates with production URLs
- [ ] Add unsubscribe links (for marketing emails)
- [ ] Set up email monitoring/alerts
- [ ] Test with real email addresses
- [ ] Configure bounce/complaint handling
- [ ] Review email sending limits
- [ ] Set up email logging

### Security Best Practices

1. **Never commit SMTP credentials**:

   - Use environment variables
   - Store in secrets manager (AWS Secrets Manager, etc.)

2. **Use TLS/SSL**:

   - Always encrypt email transmission
   - Set `SMTP_TLS=true` or `SMTP_SSL=true`

3. **Implement rate limiting**:

   - Prevent abuse
   - Protect against spam complaints

4. **Monitor bounces**:

   - Track failed deliveries
   - Update email lists

5. **Domain authentication**:
   - Configure SPF records
   - Set up DKIM signing
   - Implement DMARC policy

## Development Workflow

### Adding New Email Templates

1. **Create template function** in `email.py`:

   ```python
   async def send_new_template_email(self, to_email: str, ...):
       html_body = """..."""
       text_body = """..."""
       return await self.send_email(...)
   ```

2. **Test with MailHog**:

   ```bash
   python test_email.py
   ```

3. **View in MailHog UI**:
   http://localhost:8025

4. **Iterate until perfect**

5. **Commit changes**

### Testing Email Flow

Test complete flows:

1. **Password Reset Flow**:

   - Request reset → Email sent → Click link → Reset password

2. **User Invitation Flow**:

   - Admin invites → Email sent → User accepts → Account created

3. **Welcome Email Flow**:
   - User registers → Welcome email sent → User logs in

## Next Steps

Now that email service is set up, you can:

1. ✅ Implement password reset flow (uses email service)
2. ✅ Implement user invitation system (uses email service)
3. ✅ Send welcome emails on registration
4. ✅ Add email notifications for important events

## Resources

- **MailHog GitHub**: https://github.com/mailhog/MailHog
- **MailHog Web UI**: http://localhost:8025 (when running)
- **Email Service Code**: [backend/app/services/email.py](../backend/app/services/email.py)
- **Email Config**: [backend/app/core/config.py](../backend/app/core/config.py)
