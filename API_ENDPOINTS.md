# Job Recommendation System API Documentation

## Overview

The Job Recommendation System API provides intelligent job matching with semantic search, personalization, and ML-powered recommendations. All endpoints are async and use Pydantic for validation.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Authentication & User Management

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123",
  "location": "Lahore",
  "domain": "Software Development",
  "expected_salary_min": 80000,
  "expected_salary_max": 150000,
  "summary": "Experienced Python developer with 5 years in web development"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST /auth/login
Login with email and password.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### GET /auth/me
Get current user profile.

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "location": "Lahore",
  "domain": "Software Development",
  "expected_salary_min": 80000,
  "expected_salary_max": 150000,
  "summary": "Experienced Python developer with 5 years in web development",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Candidate Management

#### POST /candidates
Create a new candidate profile.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "location": "Lahore",
  "domain": "Software Development",
  "expected_salary_min": 80000,
  "expected_salary_max": 150000,
  "summary": "Experienced Python developer with 5 years in web development"
}
```

#### GET /candidates/{candidate_id}
Get candidate profile with experiences.

#### PUT /candidates/{candidate_id}
Update candidate profile (own profile only).

#### DELETE /candidates/{candidate_id}
Delete candidate profile (GDPR compliance).

#### POST /candidates/{candidate_id}/experience
Add experience to candidate profile.

**Request Body:**
```json
{
  "skill": "Python",
  "years": 5,
  "description": "Web development with Django and FastAPI"
}
```

#### PUT /candidates/{candidate_id}/experience/{experience_id}
Update candidate experience.

#### DELETE /candidates/{candidate_id}/experience/{experience_id}
Delete candidate experience.

#### GET /candidates/{candidate_id}/applications
Get candidate's applications.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 10, max: 100)

#### GET /candidates/{candidate_id}/interactions
Get candidate's interaction history.

**Query Parameters:**
- `days_back`: Days to look back (default: 30, max: 365)
- `interaction_types`: Filter by interaction types (optional)

### Job Management

#### POST /jobs
Create a new job posting.

**Request Body:**
```json
{
  "title": "Senior Python Developer",
  "location": "Lahore",
  "domain": "Software Development",
  "salary_min": 80000,
  "salary_max": 150000,
  "total_years_required": 3,
  "job_description": "We are looking for a senior Python developer with experience in FastAPI and PostgreSQL"
}
```

#### GET /jobs/{job_id}
Get job details with mandatory skills.

#### PUT /jobs/{job_id}
Update job posting.

#### DELETE /jobs/{job_id}
Delete job posting.

#### POST /jobs/{job_id}/mandatory-skills
Add mandatory skill to job.

**Request Body:**
```json
{
  "skill": "Python",
  "min_experience": 3
}
```

#### GET /jobs
List jobs with filters.

**Query Parameters:**
- `location`: Filter by location
- `domain`: Filter by domain
- `salary_min`: Minimum salary
- `salary_max`: Maximum salary
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 10, max: 100)

#### GET /jobs/{job_id}/applications
Get applications for a job.

### Application Management

#### POST /applications
Apply for a job.

**Request Body:**
```json
{
  "job_id": 1,
  "status": "applied"
}
```

#### GET /applications/{application_id}
Get application status.

#### PUT /applications/{application_id}/status
Update application status.

**Request Body:**
```json
{
  "status": "accepted"
}
```

#### GET /applications/candidate/{candidate_id}/applications
Get candidate's applications.

#### GET /applications/job/{job_id}/applications
Get applications for a job.

### Recommendations

#### GET /recommendations/candidates/{candidate_id}/job-recommendations
Get personalized job recommendations for a candidate.

**Query Parameters:**
- `limit`: Number of recommendations (default: 10, max: 50)
- `apply_filters`: Apply business rule filters (default: true)
- `strict_mode`: Use strict filtering mode (default: false)
- `use_ml_ranking`: Use ML-based ranking (default: true)

**Response:**
```json
[
  {
    "job_id": 1,
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "location": "Lahore",
    "domain": "Software Development",
    "salary_min": 80000,
    "salary_max": 150000,
    "similarity_score": 0.85,
    "filter_score": 0.9,
    "personalization_score": 0.88,
    "final_score": 0.87,
    "explanation": "High semantic match with your Python experience"
  }
]
```

#### GET /recommendations/jobs/{job_id}/candidate-recommendations
Get candidate recommendations for a job.

#### POST /recommendations/search/jobs
Semantic job search.

**Request Body:**
```json
{
  "query": "Python developer with Django experience",
  "limit": 10,
  "apply_filters": true,
  "strict_mode": false,
  "use_ml_ranking": true
}
```

#### POST /recommendations/search/candidates
Semantic candidate search.

### Interaction Tracking

#### POST /interactions
Log a user interaction with a job.

**Request Body:**
```json
{
  "job_id": 1,
  "interaction_type": "View"
}
```

**Valid interaction types:** "View", "Applied", "Rejected", "Saved"

#### GET /interactions/candidates/{candidate_id}/interactions
Get candidate's interaction history.

#### GET /interactions/candidates/{candidate_id}/behavior-patterns
Get candidate's behavior patterns for personalization.

#### GET /interactions/candidates/{candidate_id}/similar-users
Get users with similar behavior patterns.

### Analytics & Admin

#### GET /analytics/jobs-without-applicants
Get jobs with no applicants.

**Query Parameters:**
- `days_threshold`: Days threshold for no applicants (default: 7)
- `limit`: Number of jobs to return (default: 20, max: 100)

#### GET /analytics/candidates-zero-visibility
Get candidates with zero visibility/activity.

#### GET /analytics/skill-gap-analysis
Get skill demand vs availability analysis.

#### GET /analytics/application-stats
Get application statistics.

#### GET /analytics/job-performance
Get job performance metrics.

### System Management

#### POST /system/embeddings/generate
Generate embeddings for profiles/jobs.

**Request Body:**
```json
{
  "entity_type": "all",
  "entity_ids": [1, 2, 3]
}
```

#### POST /system/models/retrain
Trigger model retraining.

**Request Body:**
```json
{
  "model_type": "lightgbm",
  "force_retrain": false
}
```

#### GET /system/health
System health check.

#### GET /system/stats
Get system statistics.

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Authentication endpoints: 5 requests per minute
- Search endpoints: 10 requests per minute
- Other endpoints: 100 requests per minute

## Pagination

List endpoints support pagination with `skip` and `limit` parameters:
```
GET /jobs?skip=20&limit=10
```

## Filtering

Many endpoints support filtering with query parameters:
```
GET /jobs?location=Lahore&domain=Software Development&salary_min=80000
```

## Personalization

The system learns from user interactions to provide personalized recommendations:
- Job views, applications, and rejections are tracked
- ML models are trained on interaction history
- Recommendations are personalized based on behavior patterns

## Semantic Search

The system uses advanced NLP for semantic understanding:
- Job descriptions and candidate summaries are converted to embeddings
- FAISS vector database enables fast similarity search
- Results are filtered and ranked using business rules

## Security

- JWT tokens for authentication
- Password hashing with bcrypt
- Input validation with Pydantic
- CORS protection
- Rate limiting
- GDPR compliance for data deletion 