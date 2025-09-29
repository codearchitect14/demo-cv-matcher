# Sub-Recruiter Dashboard Setup

## Overview
A new sub-recruiter dashboard has been created at `/sub-recruiter/dashboard` that provides a separate layer for testing purposes without disturbing your existing application.

## Features
- **Job Management**: View all jobs assigned to the recruiter
- **Candidate Management**: View and manage candidates for each job
- **Status Updates**: Update candidate application status manually
- **Professional UI**: Clean, modern interface focused on assigned jobs only

## Access Control
- Only accessible to `tayyab10@boolmind.com`
- Other users will be redirected to an unauthorized page
- Completely separate from existing admin/recruiter dashboards

## Setup Instructions

### 1. Database Setup
To assign jobs to the test recruiter, run these SQL commands in your database:

```sql
-- Create or get the test recruiter
INSERT INTO recruiters (full_name, email, password_hash, company_id, created_at)
VALUES ('Tayyab Test', 'tayyab10@boolmind.com', '$2b$12$test', 1, NOW())
ON CONFLICT (email) DO NOTHING;

-- Get the recruiter ID
SELECT id FROM recruiters WHERE email = 'tayyab10@boolmind.com';

-- Assign some jobs to this recruiter (replace :recruiter_id with actual ID)
UPDATE jobs 
SET recruiter_id = :recruiter_id 
WHERE id IN (SELECT id FROM jobs LIMIT 5);
```

### 2. Test Data Creation
Create some test applications:

```sql
-- Create test applications for assigned jobs
INSERT INTO applications (candidate_id, job_id, status, applied_at)
SELECT 
    c.id as candidate_id,
    j.id as job_id,
    CASE (random() * 3)::int
        WHEN 0 THEN 'APPLIED'
        WHEN 1 THEN 'INTERVIEW_SCHEDULED'
        ELSE 'REJECTED'
    END as status,
    NOW() as applied_at
FROM candidates c
CROSS JOIN jobs j
WHERE j.recruiter_id = (SELECT id FROM recruiters WHERE email = 'tayyab10@boolmind.com')
LIMIT 10;
```

## API Endpoints

### Backend Endpoints (already created):
- `GET /api/v1/recruiter/assigned-jobs` - Get assigned jobs
- `GET /api/v1/recruiter/job-candidates/{job_id}` - Get candidates for a job
- `PUT /api/v1/recruiter/update-candidate-status` - Update candidate status
- `GET /api/v1/recruiter/candidate-details/{candidate_id}` - Get candidate details

### Frontend Routes:
- `/sub-recruiter/dashboard` - Main dashboard
- `/unauthorized` - Access denied page

## Usage

### 1. Login
- Use email: `tayyab10@boolmind.com`
- Use any password (authentication is simplified for testing)

### 2. Dashboard Features
- **Jobs View**: Shows all assigned jobs with applicant counts and status breakdown
- **Candidates View**: Click on a job to see all candidates who applied
- **Status Management**: Click on candidates to view details and update status
- **Professional UI**: Clean, responsive design with modern styling

### 3. Status Updates
The system reuses existing auto-update logic from `/my-applications`:
- Status changes are logged in `interaction_log` table
- Assessment scores are preserved
- All existing business logic is maintained

## File Structure

### Frontend Files:
- `frontend/src/components/SubRecruiterDashboard.js` - Main dashboard component
- `frontend/src/components/SubRecruiterDashboard.css` - Styling
- `frontend/src/components/Unauthorized.js` - Access denied page
- `frontend/src/App.js` - Updated with new routes

### Backend Files:
- `api/routers/sub_recruiter.py` - API endpoints
- `api/main.py` - Updated with new router

## Testing

### 1. Access Test
- Try accessing `/sub-recruiter/dashboard` with different emails
- Should only work with `tayyab10@boolmind.com`

### 2. Functionality Test
- View assigned jobs
- Click on jobs to see candidates
- Update candidate status
- View candidate details

### 3. Integration Test
- Verify status updates appear in main application
- Check that existing functionality is not affected

## Security Notes
- This is a testing layer and should not be used in production
- Authentication is simplified for testing purposes
- All existing security measures remain intact

## Troubleshooting

### No Jobs Assigned
- Run the SQL commands above to assign jobs
- Check that `assigned_recruiter_id` is set correctly

### No Candidates
- Create test applications using the SQL above
- Ensure candidates exist in the database

### API Errors
- Check that the backend is running
- Verify database connection
- Check console for error messages

## Next Steps
1. Set up test data using the SQL commands
2. Test the dashboard functionality
3. Verify integration with existing system
4. Remove or secure for production use
