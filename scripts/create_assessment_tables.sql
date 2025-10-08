-- Create assessments table
CREATE TABLE IF NOT EXISTS assessments (
    application_id INTEGER PRIMARY KEY,
    candidate_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    score DECIMAL(5,2),
    start_time TIMESTAMP,
    completion_time TIMESTAMP,
    cheat_attempts INTEGER DEFAULT 0,
    mcq_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create job_mcqs table
CREATE TABLE IF NOT EXISTS job_mcqs (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer CHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, question_number)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_assessments_candidate_id ON assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_assessments_job_id ON assessments(job_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);
CREATE INDEX IF NOT EXISTS idx_job_mcqs_job_id ON job_mcqs(job_id);

-- Add foreign key constraints if tables exist
DO $$ 
BEGIN
    -- Add foreign key to applications table if it exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'applications') THEN
        ALTER TABLE assessments ADD CONSTRAINT fk_assessments_application 
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE;
    END IF;
    
    -- Add foreign key to jobs table if it exists  
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'jobs') THEN
        ALTER TABLE job_mcqs ADD CONSTRAINT fk_job_mcqs_job 
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
    END IF;
END $$;
