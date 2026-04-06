"""Flask-WTF forms for the voting system."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, SelectField, FieldList, PasswordField
from wtforms.validators import DataRequired, Length, Optional, Email


class CreateVoteForm(FlaskForm):
    """Form for creating a new vote."""
    title = StringField('Vote Title', validators=[
        DataRequired(),
        Length(min=3, max=200)
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=1000)
    ])
    vote_type = SelectField('Vote Type', choices=[
        ('choice', 'Choice Vote'),
        ('rating', 'Rating Vote (0-10)')
    ], default='choice', validators=[DataRequired()])
    options = FieldList(StringField('Option'), min_entries=2, max_entries=10)
    start_date = DateTimeField('Start Date', format='%Y-%m-%d %H:%M', validators=[Optional()])
    end_date = DateTimeField('End Date', format='%Y-%m-%d %H:%M', validators=[Optional()])


class VoteForm(FlaskForm):
    """Form for submitting a vote with N1/N2 codes."""
    n1_code = StringField('N1 Code (Voter ID)', validators=[
        DataRequired(),
        Length(min=12, max=12)
    ])
    n2_code = StringField('N2 Code (Ballot ID)', validators=[
        DataRequired(),
        Length(min=12, max=12)
    ])
    choice = SelectField('Your Choice', validators=[DataRequired()])


class ResultsForm(FlaskForm):
    """Form for viewing vote results - now public."""
    pass  # No fields required - results are public


class EndVoteForm(FlaskForm):
    """Form for ending a vote early."""
    passkey = PasswordField('Admin Passkey', validators=[
        DataRequired(),
        Length(min=8, max=50)
    ])


class ContactForm(FlaskForm):
    """Form for contacting the team."""
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    subject = StringField('Subject', validators=[
        DataRequired(),
        Length(min=3, max=200)
    ])
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(min=10, max=2000)
    ])
