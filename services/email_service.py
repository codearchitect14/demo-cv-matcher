import os
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        """Initialize email service with SendGrid configuration"""
        self.api_key = os.getenv("SENDGRID_API_KEY")
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY not found in environment variables")
        
        self.sg = SendGridAPIClient(api_key=self.api_key)
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "ali.mughal@boolmind.com")  # Default sender email
        
    async def send_email(self, to_email: str, subject: str, html_content: str, 
                        from_email: Optional[str] = None) -> bool:
        """
        Send email using SendGrid
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            from_email: Sender email (optional, uses default if not provided)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            sender_email = from_email or self.from_email
            print(f"DEBUG: Creating email message for {to_email}")
            print(f"DEBUG: Sender email: {sender_email}")
            print(f"DEBUG: SendGrid API Key (first 10 chars): {self.api_key[:10] if self.api_key else 'None'}...")
            
            message = Mail(
                from_email=sender_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            print(f"DEBUG: Sending email via SendGrid to {to_email}")
            # Send email asynchronously
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.sg.send, message)
            
            print(f"DEBUG: SendGrid response status: {response.status_code}")
            print(f"DEBUG: SendGrid response body: {response.body}")
            print(f"DEBUG: SendGrid response headers: {dict(response.headers)}")
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully to {to_email}")
                print(f"DEBUG: Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}, Body: {response.body}")
                print(f"DEBUG: Email failed to send. Status: {response.status_code}, Body: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"SendGrid failed to send email to {to_email}: {str(e)}")
            print(f"DEBUG: SendGrid exception: {str(e)}")
            
            # Try fallback email service
            try:
                from services.email_service_fallback import fallback_email_service
                logger.info(f"Attempting fallback email service for {to_email}")
                return await fallback_email_service.send_email(to_email, subject, html_content, from_email)
            except Exception as fallback_error:
                logger.error(f"Fallback email service also failed: {fallback_error}")
                return False
    
    async def send_welcome_email(self, candidate_email: str, candidate_name: str) -> bool:
        """Send welcome email to newly registered candidate"""
        subject = "Welcome to CV Matcher - Account Activated!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3b82f6; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .button {{ background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to CV Matcher!</h1>
                </div>
                <div class="content">
                    <h2>Hello {candidate_name}!</h2>
                    <p>Your account has been successfully created and activated. You can now start exploring job opportunities that match your skills and experience.</p>
                    
                    <h3>What's Next?</h3>
                    <ul>
                        <li>Complete your profile with additional skills and experience</li>
                        <li>Browse job opportunities that match your profile</li>
                        <li>Apply to jobs that interest you</li>
                        <li>Track your application status</li>
                    </ul>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/candidates-dashboard" class="button">Go to Dashboard</a>
                    </p>
                    
                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                </div>
                <div class="footer">
                    <p>Best regards,<br>The CV Matcher Team</p>
                    <p><small>This email was sent to {candidate_email}</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(candidate_email, subject, html_content)
    
    async def send_application_confirmation_email(self, candidate_email: str, candidate_name: str, 
                                               job_title: str, company_name: str) -> bool:
        """Send application confirmation email to candidate"""
        subject = f"Application Submitted Successfully - {job_title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #10b981; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .job-details {{ background-color: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Application Submitted!</h1>
                </div>
                <div class="content">
                    <h2>Hello {candidate_name}!</h2>
                    <p>Your job application has been successfully submitted. Here are the details:</p>
                    
                    <div class="job-details">
                        <h3>Job Details:</h3>
                        <p><strong>Position:</strong> {job_title}</p>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>Application Date:</strong> {self._get_current_date()}</p>
                    </div>
                    
                    <h3>What Happens Next?</h3>
                    <ul>
                        <li>Your application will be reviewed by the hiring team</li>
                        <li>You'll receive updates on your application status</li>
                        <li>If shortlisted, you may be invited for an interview</li>
                        <li>You can track your application status in your dashboard</li>
                    </ul>
                    
                    <p>Thank you for your interest in this position. We'll keep you updated on the progress.</p>
                </div>
                <div class="footer">
                    <p>Best regards,<br>The CV Matcher Team</p>
                    <p><small>This email was sent to {candidate_email}</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(candidate_email, subject, html_content)
    
    async def send_login_welcome_email(self, candidate_email: str, candidate_name: str) -> bool:
        """Send welcome back email to candidate on login"""
        subject = "Welcome back to CV Matcher!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome Back!</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome Back, {candidate_name}!</h1>
                </div>
                <div class="content">
                    <p>Great to see you again! You've successfully logged into your CV Matcher account.</p>
                    
                    <p>Here's what you can do:</p>
                    <ul>
                        <li> View your profile and applications</li>
                        <li> Browse new job opportunities</li>
                        <li> Check your application status</li>
                        <li> Get personalized job recommendations</li>
                    </ul>
                    
                    <p>Ready to find your next opportunity?</p>
                    
                    <a href="http://localhost:3000/dashboard" class="button">Go to Dashboard</a>
                    
                    <p>If you didn't log in, please secure your account immediately.</p>
                    
                    <p>Happy job hunting!</p>
                    <p><strong>The CV Matcher Team</strong></p>
                </div>
                <div class="footer">
                    <p>This email was sent because you logged into your CV Matcher account.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(candidate_email, subject, html_content)

    async def send_password_reset_email(self, candidate_email: str, candidate_name: str, reset_token: str) -> bool:
        """Send password reset email to candidate"""
        subject = "Reset Your CV Matcher Password"
        
        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .warning {{ background: #fef3cd; border: 1px solid #fbbf24; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello {candidate_name},</p>
                    
                    <p>We received a request to reset your password for your CV Matcher account.</p>
                    
                    <p>Click the button below to reset your password:</p>
                    
                    <a href="{reset_link}" class="button">Reset Password</a>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong>
                        <ul>
                            <li>This link will expire in 1 hour</li>
                            <li>If you didn't request this, please ignore this email</li>
                            <li>For security, don't share this link with anyone</li>
                        </ul>
                    </div>
                    
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #6b7280;">{reset_link}</p>
                    
                    <p>Best regards,<br><strong>The CV Matcher Team</strong></p>
                </div>
                <div class="footer">
                    <p>This password reset link expires in 1 hour.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(candidate_email, subject, html_content)
    
    async def send_status_update_email(self, candidate_email: str, candidate_name: str,
                                    job_title: str, company_name: str, old_status: str, 
                                    new_status: str) -> bool:
        """Send status update email to candidate"""
        subject = f"Application Status Update - {job_title}"
        
        status_colors = {
            "APPLIED": "#3b82f6",
            "SHORTLISTED": "#10b981", 
            "INTERVIEW": "#f59e0b",
            "REJECTED": "#ef4444",
            "HIRED": "#8b5cf6"
        }
        
        status_color = status_colors.get(new_status.upper(), "#6b7280")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {status_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .status-update {{ background-color: white; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center; }}
                .old-status {{ color: #6b7280; text-decoration: line-through; }}
                .new-status {{ color: {status_color}; font-weight: bold; font-size: 18px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Application Status Update</h1>
                </div>
                <div class="content">
                    <h2>Hello {candidate_name}!</h2>
                    <p>Your application status has been updated:</p>
                    
                    <div class="status-update">
                        <h3>Job: {job_title}</h3>
                        <p>Company: {company_name}</p>
                        <p>Status: <span class="old-status">{old_status}</span> → <span class="new-status">{new_status}</span></p>
                    </div>
                    
                    {self._get_status_message(new_status)}
                    
                    <p>You can view all your applications and their current status in your dashboard.</p>
                </div>
                <div class="footer">
                    <p>Best regards,<br>The CV Matcher Team</p>
                    <p><small>This email was sent to {candidate_email}</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(candidate_email, subject, html_content)
    
    def _get_current_date(self) -> str:
        """Get current date in readable format"""
        from datetime import datetime
        return datetime.now().strftime("%B %d, %Y")
    
    def _get_status_message(self, status: str) -> str:
        """Get appropriate message based on status"""
        messages = {
            "APPLIED": "<p>Your application has been received and is under review.</p>",
            "SHORTLISTED": "<p>Congratulations! Your application has been shortlisted. The hiring team will contact you soon.</p>",
            "INTERVIEW": "<p>Great news! You've been selected for an interview. Check your dashboard for interview details.</p>",
            "REJECTED": "<p>Thank you for your interest. While your application wasn't selected this time, we encourage you to apply for other positions.</p>",
            "HIRED": "<p>Congratulations! You've been selected for the position. Welcome to the team!</p>"
        }
        return messages.get(status.upper(), "<p>Your application status has been updated.</p>")

    # ===== RECRUITER EMAIL TEMPLATES =====

    async def send_recruiter_welcome_email(self, recruiter_email: str, recruiter_name: str, 
                                         company_name: str, login_credentials: dict = None, 
                                         user_type: str = "admin") -> bool:
        """Send welcome email to newly created recruiter/admin"""
        # Set subject based on user type
        if user_type == "admin":
            subject = f"Welcome to {company_name} - Your Admin Account is Ready!"
        else:
            subject = f"Welcome to {company_name} - Your Recruiter Account is Ready!"
        
        credentials_section = ""
        if login_credentials:
            credentials_section = f"""
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
                <h3 style="margin-top: 0; color: #2e7d32;">Your Login Credentials:</h3>
                <p><strong>Email:</strong> {recruiter_email}</p>
                <p><strong>Password:</strong> {login_credentials.get('password', 'Please check with your admin')}</p>
                <p><strong>Dashboard:</strong> <a href="http://localhost:3000/recruiter/dashboard" style="color: #2e7d32;">http://localhost:3000/recruiter/dashboard</a></p>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to {company_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {company_name}!</h1>
                </div>
                <div class="content">
                    <h2>Hello {recruiter_name}!</h2>
                    <p>Your {user_type} account has been successfully created. You can now start managing jobs and candidates for {company_name}.</p>
                    
                    {credentials_section}
                    
                    <h3>What you can do:</h3>
                    <ul>
                        <li>View and manage job applications</li>
                        <li>Create and manage job postings</li>
                        <li>Assign jobs to team members</li>
                        <li>Contact qualified candidates</li>
                        <li>Create sub-recruiters for your team</li>
                        <li>Track application progress</li>
                        <li>Generate recruitment reports</li>
                    </ul>
                    
                    <p>Click the button below to access your recruiter dashboard:</p>
                    <a href="http://localhost:3000/recruiter/dashboard" class="btn">Access Dashboard</a>
                    
                    <p>If you have any questions, please contact your system administrator.</p>
                    <p>Best regards,<br>HR Team at {company_name}</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(recruiter_email, subject, html_content)

    async def send_job_posting_confirmation_email(self, admin_email: str, admin_name: str, 
                                                job_title: str, company_name: str) -> bool:
        """Send job posting confirmation email to Company Admin"""
        subject = f"Job Posted Successfully - {job_title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Job Posted Successfully</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .job-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Job Posted Successfully!</h1>
                </div>
                <div class="content">
                    <h2>Hello {admin_name}!</h2>
                    <p>Your job posting has been successfully published and is now live on our platform.</p>
                    
                    <div class="job-details">
                        <h3>Job Details:</h3>
                        <p><strong>Position:</strong> {job_title}</p>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>Status:</strong> <span style="color: #10b981; font-weight: bold;">ACTIVE</span></p>
                    </div>
                    
                    <p>Your job is now visible to candidates and will start receiving applications. You can:</p>
                    <ul>
                        <li>Monitor applications in real-time</li>
                        <li>Assign the job to specific recruiters</li>
                        <li>Contact interested candidates</li>
                        <li>Track application progress</li>
                    </ul>
                    
                    <a href="http://localhost:3000/recruiter/dashboard" class="btn">View Dashboard</a>
                    
                    <p>Best regards,<br>CV Matcher Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(admin_email, subject, html_content)

    async def send_job_assignment_email(self, recruiter_email: str, recruiter_name: str, 
                                      job_title: str, company_name: str, admin_name: str) -> bool:
        """Send job assignment notification email to assigned recruiter"""
        subject = f"New Job Assignment - {job_title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>New Job Assignment</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .assignment-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3b82f6; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Job Assignment</h1>
                </div>
                <div class="content">
                    <h2>Hello {recruiter_name}!</h2>
                    <p>You have been assigned a new job to manage by {admin_name}.</p>
                    
                    <div class="assignment-details">
                        <h3>Assignment Details:</h3>
                        <p><strong>Position:</strong> {job_title}</p>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>Assigned by:</strong> {admin_name}</p>
                        <p><strong>Assigned on:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                    </div>
                    
                    <p>Your responsibilities include:</p>
                    <ul>
                        <li>Reviewing incoming applications</li>
                        <li>Contacting qualified candidates</li>
                        <li>Conducting initial screenings</li>
                        <li>Updating application statuses</li>
                        <li>Providing feedback to candidates</li>
                    </ul>
                    
                    <a href="http://localhost:3000/recruiter/dashboard" class="btn">View Job Details</a>
                    
                    <p>If you have any questions about this assignment, please contact {admin_name}.</p>
                    <p>Best regards,<br>CV Matcher Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(recruiter_email, subject, html_content)

    async def send_candidate_contact_email(self, candidate_email: str, candidate_name: str, 
                                         admin_name: str, company_name: str, 
                                         message: str, job_title: str = None) -> bool:
        """Send contact email from Company Admin to candidate"""
        subject = f"Message from {company_name} - Job Opportunity"
        if job_title:
            subject = f"Message from {company_name} - {job_title} Position"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Message from {company_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .message-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #8b5cf6; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Message from {company_name}</h1>
                </div>
                <div class="content">
                    <h2>Hello {candidate_name}!</h2>
                    <p>You have received a message from {admin_name} at {company_name}.</p>
                    
                    <div class="message-box">
                        <h3>Message:</h3>
                        <p style="white-space: pre-line;">{message}</p>
                    </div>
                    
                    <p>If you're interested in this opportunity, please reply to this email or contact us directly.</p>
                    <p>We look forward to hearing from you!</p>
                    <p>Best regards,<br>{admin_name}<br>{company_name}</p>
                </div>
                <div class="footer">
                    <p>This message was sent through CV Matcher platform.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(candidate_email, subject, html_content)

    async def send_sub_recruiter_welcome_email(self, recruiter_email: str, recruiter_name: str, 
                                             company_name: str, admin_name: str, login_credentials: dict = None) -> bool:
        """Send welcome email to newly created sub-recruiter"""
        subject = f"Welcome to {company_name} - Your Recruiter Account is Ready!"
        
        credentials_section = ""
        if login_credentials:
            credentials_section = f"""
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
                <h3 style="margin-top: 0; color: #2e7d32;">Your Login Credentials:</h3>
                <p><strong>Email:</strong> {recruiter_email}</p>
                <p><strong>Password:</strong> {login_credentials.get('password', 'Please check with your admin')}</p>
                <p><strong>Dashboard:</strong> <a href="http://localhost:3000/recruiter/dashboard" style="color: #2e7d32;">http://localhost:3000/recruiter/dashboard</a></p>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to {company_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
                .admin-note {{ background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {company_name}!</h1>
                </div>
                <div class="content">
                    <h2>Hello {recruiter_name}!</h2>
                    <p>Your recruiter account has been created by {admin_name}. You can now start managing assigned jobs and candidates for {company_name}.</p>
                    
                    {credentials_section}
                    
                    <div class="admin-note">
                        <h3 style="margin-top: 0; color: #1976d2;">Your Role:</h3>
                        <p>You are a <strong>Sub-Recruiter</strong> working under {admin_name}. You will be assigned specific jobs to manage.</p>
                    </div>
                    
                    <h3>What you can do:</h3>
                    <ul>
                        <li>View assigned job applications</li>
                        <li>Contact qualified candidates</li>
                        <li>Update application statuses</li>
                        <li>Provide feedback to candidates</li>
                        <li>Track progress on your assigned jobs</li>
                    </ul>
                    
                    <p>Click the button below to access your recruiter dashboard:</p>
                    <a href="http://localhost:3000/recruiter/dashboard" class="btn">Access Dashboard</a>
                    
                    <p>If you have any questions, please contact {admin_name} (your admin).</p>
                    <p>Best regards,<br>HR Team at {company_name}</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(recruiter_email, subject, html_content)

    async def send_recruiter_login_email(self, recruiter_email: str, recruiter_name: str, 
                                       company_name: str) -> bool:
        """Send login welcome email to recruiter"""
        subject = f"Welcome Back to {company_name}!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome Back</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome Back!</h1>
                </div>
                <div class="content">
                    <h2>Hello {recruiter_name}!</h2>
                    <p>You've successfully logged into your {company_name} recruiter account.</p>
                    
                    <p>Ready to continue managing your recruitment activities:</p>
                    <ul>
                        <li>View and manage job applications</li>
                        <li>Contact qualified candidates</li>
                        <li>Track application progress</li>
                        <li>Update job postings</li>
                    </ul>
                    
                    <a href="http://localhost:3000/recruiter/dashboard" class="btn">Go to Dashboard</a>
                    
                    <p>If you didn't log in, please contact your system administrator immediately.</p>
                    <p>Best regards,<br>CV Matcher Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(recruiter_email, subject, html_content)

    async def send_sub_recruiter_welcome_email(self, recruiter_email: str, recruiter_name: str, 
                                             company_name: str, admin_name: str, login_credentials: dict = None) -> bool:
        """Send welcome email to newly created sub-recruiter"""
        subject = f"Welcome to {company_name} - Your Recruiter Account is Ready!"
        
        credentials_section = ""
        if login_credentials:
            credentials_section = f"""
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
                <h3 style="margin-top: 0; color: #2e7d32;">Your Login Credentials:</h3>
                <p><strong>Email:</strong> {recruiter_email}</p>
                <p><strong>Password:</strong> {login_credentials.get('password', 'Please check with your admin')}</p>
                <p><strong>Dashboard:</strong> <a href="http://localhost:3000/recruiter/dashboard" style="color: #2e7d32;">http://localhost:3000/recruiter/dashboard</a></p>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to {company_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
                .admin-note {{ background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {company_name}!</h1>
                </div>
                <div class="content">
                    <h2>Hello {recruiter_name}!</h2>
                    <p>Your recruiter account has been created by {admin_name}. You can now start managing assigned jobs and candidates for {company_name}.</p>
                    
                    {credentials_section}
                    
                    <div class="admin-note">
                        <h3 style="margin-top: 0; color: #1976d2;">Your Role:</h3>
                        <p>You are a <strong>Sub-Recruiter</strong> working under {admin_name}. You will be assigned specific jobs to manage.</p>
                    </div>
                    
                    <h3>What you can do:</h3>
                    <ul>
                        <li>View assigned job applications</li>
                        <li>Contact qualified candidates</li>
                        <li>Update application statuses</li>
                        <li>Provide feedback to candidates</li>
                        <li>Track progress on your assigned jobs</li>
                    </ul>
                    
                    <p>Click the button below to access your recruiter dashboard:</p>
                    <a href="http://localhost:3000/recruiter/dashboard" class="btn">Access Dashboard</a>
                    
                    <p>If you have any questions, please contact {admin_name} (your admin).</p>
                    <p>Best regards,<br>HR Team at {company_name}</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(recruiter_email, subject, html_content)

    async def send_recruiter_login_email(self, recruiter_email: str, recruiter_name: str, 
                                       company_name: str) -> bool:
        """Send login welcome email to recruiter"""
        subject = f"Welcome Back to {company_name}!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome Back</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome Back!</h1>
                </div>
                <div class="content">
                    <h2>Hello {recruiter_name}!</h2>
                    <p>You've successfully logged into your {company_name} recruiter account.</p>
                    
                    <p>Ready to continue managing your recruitment activities:</p>
                    <ul>
                        <li>View and manage job applications</li>
                        <li>Contact qualified candidates</li>
                        <li>Track application progress</li>
                        <li>Update job postings</li>
                    </ul>
                    
                    <a href="http://localhost:3000/recruiter/dashboard" class="btn">Go to Dashboard</a>
                    
                    <p>If you didn't log in, please contact your system administrator immediately.</p>
                    <p>Best regards,<br>CV Matcher Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(recruiter_email, subject, html_content)

    async def send_admin_login_email(self, admin_email: str, admin_name: str, 
                                   company_name: str) -> bool:
        """Send admin-specific login welcome email"""
        subject = f"Welcome Back to {company_name} - Admin Dashboard Ready!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome Back - Company Admin</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 25px; border-radius: 12px 12px 0 0; text-align: center; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 12px 12px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; margin: 15px 0; font-weight: 600; }}
                .security-notice {{ background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b; }}
                .admin-features {{ background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981; }}
                .quick-actions {{ background: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3b82f6; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome Back, Company Admin! </h1>
                    <p style="margin: 0; opacity: 0.9;">Admin Account - {company_name}</p>
                </div>
                <div class="content">
                    <h2>Hello {admin_name}!</h2>
                    <p>You've successfully logged into your <strong>{company_name}</strong> <strong>Company Admin</strong> account.</p>
                    
                    <div class="admin-features">
                        <h3 style="margin-top: 0; color: #059669;">Your Admin Dashboard is Ready:</h3>
                        <ul>
                            <li><strong> Create and Manage Jobs</strong> - Post new positions and manage existing ones</li>
                            <li><strong> Team Management</strong> - Create and manage sub-recruiters</li>
                            <li><strong> Job Assignments</strong> - Assign jobs to team members</li>
                            <li><strong> Direct Candidate Contact</strong> - Send personalized messages to candidates</li>
                            <li><strong> Application Oversight</strong> - Monitor all job applications across your team</li>
                            <li><strong> Analytics and Reports</strong> - Track recruitment performance and metrics</li>
                            <li><strong> Company Settings</strong> - Manage company profile and preferences</li>
                        </ul>
                    </div>
                    
                    <div class="quick-actions">
                        <h3 style="margin-top: 0; color: #1e40af;">Quick Admin Actions:</h3>
                        <p>• <strong>Create New Job:</strong> <a href="http://localhost:3000/jobs-dashboard" style="color: #1e40af;">Post a new position</a></p>
                        <p>• <strong>Find Candidates:</strong> <a href="http://localhost:3000/enhanced-recruiter-recommendations" style="color: #1e40af;">Search qualified candidates</a></p>
                        <p>• <strong>Manage Team:</strong> <a href="http://localhost:3000/recruiter/dashboard" style="color: #1e40af;">Create sub-recruiters</a></p>
                        <p>• <strong>View Applications:</strong> <a href="http://localhost:3000/applications-management" style="color: #1e40af;">Monitor all applications</a></p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/recruiter/dashboard" class="btn">Access Admin Dashboard</a>
                    </div>
                    
                    <div class="security-notice">
                        <p><strong> Security Notice:</strong> If you didn't initiate this login, please contact your system administrator immediately and change your password.</p>
                    </div>
                    
                    <p>Best regards,<br><strong>CV Matcher Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated message from CV Matcher. Please do not reply to this email.</p>
                    <p>© 2024 CV Matcher - Recruitment Management System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(admin_email, subject, html_content)

    async def send_candidate_application_notification_email(self, recruiter_email: str, recruiter_name: str,
                                                          candidate_name: str, job_title: str, 
                                                          company_name: str, application_id: int) -> bool:
        """Send candidate application notification email to assigned sub-recruiter"""
        subject = f"New Candidate Application - {job_title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>New Candidate Application</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
                .candidate-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Candidate Application</h1>
                </div>
                <div class="content">
                    <h2>Hello {recruiter_name}!</h2>
                    <p>You have received a new candidate application for one of your assigned positions.</p>
                    
                    <div class="candidate-details">
                        <h3>Application Details:</h3>
                        <p><strong>Candidate:</strong> {candidate_name}</p>
                        <p><strong>Position:</strong> {job_title}</p>
                        <p><strong>Application ID:</strong> #{application_id}</p>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>Status:</strong> Applied</p>
                    </div>
                    
                    <p>Please review this application and take appropriate action:</p>
                    <ul>
                        <li>Review the candidate's profile and qualifications</li>
                        <li>Schedule an interview if qualified</li>
                        <li>Update the application status</li>
                        <li>Communicate with the candidate about next steps</li>
                    </ul>
                    
                    <a href="http://localhost:3000/sub-recruiter/dashboard" class="btn">Review Application</a>
                    
                    <p>Best regards,<br>CV Matcher System</p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(recruiter_email, subject, html_content)

    async def send_application_status_change_email(self, candidate_email: str, candidate_name: str,
                                                   job_title: str, company_name: str, new_status: str) -> bool:
        """Send application status change notification email to candidate"""
        
        # Map status to user-friendly text and color
        status_mapping = {
            'APPLIED': {'text': 'Application Received', 'color': '#3b82f6', 'message': 'Your application has been received and is under review.'},
            'INTERVIEW_SCHEDULED': {'text': 'Interview Scheduled', 'color': '#8b5cf6', 'message': 'Congratulations! You have been selected for an interview.'},
            'OFFERED': {'text': 'Job Offer Extended', 'color': '#f59e0b', 'message': 'Congratulations! We are pleased to extend you a job offer for this position.'},
            'REJECTED': {'text': 'Application Not Selected', 'color': '#ef4444', 'message': 'Unfortunately, we have decided to move forward with other candidates.'},
            'HIRED': {'text': 'Congratulations - You\'re Hired!', 'color': '#10b981', 'message': 'Great news! You have been selected for this position.'}
        }
        
        status_info = status_mapping.get(new_status, {
            'text': new_status,
            'color': '#6b7280',
            'message': f'Your application status has been updated to: {new_status}'
        })
        
        subject = f"Application Status Update - {job_title} at {company_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Application Status Update</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, {status_info['color']} 0%, {status_info['color']}dd 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .status-badge {{ display: inline-block; background: {status_info['color']}; color: white; padding: 10px 20px; border-radius: 20px; font-weight: bold; margin: 20px 0; }}
                .job-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {status_info['color']}; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
                .btn {{ display: inline-block; background: {status_info['color']}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1> Application Status Update</h1>
                </div>
                <div class="content">
                    <p>Dear {candidate_name},</p>
                    
                    <p>Your application status has been updated:</p>
                    
                    <div class="status-badge">{status_info['text']}</div>
                    
                    <div class="job-details">
                        <h3>Job Details:</h3>
                        <p><strong>Position:</strong> {job_title}</p>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>New Status:</strong> {status_info['text']}</p>
                    </div>
                    
                    <p>{status_info['message']}</p>
                    
                    <div style="background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="margin-top: 0; color: #334155;">Application Status Options:</h4>
                        <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
                            <span style="background: #3b82f6; color: white; padding: 8px 16px; border-radius: 15px; font-size: 14px;">APPLIED</span>
                            <span style="background: #8b5cf6; color: white; padding: 8px 16px; border-radius: 15px; font-size: 14px;">INTERVIEW SCHEDULED</span>
                            <span style="background: #f59e0b; color: white; padding: 8px 16px; border-radius: 15px; font-size: 14px;">OFFERED</span>
                            <span style="background: #10b981; color: white; padding: 8px 16px; border-radius: 15px; font-size: 14px;">HIRED</span>
                            <span style="background: #ef4444; color: white; padding: 8px 16px; border-radius: 15px; font-size: 14px;">REJECTED</span>
                        </div>
                        <p style="font-size: 13px; color: #64748b; margin-bottom: 0; margin-top: 10px;">Your recruiter will update your status as your application progresses.</p>
                    </div>
                    
                    {'<p><strong>Next Steps:</strong></p><ul><li>Check your email for interview details</li><li>Prepare for your interview</li><li>Review the company and job description</li></ul>' if new_status == 'INTERVIEW_SCHEDULED' else ''}
                    
                    {'<p><strong>Next Steps:</strong></p><ul><li>Review the job offer details carefully</li><li>Respond within the specified timeframe</li><li>Contact the recruiter if you have any questions</li></ul>' if new_status == 'OFFERED' else ''}
                    
                    {'<p><strong>Next Steps:</strong></p><ul><li>Review and complete any required onboarding documents</li><li>Prepare for your first day</li><li>Contact HR for any questions</li></ul>' if new_status == 'HIRED' else ''}
                    
                    {'<p>Thank you for your interest in this position. We encourage you to continue exploring other opportunities on our platform.</p>' if new_status == 'REJECTED' else ''}
                    
                    <div style="text-align: center;">
                        <a href="http://localhost:3000/applications" class="btn">View My Applications</a>
                    </div>
                    
                    <p>Best regards,<br><strong>{company_name} Recruitment Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher.</p>
                    <p>© 2024 CV Matcher - Connecting Talent with Opportunity</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(candidate_email, subject, html_content)

    async def send_company_registration_notification_to_super_admin(self, company_name: str, admin_name: str, 
                                                                     admin_email: str, company_id: int) -> bool:
        """Send notification to super admin when new company registers"""
        # Get super admin email from environment or use default
        super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "aliboolmind228@gmail.com")
        
        subject = f" New Company Registration - {company_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>New Company Registration</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .company-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b; }}
                .btn {{ display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .btn-reject {{ background: #ef4444; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1> New Company Registration</h1>
                    <p style="margin: 0; opacity: 0.9;">Awaiting Your Approval</p>
                </div>
                <div class="content">
                    <p>Hello Super Admin,</p>
                    
                    <p>A new company has registered and is awaiting your approval:</p>
                    
                    <div class="company-details">
                        <h3 style="margin-top: 0;">Company Details:</h3>
                        <p><strong>Company Name:</strong> {company_name}</p>
                        <p><strong>Admin Name:</strong> {admin_name}</p>
                        <p><strong>Admin Email:</strong> {admin_email}</p>
                        <p><strong>Company ID:</strong> #{company_id}</p>
                        <p><strong>Status:</strong> <span style="background: #fef3c7; color: #d97706; padding: 5px 10px; border-radius: 10px;">PENDING</span></p>
                    </div>
                    
                    <p><strong>Action Required:</strong> Please review and approve or reject this company registration.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/super-admin/companies" class="btn">Review Company</a>
                    </div>
                    
                    <p>Best regards,<br><strong>CV Matcher System</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher Super Admin Panel.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(super_admin_email, subject, html_content)

    async def send_company_approval_email(self, company_name: str, admin_name: str, admin_email: str) -> bool:
        """Send approval notification to company admin"""
        subject = f"🎉 Company Approved - Welcome to CV Matcher!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Company Approved</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .features {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .btn {{ display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Congratulations!</h1>
                    <p style="margin: 0; opacity: 0.9;">Your Company Has Been Approved</p>
                </div>
                <div class="content">
                    <p>Dear {admin_name},</p>
                    
                    <p>Great news! Your company <strong>{company_name}</strong> has been approved by our Super Admin.</p>
                    
                    <div class="features">
                        <h3 style="margin-top: 0; color: #059669;">You Can Now:</h3>
                        <ul>
                            <li> Post job openings</li>
                            <li> Create and manage recruiters</li>
                            <li> Review candidate applications</li>
                            <li> Access analytics and reports</li>
                            <li> Select subscription plans</li>
                        </ul>
                    </div>
                    
                    <p><strong>Next Steps:</strong></p>
                    <ol>
                        <li>Login to your account</li>
                        <li>Complete your company profile</li>
                        <li>Select a subscription plan</li>
                        <li>Start posting jobs!</li>
                    </ol>
                    
                    <div style="text-align: center;">
                        <a href="http://localhost:3000/recruiter-login" class="btn">Login to Dashboard</a>
                    </div>
                    
                    <p>Welcome to CV Matcher!<br><strong>The CV Matcher Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(admin_email, subject, html_content)

    async def send_company_rejection_email(self, company_name: str, admin_name: str, admin_email: str) -> bool:
        """Send rejection notification to company admin"""
        subject = f"Company Registration Status - {company_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Company Registration Status</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .info-box {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Company Registration Status</h1>
                </div>
                <div class="content">
                    <p>Dear {admin_name},</p>
                    
                    <p>Thank you for your interest in CV Matcher.</p>
                    
                    <div class="info-box">
                        <p><strong>Status Update:</strong> Unfortunately, we are unable to approve the registration for <strong>{company_name}</strong> at this time.</p>
                    </div>
                    
                    <p><strong>What You Can Do:</strong></p>
                    <ul>
                        <li>Contact our support team for more information</li>
                        <li>Review and resubmit your application with correct details</li>
                        <li>Email us at: support@cvmatcher.com</li>
                    </ul>
                    
                    <p>We appreciate your understanding.</p>
                    
                    <p>Best regards,<br><strong>The CV Matcher Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(admin_email, subject, html_content)

    async def send_plan_selection_confirmation(self, company_name: str, admin_name: str, admin_email: str,
                                               plan_name: str, plan_price: float, super_admin_notify: bool = True) -> bool:
        """Send plan selection confirmation to company admin and optionally notify super admin"""
        subject = f" Subscription Confirmed - {plan_name} Plan"
        
        # Email to company admin
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Subscription Confirmed</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .plan-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #8b5cf6; }}
                .price {{ font-size: 32px; font-weight: bold; color: #8b5cf6; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1> Subscription Confirmed!</h1>
                </div>
                <div class="content">
                    <p>Dear {admin_name},</p>
                    
                    <p>Your subscription has been successfully activated!</p>
                    
                    <div class="plan-details">
                        <h3 style="margin-top: 0;">Subscription Details:</h3>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>Plan:</strong> {plan_name}</p>
                        <p class="price">${plan_price}/month</p>
                        <p><strong>Status:</strong> <span style="background: #d1fae5; color: #059669; padding: 5px 10px; border-radius: 10px;">Active</span></p>
                    </div>
                    
                    <p>You now have full access to all features included in your {plan_name} plan.</p>
                    
                    <p>Thank you for choosing CV Matcher!</p>
                    
                    <p>Best regards,<br><strong>The CV Matcher Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated confirmation from CV Matcher.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        admin_email_sent = await self.send_email(admin_email, subject, html_content)
        
        # Notify super admin
        if super_admin_notify:
            super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "aliboolmind228@gmail.com")
            super_admin_subject = f" New Subscription - {company_name} selected {plan_name}"
            
            super_admin_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>New Subscription</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1> New Subscription</h1>
                    </div>
                    <div class="content">
                        <p>Hello Super Admin,</p>
                        
                        <p>A company has selected a subscription plan:</p>
                        
                        <div class="details">
                            <p><strong>Company:</strong> {company_name}</p>
                            <p><strong>Admin:</strong> {admin_name} ({admin_email})</p>
                            <p><strong>Plan:</strong> {plan_name}</p>
                            <p><strong>Price:</strong> ${plan_price}/month</p>
                        </div>
                        
                        <p>Best regards,<br><strong>CV Matcher System</strong></p>
                    </div>
                    <div class="footer">
                        <p>This is an automated notification.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            await self.send_email(super_admin_email, super_admin_subject, super_admin_content)
        
        return admin_email_sent

    async def send_company_status_change_email(self, company_name: str, admin_name: str, admin_email: str,
                                               new_status: str, old_status: str) -> bool:
        """Send email when company status changes (suspended, activated, etc.)"""
        
        status_info = {
            'ACTIVE': {'color': '#10b981', 'title': 'Company Activated', 'message': 'Your company has been activated and you can now access all features.'},
            'SUSPENDED': {'color': '#ef4444', 'title': 'Company Suspended', 'message': 'Your company has been temporarily suspended. Please contact support.'},
            'REJECTED': {'color': '#ef4444', 'title': 'Company Rejected', 'message': 'Your company registration has been rejected.'}
        }
        
        info = status_info.get(new_status, {'color': '#6b7280', 'title': 'Company Status Update', 'message': f'Your company status has been updated to {new_status}.'})
        
        subject = f"{info['title']} - {company_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Company Status Update</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, {info['color']} 0%, {info['color']}dd 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .status-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {info['color']}; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{info['title']}</h1>
                </div>
                <div class="content">
                    <p>Dear {admin_name},</p>
                    
                    <div class="status-box">
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>Previous Status:</strong> {old_status}</p>
                        <p><strong>New Status:</strong> <span style="background: {info['color']}22; color: {info['color']}; padding: 5px 10px; border-radius: 10px; font-weight: bold;">{new_status}</span></p>
                    </div>
                    
                    <p>{info['message']}</p>
                    
                    {'<p><strong>What This Means:</strong><ul><li> Full access to all features</li><li> Can post jobs and manage recruiters</li><li>✅ Access to analytics and reports</li></ul></p>' if new_status == 'ACTIVE' else ''}
                    
                    {'<p><strong>Why This Happened:</strong><ul><li>Policy violation or suspicious activity</li><li>Payment issues</li><li>Other administrative reasons</li></ul><p><strong>Action Required:</strong> Contact our support team at support@cvmatcher.com</p></p>' if new_status == 'SUSPENDED' else ''}
                    
                    <p>If you have any questions, please contact our support team.</p>
                    
                    <p>Best regards,<br><strong>The CV Matcher Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(admin_email, subject, html_content)

    async def send_super_admin_login_email(self, admin_email: str, admin_name: str) -> bool:
        """Send login notification email to super admin"""
        subject = " Super Admin Login Detected"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Super Admin Login</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #7c3aed; }}
                .security-notice {{ background: #fef2f2; border: 1px solid #ef4444; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .btn {{ display: inline-block; background: #7c3aed; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1> Super Admin Login</h1>
                    <p style="margin: 0; opacity: 0.9;">Security Alert</p>
                </div>
                <div class="content">
                    <p>Hello {admin_name},</p>
                    
                    <p>You have successfully logged into your <strong>Super Admin</strong> account.</p>
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0;">Login Details:</h3>
                        <p><strong>Account:</strong> {admin_email}</p>
                        <p><strong>Role:</strong> Super Administrator</p>
                        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>Access Level:</strong> Full System Access</p>
                    </div>
                    
                    <div class="security-notice">
                        <p><strong> Security Notice:</strong></p>
                        <p>If you did not initiate this login, please:</p>
                        <ul>
                            <li>Change your password immediately</li>
                            <li>Review account activity</li>
                            <li>Contact system security team</li>
                        </ul>
                    </div>
                    
                    <p><strong>As Super Admin, you have access to:</strong></p>
                    <ul>
                        <li> Company Management (Approve/Reject/Suspend)</li>
                        <li> Subscription Management</li>
                        <li> System Analytics and Reports</li>
                        <li> Platform Configuration</li>
                        <li> User Management</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="http://localhost:3000/super-admin/dashboard" class="btn">Access Dashboard</a>
                    </div>
                    
                    <p>Best regards,<br><strong>CV Matcher Security System</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated security notification from CV Matcher.</p>
                    <p>© 2024 CV Matcher - Super Admin Panel</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(admin_email, subject, html_content)

    async def send_admin_status_change_email(self, admin_name: str, admin_email: str, 
                                             new_status: str, old_status: str) -> bool:
        """Send email notification when company admin's account status is changed"""
        
        status_color = '#10b981' if new_status == 'Activated' else '#ef4444'
        
        subject = f"Account Status Update - {new_status}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Account Status Update</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, {status_color} 0%, {status_color}dd 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .status-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {status_color}; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Account Status Update</h1>
                </div>
                <div class="content">
                    <p>Dear {admin_name},</p>
                    
                    <p>Your company admin account status has been updated by the Super Administrator.</p>
                    
                    <div class="status-box">
                        <p><strong>Account:</strong> {admin_email}</p>
                        <p><strong>Previous Status:</strong> {old_status}</p>
                        <p><strong>New Status:</strong> <span style="background: {status_color}22; color: {status_color}; padding: 5px 10px; border-radius: 10px; font-weight: bold;">{new_status}</span></p>
                    </div>
                    
                    {'<p><strong>Your account has been activated!</strong></p><p>You can now login and access all features of your company dashboard.</p>' if new_status == 'Activated' else ''}
                    
                    {'<p><strong>Your account has been deactivated.</strong></p><p>If you believe this is a mistake, please contact the Super Administrator or support team.</p><p>Email: support@cvmatcher.com</p>' if new_status == 'Deactivated' else ''}
                    
                    <p>If you have any questions, please contact our support team.</p>
                    
                    <p>Best regards,<br><strong>The CV Matcher Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(admin_email, subject, html_content)

    async def send_plan_request_to_super_admin(self, company_name: str, admin_name: str, admin_email: str,
                                               plan_name: str, plan_price: float, company_id: int) -> bool:
        """Send notification to super admin when company admin requests a subscription plan"""
        super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "alimughal228@gmail.com")
        
        subject = f"Subscription Request - {company_name} wants {plan_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Subscription Plan Request</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .request-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #8b5cf6; }}
                .btn-approve {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .btn-reject {{ display: inline-block; background: #ef4444; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Subscription Request</h1>
                    <p style="margin: 0; opacity: 0.9;">Awaiting Your Approval</p>
                </div>
                <div class="content">
                    <p>Hello Super Admin,</p>
                    
                    <p>A company admin has requested a subscription plan:</p>
                    
                    <div class="request-box">
                        <h3 style="margin-top: 0;">Request Details:</h3>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>Requested By:</strong> {admin_name} ({admin_email})</p>
                        <p><strong>Plan Requested:</strong> {plan_name}</p>
                        <p><strong>Price:</strong> ${plan_price}/month</p>
                        <p><strong>Status:</strong> <span style="background: #fef3c7; color: #d97706; padding: 5px 10px; border-radius: 10px;">PENDING</span></p>
                    </div>
                    
                    <p><strong>Action Required:</strong> Please review and approve or reject this subscription request.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/super-admin/dashboard" class="btn-approve">Review Request</a>
                    </div>
                    
                    <p>Best regards,<br><strong>CV Matcher System</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(super_admin_email, subject, html_content)

    async def send_plan_approval_to_company_admin(self, company_name: str, admin_name: str, admin_email: str,
                                                   plan_name: str, plan_price: float) -> bool:
        """Send approval notification when super admin approves subscription plan request"""
        subject = f"Subscription Approved - {plan_name} Plan Activated!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Subscription Approved</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .plan-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981; }}
                .btn {{ display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Subscription Approved!</h1>
                    <p style="margin: 0; opacity: 0.9;">Your Plan is Now Active</p>
                </div>
                <div class="content">
                    <p>Dear {admin_name},</p>
                    
                    <p>Great news! Your subscription request has been approved by the Super Admin.</p>
                    
                    <div class="plan-box">
                        <h3 style="margin-top: 0;">Active Subscription:</h3>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>Plan:</strong> {plan_name}</p>
                        <p><strong>Price:</strong> ${plan_price}/month</p>
                        <p><strong>Status:</strong> <span style="background: #d1fae5; color: #059669; padding: 5px 10px; border-radius: 10px; font-weight: bold;">ACTIVE</span></p>
                    </div>
                    
                    <p>You now have full access to all features included in your {plan_name} plan.</p>
                    
                    <div style="text-align: center;">
                        <a href="http://localhost:3000/recruiter/dashboard" class="btn">Access Dashboard</a>
                    </div>
                    
                    <p>Thank you for choosing CV Matcher!</p>
                    
                    <p>Best regards,<br><strong>The CV Matcher Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(admin_email, subject, html_content)

    async def send_plan_rejection_to_company_admin(self, company_name: str, admin_name: str, admin_email: str,
                                                    plan_name: str, rejection_reason: str = None) -> bool:
        """Send rejection notification when super admin rejects subscription plan request"""
        subject = f"Subscription Request Update - {company_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Subscription Request Update</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .info-box {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Subscription Request Update</h1>
                </div>
                <div class="content">
                    <p>Dear {admin_name},</p>
                    
                    <p>We wanted to update you on your subscription request for <strong>{company_name}</strong>.</p>
                    
                    <div class="info-box">
                        <p><strong>Requested Plan:</strong> {plan_name}</p>
                        <p><strong>Status:</strong> Under Review</p>
                        {f"<p><strong>Note:</strong> {rejection_reason}</p>" if rejection_reason else ""}
                    </div>
                    
                    <p>Your subscription request is being reviewed. You can:</p>
                    <ul>
                        <li>Contact our support team for more information</li>
                        <li>Request a different plan</li>
                        <li>Email us at: support@cvmatcher.com</li>
                    </ul>
                    
                    <p>Thank you for your patience.</p>
                    
                    <p>Best regards,<br><strong>The CV Matcher Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(admin_email, subject, html_content)

# Create global instance
email_service = EmailService()
