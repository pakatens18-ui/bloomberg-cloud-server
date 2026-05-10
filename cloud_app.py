from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage for the approval state
# Note: Render Free instances wipe memory when they restart/sleep, 
# but our polling mechanism keeps it awake during the morning window!
state = {
    "is_approved": False
}

@app.route('/')
def home():
    return "Bloomberg Webhook Server is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    # LINE sends a POST request here
    body = request.get_json()
    if not body:
        return "OK", 200

    events = body.get('events', [])
    for event in events:
        if event.get('type') == 'postback':
            postback_data = event.get('postback', {}).get('data')
            if postback_data == 'action=approve_bloomberg':
                print("Received approval from LINE! Setting state to True.")
                state["is_approved"] = True
    
    return "OK", 200

@app.route('/status', methods=['GET'])
def get_status():
    # Local Mac polls this endpoint
    return jsonify({"approved": state["is_approved"]})

@app.route('/reset', methods=['POST'])
def reset_status():
    # Local Mac hits this after successfully triggering the Canva script
    print("Resetting approval state.")
    state["is_approved"] = False
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
