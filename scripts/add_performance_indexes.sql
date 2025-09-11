-- Performance optimization indexes for CV Matcher
-- Run this script to add indexes that will dramatically improve query performance

-- Jobs table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_domain ON jobs(domain);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_salary_range ON jobs(salary_min, salary_max);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- Candidates table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_candidates_domain ON candidates(domain);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_candidates_location ON candidates(location);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_candidates_created_at ON candidates(created_at DESC);

-- Applications table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_candidate_job ON applications(candidate_id, job_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_candidate_id ON applications(candidate_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_applications_created_at ON applications(created_at DESC);

-- Text search indexes for better ILIKE performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_title_gin ON jobs USING gin(to_tsvector('english', title));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_company_gin ON jobs USING gin(to_tsvector('english', company));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_description_gin ON jobs USING gin(to_tsvector('english', job_description));

-- Composite indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_domain_location ON jobs(domain, location);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_domain_salary ON jobs(domain, salary_min, salary_max);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_candidates_domain_location ON candidates(domain, location);

-- Update table statistics for better query planning
ANALYZE jobs;
ANALYZE candidates;
ANALYZE applications;
