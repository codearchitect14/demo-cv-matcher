# Job Recommendation System Frontend

This is the React frontend for the Job Recommendation System with authentication features.

## Features

- **Authentication System**
  - Sign Up: Create new user accounts
  - Sign In: Login with existing credentials
  - Logout: Secure logout functionality
  - Token-based authentication

- **User Management**
  - Automatic token management
  - User session persistence
  - Protected routes

- **Main Application Features**
  - Candidate registration and management
  - Job posting and management
  - Experience tracking
  - Job recommendations
  - Admin dashboard
  - GDPR management

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open your browser and go to `http://localhost:3000`

## Authentication Flow

### Sign Up
1. Click "Sign Up" on the login page
2. Fill in all required fields:
   - Full Name
   - Email
   - Password
   - Location
   - Domain
   - Salary expectations (optional)
   - Professional Summary
3. Click "Sign Up" to create your account
4. You'll be automatically logged in and redirected to the main application

### Sign In
1. Enter your email and password
2. Click "Sign In"
3. You'll be redirected to the main application

### Logout
1. Click the "Logout" button in the top navigation
2. You'll be redirected to the login page

## API Integration

The frontend integrates with the following backend APIs:

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user info

## File Structure

```
frontend/src/
├── components/
│   ├── SignIn.js          # Login component
│   ├── SignUp.js          # Registration component
│   ├── CandidateRegistration.js
│   ├── ExperienceForm.js
│   ├── JobPosting.js
│   ├── JobRecommendations.js
│   ├── CandidateRecommendations.js
│   ├── AdminDashboard.js
│   └── GDPRManagement.js
├── App.js                 # Main application component
├── api.js                 # API service functions
├── index.js               # Application entry point
└── index.css              # Styles
```

## Development

- The app uses React hooks for state management
- Axios for API calls
- CSS for styling
- Local storage for token persistence

## Troubleshooting

1. **Authentication Issues**
   - Make sure the backend API is running on port 8000
   - Check browser console for API errors
   - Clear browser storage if token issues persist

2. **CORS Issues**
   - Ensure the backend has CORS properly configured
   - Check that the proxy setting in package.json is correct

3. **API Connection Issues**
   - Verify the backend is running and accessible
   - Check the API_BASE_URL in api.js
   - Ensure all required environment variables are set

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App (not recommended) 