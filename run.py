"""Run the Electronic Voting System Flask application."""
from web import create_app

app = create_app()

if __name__ == '__main__':
    print("Starting Electronic Voting System...")
    print("Visit: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
