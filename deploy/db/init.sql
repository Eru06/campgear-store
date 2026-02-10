-- Principle of least privilege: create a limited app user.
-- The POSTGRES_USER (campgear) is the owner used by migrations.
-- In production, you'd create a separate read/write user with no DDL rights.
-- For this school project, we use a single user but document the intent.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
