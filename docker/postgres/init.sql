-- =============================================================
-- Patient Intake System — Postgres init script
-- Runs once on first container creation (mounted as initdb.d)
-- =============================================================

-- Required for GIN trigram index on patient name search (Section 4)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Required for gen_random_uuid() used in table PKs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
