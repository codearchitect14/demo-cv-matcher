-- Create company_subscriptions table to track which companies use which offer plans
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS company_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    offer_plan_id UUID NOT NULL REFERENCES offer_plans(id) ON DELETE RESTRICT,
    subscribed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Expired', 'Cancelled')),
    expires_at TIMESTAMPTZ, -- NULL means no expiration
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(company_id) -- Each company can only have one active subscription
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_company_subscriptions_company_id ON company_subscriptions (company_id);
CREATE INDEX IF NOT EXISTS idx_company_subscriptions_offer_plan_id ON company_subscriptions (offer_plan_id);
CREATE INDEX IF NOT EXISTS idx_company_subscriptions_status ON company_subscriptions (status);

-- Create a function to update the updated_at column
CREATE OR REPLACE FUNCTION update_company_subscriptions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to use the function before update
DROP TRIGGER IF EXISTS set_company_subscriptions_updated_at ON company_subscriptions;
CREATE TRIGGER set_company_subscriptions_updated_at
BEFORE UPDATE ON company_subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_company_subscriptions_updated_at();
