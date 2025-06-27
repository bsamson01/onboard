-- User Profile System Phase 1 - SQLite Database Migration
-- This script creates the necessary database changes for the user profile system

-- Add new columns to users table
ALTER TABLE users ADD COLUMN user_state VARCHAR(20) DEFAULT 'registered';
ALTER TABLE users ADD COLUMN onboarding_completed_at DATETIME;
ALTER TABLE users ADD COLUMN last_profile_update DATETIME;
ALTER TABLE users ADD COLUMN profile_expiry_date DATETIME;

-- Add index for user_state for efficient querying
CREATE INDEX IF NOT EXISTS idx_users_user_state ON users(user_state);

-- Add index for profile_expiry_date for efficient expiry checking
CREATE INDEX IF NOT EXISTS idx_users_profile_expiry_date ON users(profile_expiry_date);

-- Create user_role_history table
CREATE TABLE IF NOT EXISTS user_role_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    old_role VARCHAR(50),
    new_role VARCHAR(50) NOT NULL,
    changed_by_id VARCHAR(36),
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Add indexes for user_role_history
CREATE INDEX IF NOT EXISTS idx_user_role_history_user_id ON user_role_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_role_history_changed_at ON user_role_history(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_role_history_changed_by ON user_role_history(changed_by_id);

-- Update existing users to have proper user_state
-- For now, set all existing users to 'registered' state
UPDATE users 
SET user_state = 'registered'
WHERE user_state IS NULL;

-- Set last_profile_update for existing users
UPDATE users 
SET last_profile_update = created_at
WHERE last_profile_update IS NULL;

-- Verify the migration
SELECT 
    'Users with user_state' as check_type,
    COUNT(*) as count
FROM users 
WHERE user_state IS NOT NULL

UNION ALL

SELECT 
    'user_role_history table exists' as check_type,
    CASE WHEN EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_role_history') 
         THEN 1 ELSE 0 END as count;

-- Show statistics
SELECT 
    user_state,
    COUNT(*) as count
FROM users 
GROUP BY user_state
ORDER BY count DESC; 