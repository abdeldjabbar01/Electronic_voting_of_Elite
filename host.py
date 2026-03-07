import csv
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime, timedelta

import config
from supabase_client import get_supabase
from crypto.rsa_utils import generate_rsa_keys
from crypto.hash_utils import hash_value_sha256
from utils.generator import generate_voter_codes

supabase = get_supabase()

def load_template(template_name: str) -> str:
    template_path = os.path.join('templates', template_name)
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def render_template(template: str, **kwargs) -> str:
    for key, value in kwargs.items():
        template = template.replace(f'{{{key}}}', str(value))
    return template

def send_email(recipient: str, n1: str, n2: str, election_title: str, election_id: int):
    html_template = load_template('email_template.html')
    text_template = load_template('email_template.txt')
    
    context = {
        'election_title': election_title,
        'election_id': election_id,
        'n1_code': n1,
        'n2_code': n2
    }
    
    html_content = render_template(html_template, **context)
    text_content = render_template(text_template, **context)
    
    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr(("Crypted_voting_system", config.SENDER_EMAIL))
    msg['To'] = recipient
    msg['Subject'] = f" Invite to a vote: {election_title}"
    
    msg.attach(MIMEText(text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=30)
        server.starttls()
        server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f" Email sent to {recipient}")
        return True
    except Exception as e:
        print(f" Failed to send email to {recipient}: {e}")
        return False

def create_election_from_csv():
    print("=== Create New Election ===")
    title = input("Election title: ")
    desc = input("Description: ")
    days = int(input("Duration (days): "))
    ends_at = (datetime.now() + timedelta(days=days)).isoformat()

    # Generate RSA keys for admin and counter
    admin_pub, admin_priv = generate_rsa_keys()
    counter_pub, counter_priv = generate_rsa_keys()

    # Insert election into Supabase (convert numbers to strings)
    election_data = {
        'title': title,
        'description': desc,
        'ends_at': ends_at,
        'admin_pub_e': str(admin_pub[0]),
        'admin_pub_n': str(admin_pub[1]),
        'admin_priv_d': str(admin_priv[0]),
        'admin_priv_n': str(admin_priv[1]),
        'counter_pub_e': str(counter_pub[0]),
        'counter_pub_n': str(counter_pub[1]),
        'counter_priv_d': str(counter_priv[0]),
        'counter_priv_n': str(counter_priv[1])
    }
    result = supabase.table('elections').insert(election_data).execute()
    election_id = result.data[0]['id']
    print(f" Election created with ID: {election_id}")

    # Read voters from CSV
    with open('voters.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            email = row['email']
            n1, n2 = generate_voter_codes()
            n2_hash = hash_value_sha256(n2)

            voter_data = {
                'election_id': election_id,
                'n1': n1,
                'n2_hash': n2_hash,
                'email': email,
                'used': False
            }
            supabase.table('voters').insert(voter_data).execute()
            print(f" Voter added: {email} -> N1={n1}, N2={n2}")

            # Send email
            send_email(email, n1, n2, title, election_id)

    print(" All voters processed. They can now vote using vote.py")

if __name__ == "__main__":
    create_election_from_csv()