-- Initialize the nextcloud_ingestor database
-- This file is automatically executed when the container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The activity_state table will be created by SQLAlchemy
-- This file is mainly for any custom setup or initial data

-- You can add initial data here if needed
-- For example:
-- INSERT INTO activity_state (last_activity_id, last_check_timestamp) 
-- VALUES (0, NOW()) ON CONFLICT DO NOTHING;