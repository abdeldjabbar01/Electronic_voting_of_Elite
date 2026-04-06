-- Database schema for Blind Signature based Voting Protocol

-- Votes table (unchanged, good)
CREATE TABLE votes (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title TEXT NOT NULL,
    description TEXT,
    vote_type TEXT NOT NULL DEFAULT 'choice', -- 'choice' or 'rating'
    creator_code TEXT NOT NULL,               -- plaintext, fine for creator
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vote options (unchanged)
CREATE TABLE vote_options (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    vote_id BIGINT NOT NULL REFERENCES votes(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    option_order INTEGER NOT NULL
);

-- Voters: store only email, gender, and global identifiers (no plaintext N2!)
CREATE TABLE voters (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    email TEXT UNIQUE NOT NULL,
    gender TEXT,
    n1_code TEXT NOT NULL UNIQUE,        -- 12-char, plaintext (ok for Commissioner)
    n2_hash TEXT NOT NULL,               -- TTH of N2, never plaintext N2
    has_voted BOOLEAN DEFAULT false,     -- global flag (optional)
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- FIXED: removed n2_code column.

-- Per-vote voter registration (links voter to a specific vote)
CREATE TABLE vote_voters (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    vote_id BIGINT NOT NULL REFERENCES votes(id) ON DELETE CASCADE,
    voter_email TEXT NOT NULL REFERENCES voters(email),
    n2_hash TEXT NOT NULL,               -- FIXED: store per-vote N2 hash (if codes differ per vote)
    has_voted BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(vote_id, voter_email)
);
-- FIXED: added n2_hash, removed n1_code (n1 is global from voters table).

-- Separate key tables for Administrator and Counter (replaces server_keys)
CREATE TABLE admin_keys (
    id INT PRIMARY KEY DEFAULT 1,
    public_key_n TEXT NOT NULL,
    public_key_e INT NOT NULL,
    private_key_pem TEXT NOT NULL,       -- PEM format, includes d,p,q
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE counter_keys (
    id INT PRIMARY KEY DEFAULT 1,
    public_key_n TEXT NOT NULL,
    public_key_e INT NOT NULL,
    private_key_pem TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Encrypted ballots (Anonymizer)
CREATE TABLE encrypted_ballots (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    vote_id BIGINT NOT NULL REFERENCES votes(id) ON DELETE CASCADE,
    n1_code TEXT NOT NULL,                -- for double-voting check (Commissioner validates)
    encrypted_ballot TEXT NOT NULL,       -- encrypted with Counter's public key
    blind_signature TEXT,                 -- Administrator's blind signature (unblinded by voter)
    tth_root TEXT NOT NULL,               -- FIXED: TTH of (choice + N2 + random bits)
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    processed BOOLEAN DEFAULT false
);

-- Decrypted votes (Counter's audit log)
CREATE TABLE decrypted_votes (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    ballot_id BIGINT NOT NULL REFERENCES encrypted_ballots(id) ON DELETE CASCADE,
    n2_code TEXT NOT NULL,                -- plaintext N2 (published after counting)
    vote_choice TEXT NOT NULL,
    signature_valid BOOLEAN NOT NULL,
    n2_hash_valid BOOLEAN NOT NULL,
    processed_at TIMESTAMPTZ DEFAULT NOW()
);
