"""
SUPER ADMIN ROLE-BASED ACCESS CONTROL (RBAC) DOCUMENTATION

This file documents the strict separation between Super Admin and Company operations.

====================================================================================================
SUPER ADMIN ALLOWED ACTIONS
====================================================================================================

1. COMPANY MANAGEMENT (✅ ALLOWED)
   - Approve pending companies (PENDING → ACTIVE)
   - Reject pending companies (PENDING → REJECTED)
   - Suspend active companies (ACTIVE → SUSPENDED)
   - Activate suspended companies (SUSPENDED → ACTIVE)
   - View company list and details
   - Delete companies (if absolutely necessary)

2. COMPANY ADMIN MANAGEMENT (✅ ALLOWED)
   - Create company admins (for specific company)
   - View company admins list
   - Activate/Deactivate admin accounts
   - Reset admin passwords
   - Delete admins (with restrictions - not last admin)

3. SUBSCRIPTION MANAGEMENT (✅ ALLOWED)
   - Create/edit offer plans (Silver, Gold, Platinum)
   - Assign subscription plans to companies
   - Update subscription status
   - View all subscriptions

4. SYSTEM OVERVIEW (✅ ALLOWED)
   - View dashboard statistics (companies, recruiters, candidates, jobs, applications counts)
   - View system-wide analytics
   - Monitor platform health

====================================================================================================
SUPER ADMIN RESTRICTED ACTIONS (❌ FORBIDDEN)
====================================================================================================

1. COMPANY INTERNAL RECRUITERS (❌ FORBIDDEN)
   - Cannot create sub-recruiters for a company
   - Cannot modify sub-recruiter permissions
   - Cannot assign jobs to recruiters
   - Exception: Can manage Company Admins only (top-level management)

2. JOBS MANAGEMENT (❌ FORBIDDEN)
   - Cannot create jobs
   - Cannot edit job details
   - Cannot delete jobs
   - Cannot assign jobs to recruiters
   - Can VIEW jobs for oversight only

3. CANDIDATES MANAGEMENT (❌ FORBIDDEN)
   - Cannot create candidate profiles
   - Cannot edit candidate information
   - Cannot delete candidates
   - Can VIEW candidates for oversight only

4. APPLICATIONS MANAGEMENT (❌ FORBIDDEN)
   - Cannot view individual application details
   - Cannot change application status
   - Cannot communicate with candidates about applications
   - Can VIEW application counts for statistics only

5. MESSAGING & COMMUNICATION (❌ FORBIDDEN)
   - Cannot send messages to candidates
   - Cannot send messages to recruiters
   - Cannot access company communication channels
   - Exception: System-wide notifications to admins only

6. COMPANY INTERNAL DATA (❌ FORBIDDEN)
   - Cannot access company's job descriptions
   - Cannot view candidate resumes/profiles in detail
   - Cannot see application assessment scores
   - Cannot access company analytics (only system-wide)

====================================================================================================
IMPLEMENTATION STATUS
====================================================================================================

✅ IMPLEMENTED:
1. Super Admin authentication and authorization
2. Company approval/rejection/suspension with email notifications
3. Company admin management (create, update, activate/deactivate, delete)
4. Subscription plan management
5. Email notifications for all status changes
6. Restrictions middleware created

⏳ TO IMPLEMENT:
1. Add explicit checks in job/candidate/application endpoints to block super admin
2. Add warning messages when super admin attempts forbidden actions
3. Audit logging for super admin actions
4. Frontend: Hide forbidden actions from super admin UI

====================================================================================================
ENDPOINT MAPPING
====================================================================================================

ALLOWED ENDPOINTS (Super Admin Can Access):
- POST   /api/v1/super-admin/login
- GET    /api/v1/super-admin/me
- GET    /api/v1/super-admin/overview
- GET    /api/v1/super-admin/companies
- POST   /api/v1/super-admin/companies
- PUT    /api/v1/super-admin/companies/{id}
- DELETE /api/v1/super-admin/companies/{id}
- PUT    /api/v1/super-admin/companies/{id}/approve ✅
- PUT    /api/v1/super-admin/companies/{id}/reject ✅
- PUT    /api/v1/super-admin/companies/{id}/suspend ✅
- PUT    /api/v1/super-admin/companies/{id}/activate ✅
- GET    /api/v1/super-admin/companies/{id}/details (VIEW ONLY)
- GET    /api/v1/super-admin/companies/{company_id}/admins
- POST   /api/v1/super-admin/companies/{company_id}/admins
- PUT    /api/v1/super-admin/companies/{company_id}/admins/{admin_id}
- DELETE /api/v1/super-admin/companies/{company_id}/admins/{admin_id}
- GET    /api/v1/super-admin/offer-plans
- POST   /api/v1/super-admin/offer-plans
- PUT    /api/v1/super-admin/offer-plans/{id}
- DELETE /api/v1/super-admin/offer-plans/{id}
- GET    /api/v1/super-admin/company-subscriptions
- POST   /api/v1/super-admin/company-subscriptions
- PUT    /api/v1/super-admin/company-subscriptions/{id}/status

FORBIDDEN ENDPOINTS (Super Admin Cannot Access):
- POST   /api/v1/jobs (Create job) ❌
- PUT    /api/v1/jobs/{id} (Edit job) ❌
- DELETE /api/v1/jobs/{id} (Delete job) ❌
- POST   /api/v1/candidates (Create candidate) ❌
- PUT    /api/v1/candidates/{id} (Edit candidate) ❌
- DELETE /api/v1/candidates/{id} (Delete candidate) ❌
- PUT    /api/v1/applications/{id}/status (Change application status) ❌
- POST   /api/v1/recruiter/* (Recruiter-specific actions) ❌
- POST   /api/v1/sub-recruiter/* (Sub-recruiter actions) ❌
- POST   /api/v1/candidate-contact/* (Direct candidate communication) ❌

VIEW-ONLY ENDPOINTS (Super Admin Can View for Oversight):
- GET    /api/v1/jobs (List jobs - system overview)
- GET    /api/v1/candidates (List candidates - system overview)
- GET    /api/v1/applications (List applications - system overview)

====================================================================================================
EMAIL NOTIFICATIONS
====================================================================================================

EMAILS SENT TO SUPER ADMIN:
1. Super admin login ✅
2. New company registration (PENDING approval) ✅
3. Company selects subscription plan ✅

EMAILS SENT TO COMPANY ADMIN:
1. Company approved ✅
2. Company rejected ✅
3. Company suspended ✅
4. Company activated ✅
5. Admin account activated/deactivated ✅
6. Subscription plan assigned ✅

====================================================================================================
SECURITY NOTES
====================================================================================================

1. Super Admin is a PLATFORM ADMINISTRATOR, not a Company Administrator
2. Super Admin manages the platform infrastructure and company onboarding
3. Each company's internal operations are PRIVATE and managed by Company Admins
4. This separation ensures:
   - Data privacy between companies
   - Clear accountability (Company admins manage their own operations)
   - Super admin focuses on platform health and company management
   - No conflicts of interest

====================================================================================================
"""

