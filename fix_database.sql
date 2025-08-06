-- Fix the recruiter table columns from enum to string
-- This will allow us to insert string values

-- First, let's see what we have
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'recruiters' AND column_name IN ('domain', 'company_size');

-- Drop the enum columns and recreate as string
ALTER TABLE recruiters DROP COLUMN domain;
ALTER TABLE recruiters DROP COLUMN company_size;

-- Add them back as string columns
ALTER TABLE recruiters ADD COLUMN domain VARCHAR(50) NOT NULL;
ALTER TABLE recruiters ADD COLUMN company_size VARCHAR(20) NOT NULL;

-- Verify the changes
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'recruiters' AND column_name IN ('domain', 'company_size'); 