-- Standalone migration for super_admins table (separate layer)
CREATE TABLE IF NOT EXISTS super_admins (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email varchar(254) UNIQUE NOT NULL,
  password_hash varchar(255) NOT NULL,
  full_name varchar(255),
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Updated timestamp trigger (PostgreSQL) - create function unconditionally
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS super_admins_set_updated_at ON super_admins;
CREATE TRIGGER super_admins_set_updated_at
BEFORE UPDATE ON super_admins
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();


