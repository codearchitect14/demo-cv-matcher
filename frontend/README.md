# Job Recommendation System Frontend

A minimal React frontend for testing the job recommendation system backend.

## Features

### Candidate Functions
- ✅ Candidate registration with GDPR consent
- ✅ Add candidate experience and skills
- ✅ View job recommendations with ML ranking
- ✅ Apply or reject jobs with interaction logging

### Employer Functions
- ✅ Post new jobs with mandatory skills
- ✅ View candidate recommendations for jobs
- ✅ Accept or reject applications

### Admin Dashboard
- ✅ System overview with key metrics
- ✅ Analytics: jobs without applicants, candidates with zero visibility
- ✅ Skill gap analysis and job performance metrics
- ✅ System management: generate embeddings, retrain models

### GDPR Management
- ✅ Consent tracking and updates
- ✅ Data export for portability
- ✅ Complete data deletion with audit trail
- ✅ Audit log viewing

## Setup

### Prerequisites
- Node.js (v14 or higher)
- Backend API running on `http://localhost:8000`

### Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000`

## Usage

### Testing Candidate Functions

1. **Register a Candidate:**
   - Go to the "Candidate" tab
   - Fill out the registration form
   - Note the candidate ID that gets assigned

2. **Add Experience:**
   - Enter the candidate ID in the "Selected Candidate ID" field
   - Add skills and experience details
   - This will be used for job matching

3. **View Job Recommendations:**
   - The system will show recommended jobs based on:
     - Semantic similarity (FAISS embeddings)
     - Structured filtering (location, salary, skills)
     - ML ranking (personalization)
   - Toggle "Use ML Ranking" to test different ranking methods
   - Apply or reject jobs to log interactions

### Testing Employer Functions

1. **Post a Job:**
   - Go to the "Employer" tab
   - Fill out the job posting form
   - Add mandatory skills and requirements
   - Note the job ID that gets assigned

2. **View Candidate Recommendations:**
   - Enter the job ID in the "Selected Job ID" field
   - View recommended candidates based on:
     - Semantic matching
     - Skill requirements
     - Experience levels
   - Accept or reject candidates

### Testing Admin Functions

1. **Dashboard Overview:**
   - Go to the "Admin Dashboard" tab
   - View system statistics and health
   - Monitor application metrics

2. **Analytics:**
   - Switch to "Analytics" tab
   - View jobs without applicants
   - Check candidates with zero visibility
   - Analyze skill gaps

3. **System Management:**
   - Switch to "System" tab
   - Generate embeddings for semantic search
   - Retrain ML models with latest data
   - Monitor system statistics

### Testing GDPR Compliance

1. **Consent Management:**
   - Go to the "GDPR Management" tab
   - Enter a candidate ID
   - Update consent status
   - View current consent information

2. **Data Export:**
   - Export all user data in structured format
   - View complete data for portability

3. **Data Deletion:**
   - Delete all user data with audit trail
   - Confirm deletion with reason

4. **Audit Logs:**
   - View all GDPR-related activities
   - Track data access and modifications

## API Integration

The frontend integrates with all backend endpoints:

### Core APIs
- **Candidates:** Registration, experience management, profile updates
- **Jobs:** Posting, mandatory skills, job management
- **Applications:** Apply, status updates, application tracking
- **Recommendations:** Job and candidate recommendations with ML ranking
- **Interactions:** Logging user behavior for personalization

### Analytics APIs
- **Jobs without applicants:** Identify underperforming job postings
- **Candidates zero visibility:** Find candidates needing promotion
- **Skill gap analysis:** Compare demand vs supply
- **Application statistics:** Track application funnel

### System APIs
- **Embedding generation:** Create semantic search vectors
- **Model retraining:** Update ML models with new data
- **System health:** Monitor backend status
- **System statistics:** Track system usage

### GDPR APIs
- **Consent management:** Track and update user consent
- **Data export:** Export user data for portability
- **Data deletion:** Complete data removal with audit trail
- **Audit logging:** Track all GDPR-related activities

## Testing Workflow

### 1. Setup Test Data
```bash
# Start backend
uvicorn api.main:app --reload

# Start frontend
cd frontend && npm start
```

### 2. Test Candidate Flow
1. Register a candidate with skills
2. Add experience details
3. View job recommendations
4. Apply to jobs and log interactions

### 3. Test Employer Flow
1. Post a job with requirements
2. View candidate recommendations
3. Accept/reject applications

### 4. Test Admin Functions
1. Generate embeddings
2. Retrain models
3. View analytics dashboard

### 5. Test GDPR Compliance
1. Update consent status
2. Export user data
3. View audit logs
4. Test data deletion

## Troubleshooting

### Common Issues

1. **Backend Connection Error:**
   - Ensure backend is running on `http://localhost:8000`
   - Check CORS settings in backend

2. **API Errors:**
   - Check browser console for error details
   - Verify backend logs for API issues

3. **Component Not Loading:**
   - Check if all dependencies are installed
   - Restart the development server

### Debug Mode

Enable debug logging in the browser console:
```javascript
// In browser console
localStorage.setItem('debug', 'true');
```

## Development

### Project Structure
```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── CandidateRegistration.js
│   │   ├── ExperienceForm.js
│   │   ├── JobRecommendations.js
│   │   ├── JobPosting.js
│   │   ├── CandidateRecommendations.js
│   │   ├── AdminDashboard.js
│   │   └── GDPRManagement.js
│   ├── api.js
│   ├── App.js
│   ├── index.js
│   └── index.css
├── package.json
└── README.md
```

### Adding New Features

1. **Create new component** in `src/components/`
2. **Add API methods** in `src/api.js`
3. **Update App.js** to include new component
4. **Test integration** with backend

## Production Build

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Contributing

1. Follow the existing code structure
2. Test all API integrations
3. Ensure GDPR compliance features work
4. Update documentation as needed 