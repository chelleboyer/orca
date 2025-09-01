-- Initialize database for OOUX ORCA Project Builder
-- This script runs automatically when PostgreSQL container starts

-- Create test database if it doesn't exist
SELECT 'CREATE DATABASE ooux_orca_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ooux_orca_test')\gexec

-- Create additional extensions if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pgcrypto";
