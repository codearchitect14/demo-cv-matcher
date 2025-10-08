"""
Email templates for the enhanced email service
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class EmailTemplates:
    """Email template generator with caching support"""
    
    @staticmethod
    def get_base_styles() -> str:
        """Get base CSS styles for all email templates"""
        return """
        <style>
            body { 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                color: #333; 
                margin: 0; 
                padding: 0; 
                background-color: #f4f4f4;
            }
            .container { 
                max-width: 600px; 
                margin: 0 auto; 
                background-color: white;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .header { 
                background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                color: white; 
                padding: 25px; 
                border-radius: 8px 8px 0 0; 
                text-align: center;
            }
            .content { 
                background: #f8f9fa; 
                padding: 30px; 
                border-radius: 0 0 8px 8px; 
            }
            .footer { 
                text-align: center; 
                margin-top: 20px; 
                color: #666; 
                font-size: 12px; 
                padding: 20px;
                background-color: #f8f9fa;
                border-top: 1px solid #e9ecef;
            }
            .btn { 
                display: inline-block; 
                background: #10b981; 
                color: white; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 6px; 
                margin: 10px 0; 
                font-weight: 600;
            }
            .btn:hover {
                background: #059669;
            }
            .info-box { 
                background: #e8f5e8; 
                padding: 15px; 
                border-radius: 8px; 
                margin: 20px 0; 
                border-left: 4px solid #4caf50; 
            }
            .warning-box { 
                background: #fef3c7; 
                padding: 15px; 
                border-radius: 8px; 
                margin: 20px 0; 
                border-left: 4px solid #f59e0b; 
            }
            .status-box {
                background: #f0f9ff;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #3b82f6;
            }
            .job-details {
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border: 1px solid #e5e7eb;
            }
            .candidate-details {
                background: #f9fafb;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                border-left: 3px solid #10b981;
            }
            .footer-links {
                margin: 15px 0;
            }
            .footer-links a {
                color: #10b981;
                text-decoration: none;
                margin: 0 10px;
            }
            .footer-links a:hover {
                text-decoration: underline;
            }
        </style>
        """
    
    @staticmethod
    def sub_recruiter_welcome(recruiter_name: str, company_name: str, 
                             recruiter_email: str, login_credentials: Optional[Dict] = None) -> str:
        """Generate sub-recruiter welcome email template"""
        
        credentials_section = ""
        if login_credentials:
            credentials_section = f"""
            <div class="info-box">
                <h3 style="margin-top: 0; color: #2e7d32;">Your Login Credentials:</h3>
                <p><strong>Email:</strong> {recruiter_email}</p>
                <p><strong>Password:</strong> {login_credentials.get('password', 'Please check with your admin')}</p>
                <p><strong>Dashboard:</strong> <a href="http://localhost:3000/sub-recruiter/dashboard" style="color: #2e7d32;">http://localhost:3000/sub-recruiter/dashboard</a></p>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to {company_name} - Sub-Recruiter Account</title>
            {EmailTemplates.get_base_styles()}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {company_name}!</h1>
                    <p style="margin: 0; opacity: 0.9;">Your Sub-Recruiter Account is Ready</p>
                </div>
                <div class="content">
                    <h2>Hello {recruiter_name}!</h2>
                    <p>Your <strong>Sub-Recruiter</strong> account has been successfully created for <strong>{company_name}</strong>.</p>
                    
                    {credentials_section}
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0; color: #2e7d32;">Your Role as Sub-Recruiter:</h3>
                        <ul>
                            <li><strong>📋 Manage Assigned Jobs</strong> - You'll receive job assignments from your Company Admin</li>
                            <li><strong>👥 Review Candidate Applications</strong> - Evaluate candidates for your assigned positions</li>
                            <li><strong>📊 Update Application Statuses</strong> - Move candidates through the hiring process</li>
                            <li><strong>💬 Communicate with Candidates</strong> - Provide updates and feedback</li>
                        </ul>
                    </div>
                    
                    <div class="warning-box">
                        <h4 style="margin-top: 0; color: #92400e;">Important Notes:</h4>
                        <ul>
                            <li>You can only access jobs assigned to you by your Company Admin</li>
                            <li>You cannot create new jobs or recruiters</li>
                            <li>All your actions are monitored and logged for compliance</li>
                        </ul>
                    </div>
                    
                    <p>Click the button below to access your sub-recruiter dashboard:</p>
                    <div style="text-align: center;">
                        <a href="http://localhost:3000/sub-recruiter/dashboard" class="btn">Access Sub-Recruiter Dashboard</a>
                    </div>
                    
                    <p>If you have any questions, please contact your Company Admin or our support team.</p>
                    <p>Best regards,<br><strong>HR Team at {company_name}</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated message from CV Matcher.</p>
                    <div class="footer-links">
                        <a href="http://localhost:3000/sub-recruiter/dashboard">Dashboard</a>
                        <a href="mailto:support@cvmatcher.com">Support</a>
                        <a href="http://localhost:3000">Home</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    @staticmethod
    def job_assignment(recruiter_name: str, job_title: str, company_name: str,
                      job_id: int, admin_name: str) -> str:
        """Generate job assignment email template"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>New Job Assignment - {job_title}</title>
            {EmailTemplates.get_base_styles()}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Job Assignment</h1>
                    <p style="margin: 0; opacity: 0.9;">You've been assigned to manage a new position</p>
                </div>
                <div class="content">
                    <h2>Hello {recruiter_name}!</h2>
                    <p><strong>{admin_name}</strong> has assigned you to manage a new job position at <strong>{company_name}</strong>.</p>
                    
                    <div class="job-details">
                        <h3 style="margin-top: 0; color: #1e40af;">Job Details:</h3>
                        <p><strong>Position:</strong> {job_title}</p>
                        <p><strong>Job ID:</strong> #{job_id}</p>
                        <p><strong>Assigned by:</strong> {admin_name}</p>
                        <p><strong>Company:</strong> {company_name}</p>
                    </div>
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0; color: #2e7d32;">Your Responsibilities:</h3>
                        <ul>
                            <li>Review all applications for this position</li>
                            <li>Evaluate candidate qualifications and experience</li>
                            <li>Update candidate application statuses</li>
                            <li>Communicate with candidates about next steps</li>
                            <li>Provide feedback to your Company Admin</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="http://localhost:3000/sub-recruiter/dashboard" class="btn">View Job Details</a>
                    </div>
                    
                    <p>Please log into your dashboard to see the full job description and start reviewing applications.</p>
                    <p>Best regards,<br><strong>{admin_name}</strong><br>Company Admin at {company_name}</p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher.</p>
                    <div class="footer-links">
                        <a href="http://localhost:3000/sub-recruiter/dashboard">Dashboard</a>
                        <a href="mailto:support@cvmatcher.com">Support</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    @staticmethod
    def candidate_application_notification(recruiter_name: str, candidate_name: str,
                                         job_title: str, company_name: str,
                                         application_id: int) -> str:
        """Generate candidate application notification email"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>New Candidate Application - {job_title}</title>
            {EmailTemplates.get_base_styles()}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Candidate Application</h1>
                    <p style="margin: 0; opacity: 0.9;">A candidate has applied for your assigned job</p>
                </div>
                <div class="content">
                    <h2>Hello {recruiter_name}!</h2>
                    <p>You have received a new candidate application for one of your assigned positions at <strong>{company_name}</strong>.</p>
                    
                    <div class="candidate-details">
                        <h3 style="margin-top: 0; color: #10b981;">Application Details:</h3>
                        <p><strong>Candidate:</strong> {candidate_name}</p>
                        <p><strong>Position:</strong> {job_title}</p>
                        <p><strong>Application ID:</strong> #{application_id}</p>
                        <p><strong>Status:</strong> Applied</p>
                        <p><strong>Company:</strong> {company_name}</p>
                    </div>
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0; color: #2e7d32;">Next Steps:</h3>
                        <ul>
                            <li>Review the candidate's profile and CV</li>
                            <li>Evaluate their qualifications against job requirements</li>
                            <li>Update the application status (Interview/Rejected/Offered)</li>
                            <li>Communicate with the candidate about next steps</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="http://localhost:3000/sub-recruiter/dashboard" class="btn">Review Application</a>
                    </div>
                    
                    <p>Please review this application promptly to maintain a good candidate experience.</p>
                    <p>Best regards,<br><strong>CV Matcher System</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from CV Matcher.</p>
                    <div class="footer-links">
                        <a href="http://localhost:3000/sub-recruiter/dashboard">Dashboard</a>
                        <a href="mailto:support@cvmatcher.com">Support</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    @staticmethod
    def candidate_status_update(candidate_name: str, job_title: str, 
                              new_status: str, company_name: str,
                              recruiter_name: str, next_steps: Optional[str] = None) -> str:
        """Generate candidate status update email"""
        
        status_colors = {
            "INTERVIEW_SCHEDULED": "#3b82f6",
            "REJECTED": "#ef4444", 
            "OFFERED": "#10b981",
            "HIRED": "#059669",
            "APPLIED": "#6b7280"
        }
        
        status_color = status_colors.get(new_status.upper(), "#6b7280")
        
        next_steps_section = ""
        if next_steps:
            next_steps_section = f"""
            <div class="info-box">
                <h3 style="margin-top: 0; color: #2e7d32;">Next Steps:</h3>
                <p>{next_steps}</p>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Application Status Update - {job_title}</title>
            {EmailTemplates.get_base_styles()}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Application Status Update</h1>
                    <p style="margin: 0; opacity: 0.9;">Your application status has been updated</p>
                </div>
                <div class="content">
                    <h2>Hello {candidate_name}!</h2>
                    <p>Your application status for the <strong>{job_title}</strong> position at <strong>{company_name}</strong> has been updated.</p>
                    
                    <div class="status-box" style="border-left-color: {status_color};">
                        <h3 style="margin-top: 0; color: {status_color};">Current Status: {new_status.replace('_', ' ').title()}</h3>
                        <p><strong>Position:</strong> {job_title}</p>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>Updated by:</strong> {recruiter_name}</p>
                    </div>
                    
                    {next_steps_section}
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0; color: #2e7d32;">What This Means:</h3>
                        <ul>
                            <li><strong>Applied:</strong> Your application has been received and is being reviewed</li>
                            <li><strong>Interview Scheduled:</strong> We'd like to schedule an interview with you</li>
                            <li><strong>Rejected:</strong> Unfortunately, we won't be moving forward with your application</li>
                            <li><strong>Offered:</strong> Congratulations! We'd like to extend an offer to you</li>
                            <li><strong>Hired:</strong> Welcome to the team!</li>
                        </ul>
                    </div>
                    
                    <p>If you have any questions about your application status, please don't hesitate to contact us.</p>
                    <p>Best regards,<br><strong>{recruiter_name}</strong><br>Recruiter at {company_name}</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from CV Matcher.</p>
                    <div class="footer-links">
                        <a href="http://localhost:3000/candidates/dashboard">Your Dashboard</a>
                        <a href="mailto:support@cvmatcher.com">Support</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content

# Template registry for caching
TEMPLATE_REGISTRY = {
    "sub_recruiter_welcome": EmailTemplates.sub_recruiter_welcome,
    "job_assignment": EmailTemplates.job_assignment,
    "candidate_application_notification": EmailTemplates.candidate_application_notification,
    "candidate_status_update": EmailTemplates.candidate_status_update,
}

def get_template(template_name: str, **kwargs) -> Optional[str]:
    """Get email template by name with parameters"""
    if template_name in TEMPLATE_REGISTRY:
        try:
            return TEMPLATE_REGISTRY[template_name](**kwargs)
        except Exception as e:
            logger.error(f"Error generating template {template_name}: {e}")
            return None
    else:
        logger.error(f"Template {template_name} not found in registry")
        return None

