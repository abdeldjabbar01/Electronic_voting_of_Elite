"""Flask routes."""
from datetime import datetime, timezone
from flask import render_template, request, jsonify, redirect, url_for, flash, abort
from crypto.utils import hash_code

from mailer.sender import send_voter_codes_email, send_vote_confirmation_email, send_creator_code_email, EmailSender, send_contact_email
from database.queries import VoteQueries
from core.vote_processor import VoteProcessor
from core.creator import VoteCreator
from core.tally import VoteTally
from core.voting_protocol import VotingProtocol
from web.forms import CreateVoteForm, VoteForm, ResultsForm, EndVoteForm, ContactForm



def init_routes(app):
    queries = VoteQueries()
    vote_processor = VoteProcessor(queries)
    vote_creator = VoteCreator(queries)
    vote_tally = VoteTally(queries)
    voting_protocol = VotingProtocol(queries)

    @app.route('/')
    def index():
        votes = queries.get_all_votes()
        now = datetime.now(timezone.utc)
        
        vote_voters = {}
        for vote in votes:
            voter_emails = queries.get_voters_by_vote(vote.id)
            vote_voters[vote.id] = voter_emails
        
        return render_template('index.html', votes=votes, now=now, vote_voters=vote_voters)

    @app.route('/api/votes', methods=['GET'])
    def api_get_votes():
        votes = queries.get_all_active_votes()
        return jsonify([{
            'id': v.id,
            'title': v.title,
            'description': v.description,
            'start_date': v.start_date.isoformat() if v.start_date else None,
            'end_date': v.end_date.isoformat() if v.end_date else None,
            'is_active': v.is_active
        } for v in votes])

    @app.route('/api/votes/<int:vote_id>', methods=['GET'])
    def api_get_vote(vote_id):
        vote = queries.get_vote_by_id(vote_id)
        if not vote:
            return jsonify({'error': 'Vote not found'}), 404

        options = queries.get_vote_options(vote_id)
        return jsonify({
            'id': vote.id,
            'title': vote.title,
            'description': vote.description,
            'start_date': vote.start_date.isoformat() if vote.start_date else None,
            'end_date': vote.end_date.isoformat() if vote.end_date else None,
            'is_active': vote.is_active,
            'options': [{'id': o.id, 'text': o.option_text, 'order': o.option_order} for o in options]
        })

    @app.route('/api/votes/<int:vote_id>/options', methods=['GET'])
    def api_get_vote_options(vote_id):
        options = queries.get_vote_options(vote_id)
        return jsonify({
            'options': [{'id': o.id, 'option_text': o.option_text, 'option_order': o.option_order} for o in options]
        })

    @app.route('/api/votes', methods=['POST'])
    def api_create_vote():
        """API endpoint to create a new vote."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        vote_type = data.get('vote_type', 'choice')
        options = data.get('options', [])

        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        if vote_type == 'choice' and not options:
            return jsonify({'error': 'Options are required for choice votes'}), 400
        
        try:
            import csv
            import os
            voter_emails = []
            csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'data', 'voters.csv')
            
            print(f"Loading voters from: {csv_path}")
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    email = row.get('email', '').strip()
                    if email:
                        voter_emails.append(email)
                        print(f"Found voter: {email}")
            
            print(f"Total voters loaded: {len(voter_emails)}")
        except Exception as e:
            return jsonify({'error': f'Failed to load voters: {str(e)}'}), 500
        
        if not voter_emails:
            return jsonify({'error': 'No voters found in voters.csv'}), 400

        vote_data = {
            'title': title,
            'description': description,
            'vote_type': vote_type,
            'options': options,
            'creator_code': 'PUBLIC',
            'end_date': data.get('end_date')
        }

        if vote_data['end_date']:
            from datetime import datetime, timedelta
            end_date = datetime.fromisoformat(vote_data['end_date'])
            end_date = end_date - timedelta(hours=1)
            vote_data['end_date'] = end_date.isoformat()
            print(f"Adjusted end_date from {data.get('end_date')} to {vote_data['end_date']}")

        print(f"Creating vote with data: {vote_data}")
        vote, error = voting_protocol.create_vote_with_voters(vote_data, voter_emails)
        
        if not vote:
            print(f"Vote creation failed: {error}")
            return jsonify({'error': error}), 400
        
        print(f"Vote created successfully with ID: {vote.id}")
        return jsonify({
            'success': True,
            'vote_id': vote.id,
            'message': f'Vote created successfully! {len(voter_emails)} voters will receive N1/N2 codes via email.'
        }), 201

    @app.route('/api/votes/<int:vote_id>/submit', methods=['POST'])
    def api_submit_vote(vote_id):
        """API endpoint to submit a vote using N1/N2 codes."""
        data = request.get_json()
        
        print("=" * 60)
        print(f"SUBMIT VOTE API CALLED - Vote ID: {vote_id}")
        print(f"Raw request data: {data}")
        print(f"Request headers: {dict(request.headers)}")
        print("=" * 60)
        
        if not data:
            print("ERROR: No JSON data received!")
            return jsonify({'error': 'No data provided'}), 400

        n1_code = str(data.get('n1_code', '')).strip()
        n2_code = str(data.get('n2_code', '')).strip()
        vote_choice = str(data.get('vote_choice', '')).strip()
        
        print(f"Extracted values: n1_code='{n1_code}', n2_code='{n2_code}', vote_choice='{vote_choice}'")

        if not all([n1_code, n2_code, vote_choice]):
            print(f"VALIDATION FAILED: n1_code='{n1_code}', n2_code='{n2_code}', vote_choice='{vote_choice}'")
            return jsonify({'error': 'N1 code, N2 code, and vote choice are required'}), 400

        print(f"Calling voting_protocol.submit_vote with: n1={n1_code}, n2={n2_code}, vote_id={vote_id}, choice={vote_choice}")
        success, error = voting_protocol.submit_vote(n1_code, n2_code, vote_id, vote_choice)

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({
            'success': True,
            'message': 'Vote submitted successfully! A confirmation email has been sent.'
        })

    @app.route('/api/votes/<int:vote_id>/results', methods=['GET'])
    def api_get_results(vote_id):
        """API endpoint to get vote results."""
        success = voting_protocol.decrypt_and_process_ballots(vote_id)
        if not success:
            print(f"Warning: Failed to process ballots for vote {vote_id}")
        
        results = voting_protocol.get_vote_results(vote_id)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 400
            
        return jsonify(results)

    @app.route('/api/voter/status/<n1_code>', methods=['GET'])
    def api_voter_status(n1_code):
        """Check voter status."""
        status = voting_protocol.get_voter_status(n1_code)
        return jsonify(status)

    @app.route('/api/voters', methods=['GET'])
    def api_get_voters():
        """Get list of voters from CSV file."""
        try:
            voters = []
            import os
            csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'data', 'voters.csv')
            
            import csv
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    voters.append({
                        'email': row.get('email', ''),
                        'gender': row.get('gender', '')
                    })
            
            return jsonify({
                'success': True,
                'voters': voters
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to load voters: {str(e)}'
            }), 500

    @app.route('/api/auth/verify', methods=['POST'])
    def api_auth_verify():
        """API endpoint to verify if email exists in voters table."""
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        voter = queries.get_voter_by_email(email)
        
        if voter:
            return jsonify({'success': True, 'email': email})
        else:
            return jsonify({'success': False, 'error': 'Sorry you are not welcome here !'}), 404

    @app.route('/api/votes/<int:vote_id>/count-and-end', methods=['POST'])
    def api_count_and_end_vote(vote_id):
        """API endpoint to count votes, end vote, and send results to voters."""
        vote = queries.get_vote_by_id(vote_id)
        if not vote:
            return jsonify({'error': 'Vote not found'}), 404
        
        if not vote.is_active:
            print(f"Vote {vote_id} already ended, skipping email sending")
            results = voting_protocol.get_vote_results(vote_id)
            if 'error' in results:
                return jsonify({'error': results['error']}), 400
            results['emails_sent'] = 0
            results['already_ended'] = True
            return jsonify(results)
        
        success = queries.end_vote(vote_id)
        if not success:
            return jsonify({'error': 'Failed to end vote'}), 400
        
        decrypt_success = voting_protocol.decrypt_and_process_ballots(vote_id)
        if not decrypt_success:
            print(f"Warning: Failed to decrypt ballots for vote {vote_id}")
        
        results = voting_protocol.get_vote_results(vote_id)
        if 'error' in results:
            return jsonify({'error': results['error']}), 400
        
        emails_sent = 0
        emails_failed = 0
        try:
            from mailer.sender import send_vote_results_email
            voters = queries.get_voters_by_vote(vote_id)
            print(f"Sending results to {len(voters)} voters for vote {vote_id}...")
            
            for voter_email in voters:
                try:
                    success = send_vote_results_email(
                        voter_email=voter_email,
                        vote_title=results.get('vote_title', 'Vote'),
                        vote_type=results.get('vote_type', 'rating'),
                        results=results
                    )
                    if success:
                        emails_sent += 1
                        print(f"  Results email sent to {voter_email}")
                    else:
                        emails_failed += 1
                        print(f"  Failed to send to {voter_email}")
                except Exception as email_error:
                    emails_failed += 1
                    print(f"  Error sending to {voter_email}: {email_error}")
            
            print(f"Results emails: {emails_sent} sent, {emails_failed} failed")
            results['emails_sent'] = emails_sent
            results['emails_failed'] = emails_failed
        except Exception as e:
            print(f"Error in email sending process: {e}")
            results['emails_sent'] = 0
            results['emails_failed'] = 0
        
        return jsonify(results)

    @app.route('/api/votes/<int:vote_id>/status', methods=['GET'])
    def api_vote_status(vote_id):
        """API endpoint to get vote status."""
        status = vote_processor.get_vote_status(vote_id)
        return jsonify(status)

    @app.route('/vote/<int:vote_id>')
    def vote_page(vote_id):
        """Page for voting on a specific vote."""
        vote = queries.get_vote_by_id(vote_id)
        if not vote:
            abort(404)

        options = queries.get_vote_options(vote_id)
        return render_template('vote.html', vote=vote, options=options)

    @app.route('/create-vote')
    def create_vote_page():
        """Page for creating a new vote."""
        return render_template('create_vote.html')

    @app.route('/results/<int:vote_id>')
    def results_page(vote_id):
        """Page for viewing vote results."""
        vote = queries.get_vote_by_id(vote_id)
        if not vote:
            abort(404)
        return render_template('results.html', vote=vote)

    @app.route('/about')
    def about():
        """About page."""
        return render_template('about.html')

    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        """Contact page with form."""
        form = ContactForm()
        
        if form.validate_on_submit():
            success = send_contact_email(
                sender_name=form.name.data,
                sender_email=form.email.data,
                subject=form.subject.data,
                message=form.message.data
            )
            
            if success:
                flash('Thank you! Your message has been sent successfully.', 'success')
                return redirect(url_for('contact'))
            else:
                flash('Sorry, there was an error sending your message. Please try again later.', 'error')
        
        return render_template('contact.html', form=form)
