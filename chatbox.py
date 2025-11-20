import os
import requests
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='templates', static_folder='assets')

# Simple chat endpoint that forwards the user's message to OpenRouter
OPENROUTER_ENDPOINT = 'https://api.openrouter.ai/v1/chat/completions'


def call_openrouter(message, history=None):
    api_key = os.getenv('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')
    if not api_key:
        # Development fallback: return a safe demo reply
        return {
            'reply': "Demo reply: set OPENROUTER_API_KEY to call the real API.\nYou asked: " + message
        }

    payload = {
        'model': 'gpt-4o-mini',
        'messages': [],
        'temperature': 0.2,
        'max_tokens': 512
    }

    # Optionally include previous history for context (array of {role,content})
    if history and isinstance(history, list):
        payload['messages'].extend(history)

    payload['messages'].append({'role': 'user', 'content': message})

    headers = {
        'Authorization': 'Bearer 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',
        'Content-Type': 'application/json'
    }

    try:
        resp = requests.post(OPENROUTER_ENDPOINT, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        body = resp.json()
    except requests.RequestException as e:
        return {'error': 'API request failed', 'detail': str(e)}

    # Extract reply text from common shapes
    reply = None
    if isinstance(body, dict):
        # OpenRouter returns choices similar to OpenAI shape
        choices = body.get('choices') or []
        if choices and isinstance(choices, list):
            first = choices[0]
            # many providers put message object
            msg = first.get('message') or first.get('message', {})
            if isinstance(msg, dict):
                reply = msg.get('content') or msg.get('content', {}).get('text')
            # fallback to text or delta
            if not reply:
                reply = first.get('text') or first.get('content')

    if not reply:
        # Last resort: stringify the response
        reply = json.dumps(body)

    return {'reply': reply}


@app.route('/')
def index():
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    history = data.get('history')
    if not message:
        return jsonify({'error': 'Missing message'}), 400

    result = call_openrouter(message, history=history)
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
