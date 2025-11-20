import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='templates', static_folder='assets')

OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY="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"   
# <-- put your key here


def call_openrouter(message, history=None):
    messages = []

    # Add previous chat history (if any)
    if history and isinstance(history, list):
        messages.extend(history)

    # Add the new user message
    messages.append({"role": "user", "content": message})

    payload = {
        "model": "deepseek/deepseek-r1",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 512
    }

    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(OPENROUTER_ENDPOINT, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        body = resp.json()
    except Exception as e:
        return {"error": f"API error: {str(e)}"}

    # Extract reply safely
    reply = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )

    return {"reply": reply or "No response received."}


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Missing message"}), 400

    result = call_openrouter(message, history)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
