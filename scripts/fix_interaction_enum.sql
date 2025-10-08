-- Add 'edited' value to interactiontypeenum if it doesn't exist
ALTER TYPE interactiontypeenum ADD VALUE IF NOT EXISTS 'edited';

-- Verify the enum values
SELECT unnest(enum_range(NULL::interactiontypeenum)) AS enum_values;
