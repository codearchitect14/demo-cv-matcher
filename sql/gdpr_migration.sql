-- GDPR Compliance Migration Scripts
-- Run these scripts in your PostgreSQL database

-- 1. Enable pgcrypto extension for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. Add consent_given column to candidates table
ALTER TABLE candidates 
ADD COLUMN IF NOT EXISTS consent_given BOOLEAN NOT NULL DEFAULT FALSE;

-- 3. Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    admin_id INTEGER,
    action_type VARCHAR(50) NOT NULL CHECK (action_type IN ('data_deletion', 'consent_update', 'access_log', 'data_export')),
    details TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create indexes for audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_user_action ON audit_logs(user_id, action_type);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_logs(admin_id);

-- 5. Create index for consent_given
CREATE INDEX IF NOT EXISTS idx_candidate_consent ON candidates(consent_given);

-- 6. Function to encrypt salary fields (optional - for additional security)
CREATE OR REPLACE FUNCTION encrypt_salary(salary_value NUMERIC, encryption_key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(pgp_sym_encrypt(salary_value::TEXT, encryption_key), 'base64');
END;
$$ LANGUAGE plpgsql;

-- 7. Function to decrypt salary fields
CREATE OR REPLACE FUNCTION decrypt_salary(encrypted_salary TEXT, encryption_key TEXT)
RETURNS NUMERIC AS $$
BEGIN
    RETURN pgp_sym_decrypt(decode(encrypted_salary, 'base64'), encryption_key)::NUMERIC;
END;
$$ LANGUAGE plpgsql;

-- 8. Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 9. Apply trigger to audit_logs table
CREATE TRIGGER update_audit_logs_updated_at
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 10. Create view for GDPR compliance reporting
CREATE OR REPLACE VIEW gdpr_compliance_report AS
SELECT 
    c.id as candidate_id,
    c.name,
    c.consent_given,
    c.created_at as profile_created,
    c.updated_at as profile_updated,
    COUNT(DISTINCT a.id) as application_count,
    COUNT(DISTINCT i.id) as interaction_count,
    COUNT(DISTINCT al.id) as audit_log_count,
    MAX(al.created_at) as last_audit_action
FROM candidates c
LEFT JOIN applications a ON c.id = a.candidate_id
LEFT JOIN interaction_logs i ON c.id = i.candidate_id
LEFT JOIN audit_logs al ON c.id = al.user_id
GROUP BY c.id, c.name, c.consent_given, c.created_at, c.updated_at;

-- 11. Create function to get GDPR summary for a candidate
CREATE OR REPLACE FUNCTION get_gdpr_summary(candidate_id_param INTEGER)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'candidate_id', c.id,
        'name', c.name,
        'consent_given', c.consent_given,
        'profile_created', c.created_at,
        'profile_updated', c.updated_at,
        'data_summary', json_build_object(
            'applications', COUNT(DISTINCT a.id),
            'interactions', COUNT(DISTINCT i.id),
            'audit_logs', COUNT(DISTINCT al.id)
        ),
        'last_audit_action', MAX(al.created_at)
    ) INTO result
    FROM candidates c
    LEFT JOIN applications a ON c.id = a.candidate_id
    LEFT JOIN interaction_logs i ON c.id = i.candidate_id
    LEFT JOIN audit_logs al ON c.id = al.user_id
    WHERE c.id = candidate_id_param
    GROUP BY c.id, c.name, c.consent_given, c.created_at, c.updated_at;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 12. Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON audit_logs TO your_app_user;
GRANT SELECT ON gdpr_compliance_report TO your_app_user;
GRANT EXECUTE ON FUNCTION get_gdpr_summary(INTEGER) TO your_app_user;

-- 13. Create function to anonymize candidate data (for GDPR right to be forgotten)
CREATE OR REPLACE FUNCTION anonymize_candidate(candidate_id_param INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    -- Update candidate with anonymized data
    UPDATE candidates 
    SET 
        name = 'ANONYMIZED_' || candidate_id_param,
        location = 'ANONYMIZED',
        domain = 'ANONYMIZED',
        expected_salary_min = NULL,
        expected_salary_max = NULL,
        summary = 'ANONYMIZED',
        consent_given = FALSE,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = candidate_id_param;
    
    -- Anonymize experiences
    UPDATE candidate_experiences 
    SET 
        skill = 'ANONYMIZED',
        description = 'ANONYMIZED',
        updated_at = CURRENT_TIMESTAMP
    WHERE candidate_id = candidate_id_param;
    
    -- Log the anonymization
    INSERT INTO audit_logs (user_id, action_type, details, created_at)
    VALUES (
        candidate_id_param, 
        'data_deletion', 
        json_build_object('action', 'anonymization', 'candidate_id', candidate_id_param)::TEXT,
        CURRENT_TIMESTAMP
    );
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- 14. Grant permission for anonymization function
GRANT EXECUTE ON FUNCTION anonymize_candidate(INTEGER) TO your_app_user; 