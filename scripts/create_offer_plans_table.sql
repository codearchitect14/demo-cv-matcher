-- Create offer_plans table for Super Admin plan management
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS offer_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_name VARCHAR(255) NOT NULL UNIQUE,
    price DECIMAL(10,2) NOT NULL,
    job_post_limit INTEGER, -- NULL means unlimited
    recruiter_limit INTEGER NOT NULL,
    candidate_views INTEGER, -- NULL means unlimited
    analytics_level VARCHAR(50) NOT NULL CHECK (analytics_level IN ('Basic', 'Standard', 'Advanced')),
    support_level VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_offer_plans_status ON offer_plans (status);
CREATE INDEX IF NOT EXISTS idx_offer_plans_plan_name ON offer_plans (plan_name);

-- Create a function to update the updated_at column
CREATE OR REPLACE FUNCTION update_offer_plans_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to use the function before update
DROP TRIGGER IF EXISTS set_offer_plans_updated_at ON offer_plans;
CREATE TRIGGER set_offer_plans_updated_at
BEFORE UPDATE ON offer_plans
FOR EACH ROW
EXECUTE FUNCTION update_offer_plans_updated_at();
