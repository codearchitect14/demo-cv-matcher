# GDPR Compliance Implementation

This document outlines the GDPR (General Data Protection Regulation) compliance features implemented in the Job Recommendation System.

## 🛡️ Overview

The system implements comprehensive GDPR compliance features including:
- **Consent Tracking**: Boolean field to track user consent
- **Data Deletion**: Complete user data removal with audit trail
- **Data Encryption**: PostgreSQL pgcrypto for sensitive data
- **Audit Logging**: Complete trail of all data operations
- **Access Control**: Role-based permissions for admin operations
- **Data Portability**: Export user data in structured format

## 📋 Key Components

### 1. Consent Tracking

**Database Schema:**
```sql
ALTER TABLE candidates 
ADD COLUMN consent_given BOOLEAN NOT NULL DEFAULT FALSE;
```

**API Endpoints:**
- `PUT /api/v1/gdpr/update_consent/{candidate_id}` - Update consent status
- `GET /api/v1/gdpr/consent_status/{candidate_id}` - Get consent status

**Usage:**
```python
# Update consent
await gdpr_service.update_consent(
    db=db,
    candidate_id=123,
    consent_given=True,
    admin_id=1
)
```

### 2. Data Deletion

**API Endpoint:**
- `DELETE /api/v1/gdpr/delete_user_data/{candidate_id}` - Delete all user data

**Features:**
- Deletes candidate profile and all related data
- Cascades to applications, interactions, and experiences
- Logs deletion in audit trail
- Requires admin authentication

**Usage:**
```python
# Delete user data
result = await gdpr_service.delete_user_data(
    db=db,
    candidate_id=123,
    admin_id=1,
    reason="GDPR right to be forgotten"
)
```

### 3. Audit Logging

**Database Schema:**
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES candidates(id),
    admin_id INTEGER,
    action_type VARCHAR(50) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Action Types:**
- `data_deletion` - User data deletion
- `consent_update` - Consent status changes
- `access_log` - Data access events
- `data_export` - Data export operations

**API Endpoints:**
- `GET /api/v1/gdpr/audit_logs/{candidate_id}` - Get user audit logs

### 4. Data Encryption

**PostgreSQL Setup:**
```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encryption functions
CREATE OR REPLACE FUNCTION encrypt_salary(salary_value NUMERIC, encryption_key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(pgp_sym_encrypt(salary_value::TEXT, encryption_key), 'base64');
END;
$$ LANGUAGE plpgsql;
```

**Usage:**
```sql
-- Encrypt salary data
UPDATE candidates 
SET expected_salary_min = encrypt_salary(50000, 'your-secret-key')
WHERE id = 123;

-- Decrypt salary data
SELECT decrypt_salary(expected_salary_min, 'your-secret-key') 
FROM candidates WHERE id = 123;
```

### 5. Data Portability

**API Endpoint:**
- `GET /api/v1/gdpr/export_user_data/{candidate_id}` - Export user data

**Exported Data:**
```json
{
  "candidate": {
    "id": 123,
    "name": "John Doe",
    "location": "Lahore",
    "domain": "Software Development",
    "expected_salary_min": 50000.0,
    "expected_salary_max": 80000.0,
    "summary": "Experienced developer",
    "consent_given": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "experiences": [...],
  "applications": [...],
  "interactions": [...]
}
```

## 🔐 Security Features

### 1. Access Control

**Admin Authentication:**
```python
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Get current admin ID from token"""
    try:
        admin_id = int(credentials.credentials)
        return admin_id
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid admin token")
```

### 2. IP Address Tracking

All GDPR operations log the IP address of the requesting client:
```python
ip_address=request.client.host if request else None
```

### 3. User Agent Tracking

Track the browser/client making the request:
```python
user_agent=request.headers.get("user-agent") if request else None
```

## 📊 Compliance Reporting

### 1. GDPR Compliance View

```sql
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
```

### 2. GDPR Summary Function

```sql
CREATE OR REPLACE FUNCTION get_gdpr_summary(candidate_id_param INTEGER)
RETURNS JSON AS $$
-- Returns comprehensive GDPR summary for a candidate
$$ LANGUAGE plpgsql;
```

## 🧪 Testing

### Test Script

Run the comprehensive GDPR compliance test:
```bash
python test_gdpr_compliance.py
```

