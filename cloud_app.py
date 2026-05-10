import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

# State machine
state = {
    "is_approved": False,
    "awaiting_feedback": False,
    "feedback_ready": False,
    "edit_feedback": ""
}

def send_line_reply(reply_token, message_text):
    """Send a reply message back to LINE."""
    if not LINE_TOKEN:
        return
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message_text}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

@app.route('/')
def home():
    return "Bloomberg Webhook Server is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    body = request.get_json()
    if not body:
        return "OK", 200

    events = body.get('events', [])
    for event in events:
        event_type = event.get('type')
        reply_token = event.get('replyToken')

        # Handle button postbacks
        if event_type == 'postback':
            postback_data = event.get('postback', {}).get('data')

            if postback_data == 'action=approve_bloomberg':
                print("Approval received!")
                state["is_approved"] = True
                state["awaiting_feedback"] = False
                send_line_reply(reply_token, "✅ Approved! Generating your Canva image now...")

            elif postback_data == 'action=edit_bloomberg':
                print("Edit requested!")
                state["awaiting_feedback"] = True
                send_line_reply(reply_token,
                    "✏️ โปรดพิมพ์ข้อเสนอแนะของคุณ:\n\nตัวอย่าง: 'เปลี่ยน headline ให้เน้นเรื่อง Fed' หรือ 'เพิ่มหุ้น NVDA ใน caption'")

        # Handle text messages (edit feedback from user)
        elif event_type == 'message':
            msg = event.get('message', {})
            if msg.get('type') == 'text' and state["awaiting_feedback"]:
                feedback_text = msg.get('text', '').strip()
                print(f"Edit feedback received: {feedback_text}")
                state["edit_feedback"] = feedback_text
                state["awaiting_feedback"] = False
                state["feedback_ready"] = True
                send_line_reply(reply_token,
                    "👍 ได้รับข้อเสนอแนะแล้ว! กำลังสร้างเนื้อหาใหม่...")

    return "OK", 200

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "approved": state["is_approved"],
        "feedback_ready": state["feedback_ready"],
        "edit_feedback": state["edit_feedback"],
        "awaiting_feedback": state["awaiting_feedback"]
    })

@app.route('/reset', methods=['POST'])
def reset_status():
    state["is_approved"] = False
    state["awaiting_feedback"] = False
    state["feedback_ready"] = False
    state["edit_feedback"] = ""
    print("State reset.")
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
