from flask import Flask, request
from database import save_event, init_db
from decision import process_event
import os

app = Flask(__name__)

# Initialize the database
init_db()

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data:
        try:
            save_event(data)  # Save the received data to the database
            process_event(data)  # Process the data instantly
            return {'message': 'Event processed successfully'}, 200
        except Exception as e:
            print(f"Error processing event: {e}")
            return {'message': 'Failed to process event', 'error': str(e)}, 500
    return {'message': 'No data received'}, 400


def run_webhook():
    port = int(os.environ.get('WEBHOOK_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
