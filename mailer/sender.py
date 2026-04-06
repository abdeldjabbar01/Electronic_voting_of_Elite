"""Email sending functionality."""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional


class EmailSender:
    """Handles email sending operations."""

    def __init__(
        self,
        smtp_server: str = None,
        smtp_port: int = None,
        sender_email: str = None,
        sender_password: str = None,
        sender_name: str = None
    ):
        self.smtp_server = smtp_server or os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.environ.get('SMTP_PORT', 587))
        self.sender_email = sender_email or os.environ.get('SENDER_EMAIL')
        self.sender_password = sender_password or os.environ.get('SENDER_PASSWORD')
        self.sender_name = sender_name or os.environ.get('SENDER_NAME', 'Elite_voting_systhem')

    def send_email(
        self,
        recipient: str,
        subject: str,
        body_text: str,
        body_html: str = None
    ) -> bool:
        """Send an email to a recipient.
        
        Args:
            recipient: The recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
        
        Returns:
            True if sent successfully
        """
        if not self.sender_email or not self.sender_password:
            print("Email credentials not configured")
            print(f"SMTP Server: {self.smtp_server}")
            print(f"SMTP Port: {self.smtp_port}")
            print(f"Sender Email: {self.sender_email}")
            print(f"Sender Password: {'Configured' if self.sender_password else 'Not configured'}")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        # Use professional sender name instead of raw email
        from_header = f'"{self.sender_name}" <{self.sender_email}>'
        msg['From'] = from_header
        msg['To'] = recipient

        # Attach plain text part
        msg.attach(MIMEText(body_text, 'plain'))

        # Attach HTML part if provided
        if body_html:
            msg.attach(MIMEText(body_html, 'html'))

        try:
            print(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            
            # Use SSL for port 465, TLS for port 587
            if self.smtp_port == 465:
                print("Using SSL connection...")
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    print("Logging into SMTP...")
                    server.login(self.sender_email, self.sender_password)
                    print(f"Sending email to: {recipient}")
                    server.sendmail(self.sender_email, recipient, msg.as_string())
                    print("Email sent successfully!")
            else:
                print("Starting TLS...")
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    print("Logging into SMTP...")
                    server.login(self.sender_email, self.sender_password)
                    print(f"Sending email to: {recipient}")
                    server.sendmail(self.sender_email, recipient, msg.as_string())
                    print("Email sent successfully!")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            print(f"Exception type: {type(e).__name__}")
            return False

    def load_template(self, template_name: str) -> str:
        """Load an email template from file.
        
        Args:
            template_name: Name of the template file
        
        Returns:
            Template content as string
        """
        template_path = Path(__file__).parent / 'templates' / template_name
        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        return ""


def send_voter_code_email(
    recipient_email: str,
    voter_code: str,
    vote_title: str
) -> bool:
    """Send voter code email to a registered voter.
    
    Args:
        recipient_email: Voter's email address
        voter_code: The unique voter code
        vote_title: Title of the vote
    
    Returns:
        True if sent successfully
    """
    sender = EmailSender()
    
    subject = f"Your Voting Code for: {vote_title}"
    
    # Load and format template
    template = sender.load_template('voter_code.txt')
    if template:
        body = template.format(
            voter_code=voter_code,
            vote_title=vote_title,
            recipient_email=recipient_email
        )
    else:
        body = f"""Hello,

Your voting code for "{vote_title}" is:

{voter_code}

Please keep this code secure. You will need it to cast your vote.

Best regards,
Electronic Voting System
"""

    return sender.send_email(recipient_email, subject, body)


def send_vote_confirmation_email(
    recipient_email: str,
    vote_title: str,
    submission_time: str
) -> bool:
    """Send vote confirmation email.
    
    Args:
        recipient_email: Voter's email address
        vote_title: Title of the vote
        submission_time: Time when vote was submitted
    
    Returns:
        True if sent successfully
    """
    sender = EmailSender()
    
    subject = f"Vote Confirmation: {vote_title}"
    
    # Load and format template
    template = sender.load_template('vote_confirmation.txt')
    if template:
        body = template.format(
            vote_title=vote_title,
            submission_time=submission_time,
            recipient_email=recipient_email
        )
    else:
        body = f"""Hello,

Thank you for participating in "{vote_title}".

Your vote has been successfully submitted at {submission_time}.

Your vote is secure and encrypted.

Best regards,
Electronic Voting System
"""

    return sender.send_email(recipient_email, subject, body)


def send_creator_code_email(
    recipient_email: str,
    creator_code: str,
    vote_title: str,
    private_key: str = None
) -> bool:
    """Send creator code email to vote creator.
    
    Args:
        recipient_email: Creator's email address
        creator_code: The unique creator code
        vote_title: Title of the vote
        private_key: Optional private key for vote decryption
    
    Returns:
        True if sent successfully
    """
    sender = EmailSender()
    
    subject = f"Your Vote Creator Code: {vote_title}"
    
    body = f"""Hello,

You have created a new vote: "{vote_title}"

Your creator code is: {creator_code}

Keep this code secure. You will need it to:
- End the vote early
- View the results after voting closes

"""
    
    if private_key:
        body += f"Your private key is: {private_key}\n\n"
    
    body += """Thank you for using the Electronic Voting System!
"""
    
    return sender.send_email(recipient_email, subject, body)


def send_voter_codes_email(
    recipient_email: str,
    n1_code: str,
    n2_code: str,
    vote_title: str,
    vote_id: int = None
) -> bool:
    """Send N1 and N2 codes to a voter with HTML email and vote link."""
    sender = EmailSender()
    
    subject = f"Your Voting Codes for: {vote_title}"
    
    # Build vote link using environment variable or fallback to localhost
    site_domain = os.environ.get('SITE_DOMAIN', 'http://localhost:5000')
    vote_link = f"{site_domain}/vote/{vote_id}" if vote_id else "#"
    
    # Plain text fallback
    text_body = f"""Your Voting Codes for: {vote_title}

Vote Link: {vote_link}

N1 Code (Voter ID): {n1_code}
N2 Code (Ballot ID): {n2_code}

Keep these codes secure and private!
"""
    
    # HTML email
    try:
        template_path = Path(__file__).parent / 'templates' / 'voter_codes.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            html_body = f.read()
        
        html_body = html_body.replace('{n1_code}', n1_code)
        html_body = html_body.replace('{n2_code}', n2_code)
        html_body = html_body.replace('{vote_title}', vote_title)
        html_body = html_body.replace('{vote_link}', vote_link)
        
    except Exception:
        html_body = None
    
    return sender.send_email(recipient_email, subject, text_body, html_body)


def send_vote_confirmation_email(
    recipient_email: str,
    vote_choice: str,
    vote_title: str
) -> bool:
    """Send vote confirmation email with HTML."""
    sender = EmailSender()
    
    subject = f"Vote Confirmation - {vote_title}"
    
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Plain text fallback
    text_body = f"""Vote Confirmation for: {vote_title}

Your Choice: {vote_choice}
Time: {timestamp}

Your vote has been recorded successfully.
Thank you for participating!
"""
    
    # HTML email
    try:
        template_path = Path(__file__).parent / 'templates' / 'vote_confirmation.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            html_body = f.read()
        
        html_body = html_body.replace('{vote_choice}', vote_choice)
        html_body = html_body.replace('{vote_title}', vote_title)
        html_body = html_body.replace('{timestamp}', timestamp)
        
    except Exception:
        html_body = None
    
    return sender.send_email(recipient_email, subject, text_body, html_body)


def send_contact_email(
    sender_name: str,
    sender_email: str,
    subject: str,
    message: str
) -> bool:
    """Send contact form submission to admin email.
    
    Args:
        sender_name: Name of the person submitting the form
        sender_email: Email of the person submitting the form
        subject: Subject line from the form
        message: Message content from the form
    
    Returns:
        True if sent successfully
    """
    sender = EmailSender()
    
    # Admin email to receive contact submissions
    admin_email = "aa.abba@ensta.edu.dz"
    
    email_subject = f"Contact Form: {subject}"
    
    # Plain text body
    body_text = f"""New Contact Form Submission

From: {sender_name} <{sender_email}>
Subject: {subject}

Message:
{message}

---
Sent via Electronic Voting System Contact Form
"""
    
    # HTML body
    body_html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #41431B; color: #F8F3E1; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #E3DBBB; }}
        .field {{ margin-bottom: 15px; }}
        .field-label {{ font-weight: bold; color: #41431B; }}
        .message-box {{ background: white; padding: 15px; border-left: 4px solid #AEB784; margin-top: 10px; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>New Contact Form Submission</h2>
        </div>
        <div class="content">
            <div class="field">
                <span class="field-label">From:</span> {sender_name} ({sender_email})
            </div>
            <div class="field">
                <span class="field-label">Subject:</span> {subject}
            </div>
            <div class="field">
                <span class="field-label">Message:</span>
                <div class="message-box">{message.replace(chr(10), '<br>')}</div>
            </div>
        </div>
        <div class="footer">
            Sent via Electronic Voting System Contact Form
        </div>
    </div>
</body>
</html>"""
    
    return sender.send_email(admin_email, email_subject, body_text, body_html)


def send_vote_results_email(
    voter_email: str,
    vote_title: str,
    vote_type: str,
    results: dict
) -> bool:
    """Send vote results email to voters with HTML formatting."""
    sender = EmailSender()
    
    subject = f"Vote Results - {vote_title}"
    
    total_votes = results.get('total_votes', 0)
    results_data = results.get('results', [])
    
    # Build results text
    if vote_type == 'rating':
        # Calculate average for rating
        total_sum = sum(float(r.get('option', 0)) * r.get('count', 0) for r in results_data)
        average = total_sum / total_votes if total_votes > 0 else 0
        results_text = f"Average Rating: {average:.2f}/10\n\n"
        for r in results_data:
            results_text += f"  {r.get('option')}: {r.get('count')} votes ({r.get('percentage', 0)}%)\n"
    else:
        # Choice vote results
        results_text = "Results:\n\n"
        for r in sorted(results_data, key=lambda x: x.get('count', 0), reverse=True):
            bar = "█" * int(r.get('percentage', 0) / 5)
            results_text += f"  {r.get('option')}: {r.get('count')} votes ({r.get('percentage', 0)}%) {bar}\n"
    
    text_body = f"""Vote Results: {vote_title}

Total Votes: {total_votes}

{results_text}

Thank you for participating in this vote!
"""
    
    # HTML email - simple and clean
    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.5; color: #333; background: #f5f5f5; }}
        .container {{ max-width: 500px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .header {{ background: #41431B; color: #F8F3E1; padding: 20px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 1.1rem; font-weight: 500; }}
        .header p {{ margin: 5px 0 0; font-size: 0.85rem; opacity: 0.9; }}
        .content {{ padding: 20px; }}
        .total-votes {{ text-align: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #E3DBBB; }}
        .total-votes .label {{ font-size: 0.75rem; color: #666; text-transform: uppercase; letter-spacing: 1px; }}
        .total-votes .count {{ font-size: 1.5rem; font-weight: 600; color: #41431B; margin-top: 3px; }}
        .rating-box {{ background: #41431B; color: #F8F3E1; border-radius: 6px; padding: 15px; text-align: center; margin-bottom: 20px; }}
        .rating-box .value {{ font-size: 2rem; font-weight: 600; }}
        .rating-box .label {{ font-size: 0.7rem; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }}
        .results-list {{ background: #F8F3E1; border-radius: 6px; padding: 15px; }}
        .result-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #E3DBBB; font-size: 0.85rem; }}
        .result-row:last-child {{ border-bottom: none; }}
        .result-name {{ font-weight: 500; color: #41431B; }}
        .result-stats {{ text-align: right; color: #555; }}
        .progress {{ width: 100%; height: 4px; background: #E3DBBB; border-radius: 2px; margin-top: 5px; }}
        .progress-fill {{ height: 100%; background: #41431B; border-radius: 2px; }}
        .footer {{ text-align: center; padding: 15px; font-size: 0.75rem; color: #888; background: #fafafa; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Vote Results</h1>
            <p>{vote_title}</p>
        </div>
        <div class="content">
            <div class="total-votes">
                <div class="label">Total Votes</div>
                <div class="count">{total_votes}</div>
            </div>
"""
    
    if vote_type == 'rating':
        total_sum = sum(float(r.get('option', 0)) * r.get('count', 0) for r in results_data)
        average = total_sum / total_votes if total_votes > 0 else 0
        html_body += f"""
            <div class="rating-box">
                <div class="value">{average:.2f}</div>
                <div class="label">Average Rating (out of 10)</div>
            </div>
"""
    
    html_body += """
        </div>
        <div class="footer">
            Thank you for voting<br>
            SecureVote System
        </div>
    </div>
</body>
</html>"""
    
    return sender.send_email(voter_email, subject, text_body, html_body)
