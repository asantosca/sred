# app/services/email.py - Email service for BC Legal Tech

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service supporting both development (MailHog) and production (real SMTP)"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.smtp_ssl = settings.SMTP_SSL
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML version of email body
            text_body: Plain text version (optional, will strip HTML if not provided)
            cc: List of CC recipients
            bcc: List of BCC recipients

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            if cc:
                msg["Cc"] = ", ".join(cc)

            # Add plain text version (fallback)
            if text_body:
                text_part = MIMEText(text_body, "plain")
                msg.attach(text_part)

            # Add HTML version
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)

            # Build recipient list
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Send email
            if self.smtp_ssl:
                # Use SSL
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                # Use regular connection
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)

                # Upgrade to TLS if needed
                if self.smtp_tls:
                    server.starttls()

            # Login if credentials provided
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            # Send the email
            server.send_message(msg, self.from_email, recipients)
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_password_reset_email(
        self, to_email: str, reset_token: str, user_name: Optional[str] = None
    ) -> bool:
        """
        Send password reset email

        Args:
            to_email: User's email address
            reset_token: Password reset token
            user_name: User's name (optional)

        Returns:
            True if email sent successfully
        """
        # In production, this would be a proper URL
        # For now, we'll use a placeholder
        reset_url = f"http://localhost:3000/reset-password?token={reset_token}"

        greeting = f"Hi {user_name}," if user_name else "Hi,"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Password Reset Request</h2>
                <p>{greeting}</p>
                <p>We received a request to reset your password for your BC Legal Tech account.</p>
                <p>Click the button below to reset your password:</p>
                <a href="{reset_url}" class="button">Reset Password</a>
                <p>Or copy and paste this link into your browser:</p>
                <p><a href="{reset_url}">{reset_url}</a></p>
                <p><strong>This link will expire in 1 hour.</strong></p>
                <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                <div class="footer">
                    <p>BC Legal Tech - AI-Powered Legal Document Intelligence</p>
                    <p>This is an automated email, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        {greeting}

        We received a request to reset your password for your BC Legal Tech account.

        Click this link to reset your password:
        {reset_url}

        This link will expire in 1 hour.

        If you didn't request a password reset, you can safely ignore this email.

        ---
        BC Legal Tech - AI-Powered Legal Document Intelligence
        This is an automated email, please do not reply.
        """

        return await self.send_email(
            to_email=to_email,
            subject="Reset Your Password - BC Legal Tech",
            html_body=html_body,
            text_body=text_body,
        )

    async def send_user_invitation_email(
        self,
        to_email: str,
        invited_by: str,
        company_name: str,
        invitation_token: str,
    ) -> bool:
        """
        Send user invitation email

        Args:
            to_email: Invitee's email address
            invited_by: Name of person who sent invitation
            company_name: Name of the company/law firm
            invitation_token: Invitation token for signup

        Returns:
            True if email sent successfully
        """
        invitation_url = f"http://localhost:3000/accept-invitation?token={invitation_token}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #28a745;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>You've Been Invited to BC Legal Tech</h2>
                <p>Hi,</p>
                <p><strong>{invited_by}</strong> has invited you to join <strong>{company_name}</strong> on BC Legal Tech.</p>
                <p>BC Legal Tech is an AI-powered legal document intelligence platform that helps law firms:</p>
                <ul>
                    <li>Upload and organize legal documents</li>
                    <li>Chat with your documents using AI</li>
                    <li>Get instant answers with cited sources</li>
                    <li>Collaborate with your team</li>
                </ul>
                <p>Click the button below to accept the invitation and create your account:</p>
                <a href="{invitation_url}" class="button">Accept Invitation</a>
                <p>Or copy and paste this link into your browser:</p>
                <p><a href="{invitation_url}">{invitation_url}</a></p>
                <p><strong>This invitation will expire in 7 days.</strong></p>
                <div class="footer">
                    <p>BC Legal Tech - AI-Powered Legal Document Intelligence</p>
                    <p>This is an automated email, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        You've Been Invited to BC Legal Tech

        Hi,

        {invited_by} has invited you to join {company_name} on BC Legal Tech.

        BC Legal Tech is an AI-powered legal document intelligence platform.

        Click this link to accept the invitation and create your account:
        {invitation_url}

        This invitation will expire in 7 days.

        ---
        BC Legal Tech - AI-Powered Legal Document Intelligence
        This is an automated email, please do not reply.
        """

        return await self.send_email(
            to_email=to_email,
            subject=f"Invitation to Join {company_name} on BC Legal Tech",
            html_body=html_body,
            text_body=text_body,
        )

    async def send_welcome_email(
        self, to_email: str, user_name: str, company_name: str
    ) -> bool:
        """
        Send welcome email to new users

        Args:
            to_email: User's email address
            user_name: User's name
            company_name: Company/firm name

        Returns:
            True if email sent successfully
        """
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Welcome to BC Legal Tech!</h2>
                <p>Hi {user_name},</p>
                <p>Welcome to BC Legal Tech! Your account for <strong>{company_name}</strong> has been created successfully.</p>
                <h3>Getting Started:</h3>
                <ol>
                    <li><strong>Upload Documents:</strong> Start by uploading your legal documents (PDF, Word, Excel)</li>
                    <li><strong>AI Processing:</strong> Our AI will analyze and index your documents</li>
                    <li><strong>Chat & Search:</strong> Ask questions and get answers with cited sources</li>
                    <li><strong>Collaborate:</strong> Share documents and conversations with your team</li>
                </ol>
                <a href="http://localhost:3000/dashboard" class="button">Go to Dashboard</a>
                <p>If you have any questions, our support team is here to help.</p>
                <div class="footer">
                    <p>BC Legal Tech - AI-Powered Legal Document Intelligence</p>
                    <p>This is an automated email, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Welcome to BC Legal Tech!

        Hi {user_name},

        Welcome to BC Legal Tech! Your account for {company_name} has been created successfully.

        Getting Started:
        1. Upload Documents: Start by uploading your legal documents
        2. AI Processing: Our AI will analyze and index your documents
        3. Chat & Search: Ask questions and get answers with cited sources
        4. Collaborate: Share documents and conversations with your team

        Visit: http://localhost:3000/dashboard

        ---
        BC Legal Tech - AI-Powered Legal Document Intelligence
        This is an automated email, please do not reply.
        """

        return await self.send_email(
            to_email=to_email,
            subject=f"Welcome to BC Legal Tech, {user_name}!",
            html_body=html_body,
            text_body=text_body,
        )
