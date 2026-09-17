"""
O-Negative Memory Database Schema

PostgreSQL tables for:
1. people: Donor/requester/patient records
2. donor_availability: Live operational state
3. donor_history: Historical memory (influences decisions)
4. bank_reliability: Blood bank reputation/reliability tracking
5. requests: Log of all blood requests and outcomes
"""

SCHEMA_SQL = """
-- People table (donors, requesters, patients)
CREATE TABLE IF NOT EXISTS people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    role TEXT CHECK (role IN ('requester', 'donor', 'patient')),
    blood_group TEXT,
    phone_hash TEXT UNIQUE,
    location TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Live operational state
CREATE TABLE IF NOT EXISTS donor_availability (
    person_id UUID PRIMARY KEY REFERENCES people(id) ON DELETE CASCADE,
    availability_status TEXT CHECK (availability_status IN ('available', 'recently_donated', 'unavailable')),
    approx_location TEXT,
    updated_at TIMESTAMP DEFAULT now()
);

-- Historical memory (influences future decisions)
CREATE TABLE IF NOT EXISTS donor_history (
    person_id UUID REFERENCES people(id) ON DELETE CASCADE,
    last_donation_date DATE,
    recent_medication_flag BOOLEAN DEFAULT false,
    recent_medication_note TEXT,
    response_count INT DEFAULT 0,
    response_success_count INT DEFAULT 0,
    avg_response_time_minutes INT,
    updated_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (person_id, updated_at)
);

-- Blood bank reliability tracking
CREATE TABLE IF NOT EXISTS bank_reliability (
    bank_id TEXT PRIMARY KEY,
    bank_name TEXT,
    location TEXT,
    times_contact_successful INT DEFAULT 0,
    times_contact_failed INT DEFAULT 0,
    last_verified TIMESTAMP,
    updated_at TIMESTAMP DEFAULT now()
);

-- All blood requests and outcomes
CREATE TABLE IF NOT EXISTS requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id UUID REFERENCES people(id),
    blood_group TEXT,
    location TEXT,
    raw_query TEXT,
    outcome TEXT CHECK (outcome IN ('fulfilled', 'partial', 'unfulfilled', 'processing')),
    reasoning_trail JSONB,
    created_at TIMESTAMP DEFAULT now(),
    completed_at TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_people_blood_group ON people(blood_group);
CREATE INDEX IF NOT EXISTS idx_people_role ON people(role);
CREATE INDEX IF NOT EXISTS idx_donor_availability_status ON donor_availability(availability_status);
CREATE INDEX IF NOT EXISTS idx_requests_blood_group ON requests(blood_group);
CREATE INDEX IF NOT EXISTS idx_requests_location ON requests(location);
CREATE INDEX IF NOT EXISTS idx_requests_outcome ON requests(outcome);
"""

def get_schema() -> str:
    """Return the full SQL schema."""
    return SCHEMA_SQL
