"""Email module initialization."""
from .sender import send_voter_code_email, send_vote_confirmation_email, send_creator_code_email, send_vote_results_email, EmailSender

__all__ = ['send_voter_code_email', 'send_vote_confirmation_email', 'send_creator_code_email', 'send_vote_results_email', 'EmailSender']
