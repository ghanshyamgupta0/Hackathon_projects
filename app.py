from flask import Flask, render_template, request, jsonify
import os
import requests
import json
import re
import random

# Serve static files from `assets/` and templates from `templates/`
app = Flask(__name__, static_folder='assets', template_folder='templates')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/service-info', methods=['POST'])
def service_info():
    data = request.get_json(silent=True) or {}
    service = (data.get('service') or '').strip()
    if not service:
        return jsonify({'error': 'Missing service parameter'}), 400

    prompt = (
        f"You are an expert government assistant. The user wants information about '{service}'.\n"
        "Return a JSON object with these fields:\n"
        "- title: short title string\n"
        "- documents: an array of short strings (required documents)\n"
        "- steps: an array of step strings in order\n"
        "- offices: an array of objects {name, address, url} with at least one office\n"
        "- processing_time: short string (e.g., '4-6 weeks' or 'Same day')\n"
        "- best_time: short advice when to visit (e.g., 'Weekdays morning')\n"
        "- references: array of {title, url} for official links\n"
        "- mandatory: boolean indicating if the service is mandatory or optional\n"
        "Please vary the order of documents, steps, and offices each time. "
        "Return ONLY a valid JSON object, no extra text or code fences."
    )

    api_key = os.getenv('GEMINI_API_KEY')  # Put your API key in an environment variable
    if not api_key:
        # Development fallback so frontend works without credentials
        example = {
            'title': service,
            'documents': ['Application Form', 'Proof of ID', 'Proof of Address', 'Passport-size photo'],
            'steps': ['Fill application', 'Attach documents', 'Submit to office', 'Pay fee', 'Collect document'],
            'offices': [
                {'name': 'Central Service Office', 'address': '12 Main St, Capital', 'url': 'https://example.gov/central'},
            ],
            'processing_time': '2–4 weeks',
            'best_time': 'Weekdays morning (9–11am)',
            'references': [{'title': 'Official Service Page', 'url': 'https://example.gov/service'}],
            'mandatory': True
        }
        return jsonify(example)

    # Gemini API call
    endpoint = f"https://generativeai.googleapis.com/v1beta2/models/text-bison-001:generate?key={api_key}"
    payload = {
        'prompt': {'text': prompt},
        'temperature': 0.7,           # Increased for variety
        'maxOutputTokens': 512,
        'candidateCount': 3           # Request multiple outputs
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=20)
        resp.raise_for_status()
        body = resp.json()

        # Pick a random candidate if available
        text = None
        if 'candidates' in body and isinstance(body['candidates'], list) and body['candidates']:
            candidate = random.choice(body['candidates'])
            text = candidate.get('output') or candidate.get('content')

        if not text and 'output' in body and isinstance(body['output'], list) and body['output']:
            parts = [p.get('content') or p.get('text') for p in body['output'] if isinstance(p, dict)]
            text = '\n'.join([p for p in parts if p])

        if not text:
            text = json.dumps(body)

        # Parse JSON from model output
        parsed = None
        try:
            parsed = json.loads(text)
        except Exception:
            m = re.search(r"(\{(?:.|\n)*\})", text)
            if m:
                try:
                    parsed = json.loads(m.group(1))
                except Exception:
                    parsed = None

        if not parsed:
            return jsonify({'error': 'Could not parse model response', 'raw': text}), 500

        return jsonify(parsed)

    except requests.RequestException as exc:
        return jsonify({'error': 'AI request failed', 'detail': str(exc)}), 502


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