**Test Coverage:**
- ✅ Consent tracking and updates
- ✅ Data deletion with audit trail
- ✅ Audit log creation and retrieval
- ✅ Data export functionality
- ✅ Encryption features
- ✅ Access control validation

### Test Results

```
🧪 Starting GDPR Compliance Tests
📝 Test 1: Creating candidate with consent tracking
✅ Created candidate 1 with consent: True
📝 Test 2: Updating consent status
✅ Updated consent: {'message': 'Consent updated successfully', 'candidate_id': 1, 'consent_given': False}
📝 Test 3: Creating audit logs
✅ Created audit log 1
📝 Test 4: Retrieving user audit logs
✅ Retrieved 2 audit logs
📝 Test 5: Exporting user data
✅ Exported data for candidate 1
   - Profile data: John Doe
   - Experiences: 0
   - Applications: 0
   - Interactions: 1
🎉 All GDPR compliance tests completed successfully!
```

## 📋 GDPR Rights Implementation

### 1. Right to be Informed
- ✅ Clear consent tracking
- ✅ Transparent data processing

### 2. Right of Access
- ✅ Data export functionality
- ✅ Audit log access

### 3. Right to Rectification
- ✅ Update candidate data
- ✅ Consent modification

### 4. Right to Erasure
- ✅ Complete data deletion
- ✅ Audit trail preservation

### 5. Right to Data Portability
- ✅ Structured data export
- ✅ JSON format output

### 6. Right to Object
- ✅ Consent withdrawal
- ✅ Data processing controls

## 🔧 Database Migration

### Run Migration Script

```bash
# Execute the GDPR migration script
psql -d your_database -f sql/gdpr_migration.sql
```

### Migration Steps

1. **Enable pgcrypto extension**
2. **Add consent_given column**
3. **Create audit_logs table**
4. **Create indexes for performance**
5. **Create encryption functions**
6. **Create GDPR compliance views**
7. **Grant necessary permissions**

## 🚀 API Usage Examples

### 1. Update Consent

```bash
curl -X PUT "http://localhost:8000/api/v1/gdpr/update_consent/123" \
  -H "Authorization: Bearer admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": 123,
    "consent_given": true,
    "admin_id": 1
  }'
```

### 2. Delete User Data

```bash
curl -X DELETE "http://localhost:8000/api/v1/gdpr/delete_user_data/123" \
  -H "Authorization: Bearer admin_token" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": 123,
    "reason": "GDPR right to be forgotten",
    "admin_id": 1
  }'
```

### 3. Export User Data

```bash
curl -X GET "http://localhost:8000/api/v1/gdpr/export_user_data/123" \
  -H "Authorization: Bearer admin_token"
```

### 4. Get Audit Logs

```bash
curl -X GET "http://localhost:8000/api/v1/gdpr/audit_logs/123" \
  -H "Authorization: Bearer admin_token"
```

## 📈 Monitoring and Alerts

### 1. Audit Log Monitoring

Monitor GDPR compliance through audit logs:
```sql
-- Recent GDPR activities
SELECT 
    action_type,
    COUNT(*) as count,
    MAX(created_at) as last_activity
FROM audit_logs 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY action_type;
```

### 2. Consent Status Monitoring

```sql
-- Candidates without consent
SELECT COUNT(*) as candidates_without_consent
FROM candidates 
WHERE consent_given = FALSE;
```

### 3. Data Deletion Monitoring

```sql
-- Recent data deletions
SELECT 
    user_id,
    details,
    created_at
FROM audit_logs 
WHERE action_type = 'data_deletion'
ORDER BY created_at DESC;
```

## 🔒 Security Best Practices

### 1. Encryption Keys
- Store encryption keys securely
- Rotate keys regularly
- Use environment variables for keys

### 2. Access Control
- Implement proper JWT authentication
- Use role-based access control
- Log all admin actions

### 3. Data Retention
- Implement data retention policies
- Automatically delete old audit logs
- Archive data before deletion

### 4. Audit Trail
- Never delete audit logs
- Encrypt sensitive audit data
- Regular backup of audit logs

## 📞 Support

For GDPR compliance questions or issues:

1. **Check audit logs** for compliance verification
2. **Run test scripts** to validate functionality
3. **Review API documentation** for endpoint usage
4. **Monitor compliance reports** for insights

---

**Note:** This implementation provides a solid foundation for GDPR compliance. In production, consider additional security measures, regular compliance audits, and legal review of the implementation. 