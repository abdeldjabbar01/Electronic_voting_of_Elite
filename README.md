# Blind Signature Electronic Voting System

Hey! This is our cryptography course project - a secure electronic voting system that uses blind signatures to keep votes anonymous while still verifying voter authenticity. We built this as a team of four over the course of a semester, and honestly we're pretty proud of how it turned out.

## What This Project Does

The system implements a blind signature voting protocol that lets people vote without anyone (not even the system administrators) knowing who voted for what. At the same time, it guarantees that only authorized voters can vote, and each person can only vote once.

Here's the core idea: when you vote, your choice gets encrypted and "blinded" with a random factor before being signed by the server. The server signs it without knowing what's inside, then you unblind it. The result is a valid signature that proves you're an authorized voter, but the signature can't be linked back to your identity.

## Meet the Team

### ABBA ABDELDJABBAR - Project Manager & Integrator
Managed overall architecture, GitHub repository, and module integration. Built core business logic.

**Key contributions:** `core/voting_protocol.py`, `core/vote_processor.py`, `core/tally.py`, `core/creator.py`, `constants.py`

### OINTEN Mohamad Amine - Database Specialist  
Designed Supabase schema and wrote all CRUD operations. Ensured data integrity and query optimization.

**Key contributions:** `database/models.py`, `database/queries.py`, `database/client.py`

### BENABED Farouk - Cryptography Engineer
Implemented RSA blind signatures, key generation, Tiger Tree Hash, and secure code generation.

**Key contributions:** `crypto/blind_signature.py`, `crypto/rsa_utils.py`, `crypto/tth.py`, `crypto/code_generator.py`


### BELAHRAUI Abderrahman - Web Frontend Developer
Built the Flask web interface, templates, CSS/JS, and responsive design. Shares frontend and UI/UX responsibilities with Youcef.

**Key contributions:** `web/routes.py`, `web/forms.py`, `web/templates/`, `web/static/`

### YOUSFI Youcef - Web Frontend Developer
Worked on the Flask web interface, focusing on UI/UX improvements, interactive elements, and assisted with template and static asset development. Shares frontend responsibilities with Abderrahman.

**Key contributions:** `web/templates/`, `web/static/`, UI/UX improvements

### HOUACHE Hamo - Email & Communication Module
Integrated SMTP for voter codes and confirmations. Created email templates.

**Key contributions:** `mailer/sender.py`, `mailer/templates/`

## How It Works (The Technical Version)

Our voting protocol follows Chaum's blind signature scheme with some modifications for our use case. Here's the flow:

### 1. Vote Creation
- The vote creator sets up a new election with title, description, and options
- RSA key pairs are generated for the vote
- The system creates unique N1 and N2 codes for each voter
- Voter codes are sent via email

### 2. Voter Registration (The Commissioner Role)
- Voters receive two codes: N1 (identity) and N2 (ballot identifier)
- The Commissioner stores a hash of N2, not N2 itself
- This separation prevents linking identity to ballot later

### 3. Voting Process (The Anonymizer Role)
- Voter creates their ballot: `m = (vote_choice, N2, random_bits)`
- Voter blinds the message: `m' = m * k^e mod N` where k is a random blinding factor
- The Administrator signs the blinded message: `s' = (m')^d mod N`
- Voter unblinds: `s = s' * k^(-1) mod N`
- Result: a valid signature on the ballot that can't be traced to the voter

### 4. Vote Casting
- The signed ballot is submitted with the hash of N2
- The system verifies the signature using the admin's public key
- If valid, the vote is stored encrypted with the counter's public key

### 5. Tallying (The Counter Role)
- When voting ends, the Counter decrypts all votes using their private key
- Results are calculated and displayed
- The Counter never sees voter identities - only the anonymized N2 hashes

## Project Structure

