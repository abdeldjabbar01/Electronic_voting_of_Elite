# database.py
# Purpose: Handle all database operations
# Functionality:
#   - Connects to the SQLite database (voting.db)
#   - Initializes tables from schema.sql if needed
#   - Provides CRUD operations for voters, codes, votes, fingerprints
# What it does:
#   - Connects to DB and executes queries
#   - Inserts, updates, fetches records
# Returns:
#   - Query results (lists, dictionaries)
# Notes:
#   - Contributors implement functions like add_voter, validate_N1, store_vote, fetch_votes