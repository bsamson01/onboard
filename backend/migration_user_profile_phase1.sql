-- User Profile System Phase 1 - Database Migration
-- This script creates the necessary database changes for the user profile system

-- Add new columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_state VARCHAR(20) DEFAULT 'registered';
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_profile_update TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_expiry_date TIMESTAMP WITH TIME ZONE;

-- Add constraint for user_state enum
ALTER TABLE users ADD CONSTRAINT check_user_state 
    CHECK (user_state IN ('registered', 'onboarded', 'outdated'));

-- Add index for user_state for efficient querying
CREATE INDEX IF NOT EXISTS idx_users_user_state ON users(user_state);

-- Add index for profile_expiry_date for efficient expiry checking
CREATE INDEX IF NOT EXISTS idx_users_profile_expiry_date ON users(profile_expiry_date);

-- Add new column to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS last_reminder_sent TIMESTAMP WITH TIME ZONE;

-- Create user_role_history table
CREATE TABLE IF NOT EXISTS user_role_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    old_role VARCHAR(50),
    new_role VARCHAR(50) NOT NULL,
    changed_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reason TEXT
);

-- Add indexes for user_role_history
CREATE INDEX IF NOT EXISTS idx_user_role_history_user_id ON user_role_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_role_history_changed_at ON user_role_history(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_role_history_changed_by ON user_role_history(changed_by_id);

-- Add comment to table
COMMENT ON TABLE user_role_history IS 'Tracks all user role changes with audit trail';

-- Update existing users to have proper user_state
-- Note: You may want to customize this logic based on your current data
UPDATE users 
SET user_state = CASE 
    WHEN id IN (
        SELECT DISTINCT u.id 
        FROM users u 
        INNER JOIN customers c ON u.id = c.user_id 
        INNER JOIN onboarding_applications oa ON c.id = oa.customer_id 
        WHERE oa.status = 'approved'
    ) THEN 'onboarded'
    ELSE 'registered'
END
WHERE user_state = 'registered';

-- Set onboarding_completed_at for users who have completed onboarding
UPDATE users 
SET onboarding_completed_at = (
    SELECT oa.completed_at 
    FROM customers c 
    INNER JOIN onboarding_applications oa ON c.id = oa.customer_id 
    WHERE c.user_id = users.id 
    AND oa.status = 'approved' 
    ORDER BY oa.completed_at DESC 
    LIMIT 1
)
WHERE user_state = 'onboarded' AND onboarding_completed_at IS NULL;

-- Set profile_expiry_date to 1 year from onboarding completion
UPDATE users 
SET profile_expiry_date = onboarding_completed_at + INTERVAL '1 year'
WHERE user_state = 'onboarded' 
AND onboarding_completed_at IS NOT NULL 
AND profile_expiry_date IS NULL;

-- Set last_profile_update for existing users
UPDATE users 
SET last_profile_update = COALESCE(onboarding_completed_at, created_at)
WHERE last_profile_update IS NULL;

-- Create function to automatically update profile timestamps
CREATE OR REPLACE FUNCTION update_profile_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_profile_update = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update last_profile_update
DROP TRIGGER IF EXISTS trigger_update_profile_timestamp ON users;
CREATE TRIGGER trigger_update_profile_timestamp
    BEFORE UPDATE ON users
    FOR EACH ROW
    WHEN (OLD.first_name IS DISTINCT FROM NEW.first_name OR 
          OLD.last_name IS DISTINCT FROM NEW.last_name OR 
          OLD.phone_number IS DISTINCT FROM NEW.phone_number)
    EXECUTE FUNCTION update_profile_timestamp();

-- Create trigger to automatically update last_profile_update on customer updates
DROP TRIGGER IF EXISTS trigger_update_customer_profile_timestamp ON customers;
CREATE TRIGGER trigger_update_customer_profile_timestamp
    AFTER UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_user_profile_timestamp_from_customer();

-- Function to update user timestamp when customer data changes
CREATE OR REPLACE FUNCTION update_user_profile_timestamp_from_customer()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users 
    SET last_profile_update = NOW() 
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions (adjust as needed for your user roles)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_role_history TO your_app_user;
-- GRANT USAGE ON SEQUENCE user_role_history_id_seq TO your_app_user;

-- Verify the migration
DO $$
DECLARE
    user_count INTEGER;
    role_history_count INTEGER;
BEGIN
    -- Check users table
    SELECT COUNT(*) INTO user_count FROM users WHERE user_state IS NOT NULL;
    RAISE NOTICE 'Users with user_state: %', user_count;
    
    -- Check role history table exists
    SELECT COUNT(*) INTO role_history_count FROM information_schema.tables 
    WHERE table_name = 'user_role_history';
    RAISE NOTICE 'user_role_history table exists: %', role_history_count > 0;
    
    RAISE NOTICE 'Migration completed successfully!';
END $$;

-- Show statistics
SELECT 
    user_state,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM users 
GROUP BY user_state
ORDER BY count DESC;