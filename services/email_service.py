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
        self.from_email = "ali.mughal@boolmind.com"  # Default sender email
        
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
            print(f"DEBUG: Creating email message for {to_email}")
            message = Mail(
                from_email=from_email or self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            print(f"DEBUG: Sending email via SendGrid to {to_email}")
            # Send email asynchronously
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.sg.send, message)
            
            print(f"DEBUG: SendGrid response status: {response.status_code}")
            if response.status_code == 202:
                logger.info(f"Email sent successfully to {to_email}")
                print(f"DEBUG: Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}")
                print(f"DEBUG: Email failed to send. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            print(f"DEBUG: Exception in send_email: {str(e)}")
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
                        <li>📋 View your profile and applications</li>
                        <li>🔍 Browse new job opportunities</li>
                        <li>📊 Check your application status</li>
                        <li>🎯 Get personalized job recommendations</li>
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
                                         company_name: str, login_credentials: dict = None) -> bool:
        """Send welcome email to newly created recruiter"""
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
                    <p>Your recruiter account has been successfully created. You can now start managing jobs and candidates for {company_name}.</p>
                    
                    {credentials_section}
                    
                    <h3>What you can do:</h3>
                    <ul>
                        <li>View and manage job applications</li>
                        <li>Assign jobs to team members</li>
                        <li>Contact qualified candidates</li>
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

# Create global instance
email_service = EmailService()
