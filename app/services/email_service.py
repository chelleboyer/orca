"""
Email service for sending notifications and invitations
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.models import ProjectInvitation, ProjectMember


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_HOST', 'localhost')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USER', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.smtp_use_tls = getattr(settings, 'SMTP_TLS', True)
        self.from_email = getattr(settings, 'EMAILS_FROM_EMAIL', 'noreply@ooux-orca.com')
        self.from_name = getattr(settings, 'EMAILS_FROM_NAME', 'OOUX ORCA')
        
        # For development, we'll just log emails instead of sending
        self.development_mode = getattr(settings, 'DEBUG', True)

    def send_project_invitation(self, invitation: ProjectInvitation) -> bool:
        """
        Send project invitation email
        
        Args:
            invitation: ProjectInvitation object
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = f"You're invited to join '{invitation.project.title}' on OOUX ORCA"
            
            # Create invitation URL
            invitation_url = f"{settings.FRONTEND_URL}/invite/{invitation.token}"
            
            # HTML email content
            html_content = self._create_invitation_email_html(
                invitation=invitation,
                invitation_url=invitation_url
            )
            
            # Plain text fallback
            text_content = self._create_invitation_email_text(
                invitation=invitation,
                invitation_url=invitation_url
            )
            
            return self._send_email(
                to_email=invitation.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            print(f"Failed to send invitation email: {e}")
            return False

    def send_welcome_to_project(self, membership: ProjectMember) -> bool:
        """
        Send welcome email to new project member
        
        Args:
            membership: ProjectMember object
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = f"Welcome to '{membership.project.title}' on OOUX ORCA"
            
            project_url = f"{settings.FRONTEND_URL}/projects/{membership.project.slug}"
            
            html_content = self._create_welcome_email_html(
                membership=membership,
                project_url=project_url
            )
            
            text_content = self._create_welcome_email_text(
                membership=membership,
                project_url=project_url
            )
            
            return self._send_email(
                to_email=membership.user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
            return False

    def send_invitation_reminder(self, invitation: ProjectInvitation) -> bool:
        """
        Send reminder email for expiring invitation
        
        Args:
            invitation: ProjectInvitation object
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            days_left = invitation.days_until_expiry
            subject = f"Reminder: Invitation to '{invitation.project.title}' expires in {days_left} day{'s' if days_left != 1 else ''}"
            
            invitation_url = f"{settings.FRONTEND_URL}/invite/{invitation.token}"
            
            html_content = self._create_reminder_email_html(
                invitation=invitation,
                invitation_url=invitation_url,
                days_left=days_left
            )
            
            text_content = self._create_reminder_email_text(
                invitation=invitation,
                invitation_url=invitation_url,
                days_left=days_left
            )
            
            return self._send_email(
                to_email=invitation.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            print(f"Failed to send reminder email: {e}")
            return False

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send email using SMTP or log in development mode
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content
            reply_to: Optional reply-to address
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if self.development_mode:
            # In development mode, just log the email
            print("\\n" + "="*60)
            print("📧 EMAIL NOTIFICATION (Development Mode)")
            print("="*60)
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            if reply_to:
                print(f"Reply-To: {reply_to}")
            print("\\nContent:")
            print(text_content)
            print("="*60)
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False

    def _create_invitation_email_html(
        self,
        invitation: ProjectInvitation,
        invitation_url: str
    ) -> str:
        """Create HTML content for invitation email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Project Invitation</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">You're invited to collaborate!</h1>
                
                <p>Hello!</p>
                
                <p><strong>{invitation.inviter.name}</strong> has invited you to join the OOUX project:</p>
                
                <div style="background: #f8fafc; border-left: 4px solid #2563eb; padding: 16px; margin: 20px 0;">
                    <h2 style="margin: 0 0 8px 0; color: #1e40af;">{invitation.project.title}</h2>
                    <p style="margin: 0; color: #64748b;">Role: <strong>{invitation.role.title()}</strong></p>
                </div>
                
                {f'<div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; margin: 20px 0;"><p style="margin: 0; font-style: italic;">"{invitation.message}"</p></div>' if invitation.message else ''}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invitation_url}" 
                       style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Accept Invitation
                    </a>
                </div>
                
                <p>This invitation will expire on <strong>{invitation.expires_at.strftime('%B %d, %Y at %I:%M %p')}</strong>.</p>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #64748b;">
                    If you can't click the button above, copy and paste this link into your browser:<br>
                    <a href="{invitation_url}" style="color: #2563eb;">{invitation_url}</a>
                </p>
                
                <p style="font-size: 14px; color: #64748b;">
                    If you don't want to join this project, you can safely ignore this email.
                </p>
            </div>
        </body>
        </html>
        """

    def _create_invitation_email_text(
        self,
        invitation: ProjectInvitation,
        invitation_url: str
    ) -> str:
        """Create plain text content for invitation email"""
        message_section = f'\\nPersonal message: "{invitation.message}"\\n' if invitation.message else ''
        
        return f"""
You're invited to collaborate on OOUX ORCA!

Hello!

{invitation.inviter.name} has invited you to join the OOUX project:

Project: {invitation.project.title}
Role: {invitation.role.title()}
{message_section}
To accept this invitation, visit:
{invitation_url}

This invitation will expire on {invitation.expires_at.strftime('%B %d, %Y at %I:%M %p')}.

If you don't want to join this project, you can safely ignore this email.

---
OOUX ORCA - Object-Oriented UX Collaboration Platform
        """.strip()

    def _create_welcome_email_html(
        self,
        membership: ProjectMember,
        project_url: str
    ) -> str:
        """Create HTML content for welcome email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Project</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #059669;">Welcome to the team!</h1>
                
                <p>Hi {membership.user.name},</p>
                
                <p>You've successfully joined the OOUX project:</p>
                
                <div style="background: #f0fdf4; border-left: 4px solid #059669; padding: 16px; margin: 20px 0;">
                    <h2 style="margin: 0 0 8px 0; color: #047857;">{membership.project.title}</h2>
                    <p style="margin: 0; color: #064e3b;">Your role: <strong>{membership.role.title()}</strong></p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{project_url}" 
                       style="background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Go to Project
                    </a>
                </div>
                
                <p>You can now start collaborating with your team to create amazing Object-Oriented UX designs!</p>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #64748b;">
                    Questions? Check out our help documentation or contact your project facilitator.
                </p>
            </div>
        </body>
        </html>
        """

    def _create_welcome_email_text(
        self,
        membership: ProjectMember,
        project_url: str
    ) -> str:
        """Create plain text content for welcome email"""
        return f"""
Welcome to the team!

Hi {membership.user.name},

You've successfully joined the OOUX project:

Project: {membership.project.title}
Your role: {membership.role.title()}

Visit your project: {project_url}

You can now start collaborating with your team to create amazing Object-Oriented UX designs!

Questions? Check out our help documentation or contact your project facilitator.

---
OOUX ORCA - Object-Oriented UX Collaboration Platform
        """.strip()

    def _create_reminder_email_html(
        self,
        invitation: ProjectInvitation,
        invitation_url: str,
        days_left: int
    ) -> str:
        """Create HTML content for reminder email"""
        urgency_color = "#dc2626" if days_left <= 1 else "#f59e0b"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Invitation Reminder</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: {urgency_color};">Don't miss out!</h1>
                
                <p>Hello!</p>
                
                <p>This is a friendly reminder that your invitation to join the OOUX project "<strong>{invitation.project.title}</strong>" expires in <strong>{days_left} day{'s' if days_left != 1 else ''}</strong>.</p>
                
                <div style="background: #fef2f2; border-left: 4px solid {urgency_color}; padding: 16px; margin: 20px 0;">
                    <p style="margin: 0; font-weight: bold;">Expires: {invitation.expires_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invitation_url}" 
                       style="background: {urgency_color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Accept Invitation Now
                    </a>
                </div>
                
                <p>After the expiration date, you'll need to request a new invitation to join the project.</p>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #64748b;">
                    If you can't click the button above, copy and paste this link into your browser:<br>
                    <a href="{invitation_url}" style="color: {urgency_color};">{invitation_url}</a>
                </p>
            </div>
        </body>
        </html>
        """

    def _create_reminder_email_text(
        self,
        invitation: ProjectInvitation,
        invitation_url: str,
        days_left: int
    ) -> str:
        """Create plain text content for reminder email"""
        return f"""
Don't miss out - Invitation expiring soon!

Hello!

This is a friendly reminder that your invitation to join the OOUX project "{invitation.project.title}" expires in {days_left} day{'s' if days_left != 1 else ''}.

Expires: {invitation.expires_at.strftime('%B %d, %Y at %I:%M %p')}

To accept this invitation, visit:
{invitation_url}

After the expiration date, you'll need to request a new invitation to join the project.

---
OOUX ORCA - Object-Oriented UX Collaboration Platform
        """.strip()
