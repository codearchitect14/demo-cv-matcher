-- Add recruiter assignment functionality to jobs table
-- This script adds recruiter_id column and related indexes

-- Add recruiter_id column to jobs table
ALTER TABLE jobs 
ADD COLUMN recruiter_id INTEGER;

-- Add foreign key constraint to recruiters table
ALTER TABLE jobs 
ADD CONSTRAINT fk_jobs_recruiter_id 
FOREIGN KEY (recruiter_id) REFERENCES recruiters(id) ON DELETE SET NULL;

-- Create index for performance
CREATE INDEX IF NOT EXISTS ix_jobs_recruiter_id ON jobs (recruiter_id);

-- Update existing jobs with a default recruiter (assuming recruiter with id=1 exists)
-- You can change this to any existing recruiter ID
UPDATE jobs 
SET recruiter_id = 1 
WHERE recruiter_id IS NULL;

-- Make recruiter_id NOT NULL after setting default values
ALTER TABLE jobs 
ALTER COLUMN recruiter_id SET NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN jobs.recruiter_id IS 'ID of the recruiter assigned to manage this job';

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'jobs' 
AND column_name = 'recruiter_id';



