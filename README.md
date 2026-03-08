    # Electronic Voting System with Blind Signatures

## Team Members & Responsibilities
- ouinten moahamed : crypto/ folder
- benabed farouk: utils/ and voting/ folders
- abderrahman belahraoui: entities/ folder
- ABBA ABDELDJABBAR: cli/ folder
- Hammou huache: email templates

## How to Run
1. Create virtual environment: `python -m venv venv`
2. Activate it: `venv\Scripts\activate` (Windows)
3. Install requirements: `pip install -r requirements.txt`
4. Run any script: `python cli/host.py` for example


project-crypto-voting_Elite/
│
├── .env
├── .gitignore
├── README.md
├── config.py
├── supabase_client.py
├── requirements.txt
│
├── crypto/           "ouinten moahamed"
│   ├── __init__.py
│   ├── rsa_utils.py
│   ├── blind_signature.py
│   └── hash_utils.py
│
├── utils/            "benabed farouk"
│   ├── __init__.py
│   ├── generator.py
│   └── helpers.py
│
├── voting/           "benabed farouk"
│   ├── __init__.py
│   └── codec.py
│
├── entities/         "abderrahman belahraoui"
│   ├── __init__.py
│   ├── commissioner.py
│   ├── administrator.py
│   ├── anonymizer.py
│   └── counter.py
│
├── cli/              "ABBA ABDELDJABBAR"
│   ├── __init__.py
│   ├── host.py
│   ├── vote.py
│   └── count.py
│
└── templates/        "Hammou huache"
    ├── email_template.html
    └── email_template.txt


