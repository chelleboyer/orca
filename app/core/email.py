"""
Email service for authentication and notifications
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending authentication and notification emails"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_TLS
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME
        self.use_console_backend = settings.USE_EMAIL_CONSOLE_BACKEND
    
    def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email via SMTP or console backend"""
        
        if self.use_console_backend:
            # Development mode - print email to console
            self._print_email_to_console(to_email, subject, html_content, text_content)
            return True
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
                logger.error("SMTP configuration incomplete")
                return False
            
            # Type checking ensures these are not None at this point
            assert self.smtp_host is not None
            assert self.smtp_user is not None
            assert self.smtp_password is not None
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def _print_email_to_console(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ):
        """Print email content to console for development"""
        print("\n" + "="*80)
        print("EMAIL CONSOLE BACKEND - Development Mode")
        print("="*80)
        print(f"To: {to_email}")
        print(f"From: {self.from_name} <{self.from_email}>")
        print(f"Subject: {subject}")
        print("-"*80)
        
        if text_content:
            print("TEXT CONTENT:")
            print(text_content)
            print("-"*80)
        
        print("HTML CONTENT:")
        print(html_content)
        print("="*80 + "\n")
    
    def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Send email verification email"""
        
        verification_url = f"http://localhost:8000/api/v1/auth/verify-email/{verification_token}"
        
        subject = "Verify your OOUX ORCA account"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Account</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; background-color: #3b82f6; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to OOUX ORCA!</h1>
                </div>
                <div class="content">
                    <h2>Verify Your Email Address</h2>
                    <p>Thank you for signing up for OOUX ORCA Project Builder. To complete your registration and start using the platform, please verify your email address by clicking the button below:</p>
                    
                    <a href="{verification_url}" class="button">Verify Email Address</a>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p><a href="{verification_url}">{verification_url}</a></p>
                    
                    <p><strong>This verification link will expire in 24 hours.</strong></p>
                    
                    <p>If you didn't create an account with OOUX ORCA, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>Best regards,<br>The OOUX ORCA Team</p>
                    <p><small>This is an automated message. Please do not reply to this email.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to OOUX ORCA!
        
        Thank you for signing up for OOUX ORCA Project Builder. To complete your registration and start using the platform, please verify your email address by visiting the following link:
        
        {verification_url}
        
        This verification link will expire in 24 hours.
        
        If you didn't create an account with OOUX ORCA, you can safely ignore this email.
        
        Best regards,
        The OOUX ORCA Team
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        
        reset_url = f"http://localhost:8000/reset-password?token={reset_token}"
        
        subject = "Reset your OOUX ORCA password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; background-color: #dc2626; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background-color: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .warning {{ background-color: #fef2f2; border: 1px solid #fca5a5; padding: 15px; border-radius: 6px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Reset Your Password</h2>
                    <p>We received a request to reset your password for your OOUX ORCA account. If you made this request, click the button below to reset your password:</p>
                    
                    <a href="{reset_url}" class="button">Reset Password</a>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p><a href="{reset_url}">{reset_url}</a></p>
                    
                    <div class="warning">
                        <p><strong>Important Security Information:</strong></p>
                        <ul>
                            <li>This password reset link will expire in 15 minutes</li>
                            <li>The link can only be used once</li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>Your password will remain unchanged unless you click the link and set a new one</li>
                        </ul>
                    </div>
                    
                    <p>If you continue to have problems accessing your account, please contact our support team.</p>
                </div>
                <div class="footer">
                    <p>Best regards,<br>The OOUX ORCA Team</p>
                    <p><small>This is an automated security message. Please do not reply to this email.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request - OOUX ORCA
        
        We received a request to reset your password for your OOUX ORCA account. If you made this request, visit the following link to reset your password:
        
        {reset_url}
        
        IMPORTANT SECURITY INFORMATION:
        - This password reset link will expire in 15 minutes
        - The link can only be used once
        - If you didn't request this reset, please ignore this email
        - Your password will remain unchanged unless you click the link and set a new one
        
        If you continue to have problems accessing your account, please contact our support team.
        
        Best regards,
        The OOUX ORCA Team
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send welcome email after successful verification"""
        
        subject = "Welcome to OOUX ORCA! Your account is ready"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to OOUX ORCA</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; background-color: #10b981; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .features {{ background-color: white; padding: 20px; border-radius: 6px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to OOUX ORCA!</h1>
                </div>
                <div class="content">
                    <h2>Hello {user_name}!</h2>
                    <p>Your account has been successfully verified and you're ready to start building amazing Object-Oriented UX projects!</p>
                    
                    <div class="features">
                        <h3>What you can do with OOUX ORCA:</h3>
                        <ul>
                            <li>📋 Create and manage OOUX projects</li>
                            <li>🔗 Map object relationships and hierarchies</li>
                            <li>🎯 Define call-to-actions and user flows</li>
                            <li>📊 Generate comprehensive OOUX reports</li>
                            <li>👥 Collaborate with your team in real-time</li>
                            <li>📤 Export your work in multiple formats</li>
                        </ul>
                    </div>
                    
                    <a href="http://localhost:8000/login" class="button">Start Building Your First Project</a>
                    
                    <p>If you have any questions or need help getting started, check out our documentation or contact our support team.</p>
                </div>
                <div class="footer">
                    <p>Happy building!<br>The OOUX ORCA Team</p>
                    <p><small>Follow us for tips and updates on Object-Oriented UX methodology.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to OOUX ORCA!
        
        Hello {user_name}!
        
        Your account has been successfully verified and you're ready to start building amazing Object-Oriented UX projects!
        
        What you can do with OOUX ORCA:
        - Create and manage OOUX projects
        - Map object relationships and hierarchies
        - Define call-to-actions and user flows
        - Generate comprehensive OOUX reports
        - Collaborate with your team in real-time
        - Export your work in multiple formats
        
        Get started: http://localhost:8000/login
        
        If you have any questions or need help getting started, check out our documentation or contact our support team.
        
        Happy building!
        The OOUX ORCA Team
        """
        
        return self._send_email(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()
