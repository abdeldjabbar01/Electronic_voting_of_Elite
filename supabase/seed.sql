-- Create votes table
CREATE TABLE IF NOT EXISTS votes (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create vote_options table
CREATE TABLE IF NOT EXISTS vote_options (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER REFERENCES votes(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create votes_cast table
CREATE TABLE IF NOT EXISTS votes_cast (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER REFERENCES votes(id) ON DELETE CASCADE,
    option_id INTEGER REFERENCES vote_options(id) ON DELETE CASCADE,
    voted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    voter_ip INET,
    UNIQUE(vote_id, voter_ip) -- Prevent duplicate votes from same IP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_votes_created_at ON votes(created_at);
CREATE INDEX IF NOT EXISTS idx_vote_options_vote_id ON vote_options(vote_id);
CREATE INDEX IF NOT EXISTS idx_votes_cast_vote_id ON votes_cast(vote_id);
CREATE INDEX IF NOT EXISTS idx_votes_cast_voter_ip ON votes_cast(voter_ip);

-- Enable Row Level Security (RLS)
ALTER TABLE votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE vote_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE votes_cast ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (read-only)
CREATE POLICY "Allow public read access to votes" ON votes
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access to vote_options" ON vote_options
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access to votes_cast" ON votes_cast
    FOR SELECT USING (true);

-- Create policies for authenticated users (insert votes_cast)
CREATE POLICY "Allow authenticated users to cast votes" ON votes_cast
    FOR INSERT WITH CHECK (true);

-- Create policies for service role (admin access)
CREATE POLICY "Allow service role all access to votes" ON votes
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role all access to vote_options" ON vote_options
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role all access to votes_cast" ON votes_cast
    FOR ALL USING (auth.role() = 'service_role');

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_votes_updated_at 
    BEFORE UPDATE ON votes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO votes (title, description, start_time, end_time) VALUES
('Sample Election 2024', 'Choose your preferred candidate for the upcoming election.', 
 NOW() - INTERVAL '1 day', NOW() + INTERVAL '2 days'),
('Best Programming Language', 'Vote for your favorite programming language.',
 NOW(), NOW() + INTERVAL '7 days');

-- Insert sample options for first vote
INSERT INTO vote_options (vote_id, option_text) VALUES
(1, 'Candidate A'),
(1, 'Candidate B'),
(1, 'Candidate C');

-- Insert sample options for second vote
INSERT INTO vote_options (vote_id, option_text) VALUES
(2, 'Python'),
(2, 'JavaScript'),
(2, 'Java'),
(2, 'C++'),
(2, 'Go');