```
electronic_voting_project/
│
├── core/                           # Business logic & voting roles
│   ├── administrator.py            # Admin: key mgmt, signature validation
│   ├── commissioner.py             # Commissioner: voter registration, N2 hashing
│   ├── anonymizer.py               # Anonymizer: blind signature orchestration
│   ├── counter.py                  # Counter: vote decryption and tallying
│   ├── creator.py                  # Creator: vote creation and setup
│   ├── tally.py                    # Result calculation logic
│   ├── vote_processor.py           # Ballot processing
│   └── voting_protocol.py          # Main orchestrator - ties everything together
│
├── crypto/                         # Cryptographic implementations
│   ├── blind_signature.py          # RSA blind signature (Chaum's protocol)
│   ├── rsa_utils.py                # RSA key generation, encrypt/decrypt
│   ├── tth.py                      # Tiger Tree Hash for ballot integrity
│   ├── code_generator.py           # Secure code generation (N1, N2 codes)
│   └── utils.py                    # Crypto helper functions
│
├── web/                            # Flask web application
│   ├── routes.py                   # URL routes and view functions
│   ├── forms.py                    # WTForms form definitions
│   ├── templates/                  # Jinja2 HTML templates
│   │   ├── base.html               # Base layout
│   │   ├── index.html              # Home page with vote listings
│   │   ├── create_vote.html        # Create new vote form
│   │   ├── vote.html               # Voting interface
│   │   ├── results.html            # Results display
│   │   └── ...
│   └── static/                     # CSS, JavaScript, images
│       ├── css/style.css
│       └── js/scripts.js
│
├── database/                       # Data layer
│   ├── client.py                   # Supabase connection
│   ├── models.py                   # Data classes (Vote, Voter, Ballot, etc.)
│   └── queries.py                  # All database operations
│
├── mailer/                         # Email notifications
│   ├── sender.py                   # Email sending logic
│   └── templates/                  # Email templates (HTML and text)
│       ├── voter_code.txt          # Voter code email
│       └── vote_confirmation.txt   # Confirmation email
│
│
├── supabase/                       # Database migrations and config
│
├── run.py                          # Application entry point
├── constants.py                    # Configuration constants
└── requirements.txt                # Python dependencies
```

## Security Features

- **Blind Signatures**: Ensures voter anonymity - the administrator signs ballots without seeing their content
- **Separation of Duties**: Five distinct roles (Administrator, Commissioner, Anonymizer, Counter, Creator) prevent any single entity from compromising the election
- **RSA Encryption**: 2048-bit keys for ballot encryption
- **N1/N2 Separation**: Identity codes and ballot codes are separate and unlinkable
- **Tiger Tree Hash**: Provides integrity verification for ballots
- **Secure Code Generation**: Cryptographically random 16-character codes

## Known Limitations

- The current implementation stores private keys in the database (encrypted, but still). For a production system, we'd use HSMs or threshold cryptography.
- Email delivery can be slow with Gmail's rate limits. For a real election, you'd want a proper email service.
- No voter authentication beyond the code emails. A real system would need additional factors.
- The UI is functional but basic - we focused on the crypto implementation.

## Technologies Used

- **Backend**: Python 3.8+, Flask 2.3
- **Database**: Supabase (PostgreSQL)
- **Cryptography**: RSA (2048-bit), Tiger Tree Hash, blind signatures
- **Frontend**: HTML5, CSS3, vanilla JavaScript
- **Forms**: Flask-WTF, WTForms
- **Email**: SMTP with Gmail

## Course Context

This project was developed for the Cryptology course at [Your University]. The goal was to implement a real cryptographic protocol and demonstrate understanding of both the theory and practical implementation challenges.

## Lessons Learned

- **Crypto is hard**: Even "simple" protocols like blind signatures have edge cases that took hours to debug
- **Separation of duties matters**: Designing the system so no single role can cheat was a great learning experience
- **Integration > Individual components**: Each piece worked in isolation, but getting them to work together was the real challenge
- **Security vs usability tradeoffs**: We had to simplify some aspects to make it actually usable

## Future Improvements

If we had more time, we'd add:
- Threshold cryptography for key management (no single point of failure)
- Better UI/UX (it's pretty barebones right now)
- Mobile app for voting
- Audit logs that don't compromise anonymity
- Formal security proof

## License

This is an educational project. Feel free to use it for learning, but please don't use it for actual elections without significant additional security review.

## Contact

If you have questions about the implementation, feel free to reach out to any of us. We're happy to explain the crypto details or help you understand the blind signature protocol better.

---

**Built with lots of coffee and late nights by ABBA ABDELDJABBAR, OINTEN Mohamad Amine, BENABED Farouk, BELAHRAUI Abderrahman, and HOUACHE Hamo.**
