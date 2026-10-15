"""
Hotel Bhagshree — Application Entry Point
Run with: python run.py
"""

import os
from datetime import datetime
from app import create_app

app = create_app()


@app.context_processor
def inject_now():
    """Make `now` available in all templates for the copyright year."""
    return {'now': datetime.utcnow()}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting Hotel Bhagshree on http://127.0.0.1:{port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
    )

