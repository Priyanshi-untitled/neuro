from flask import Flask, jsonify, request
from neuro_sync import Neurosync_main  # change this import based on your actual file name

app = Flask(__name__)
# --- Routes ---
@app.route('/')
def index():
    return Neurosync_main('render')

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/curate', methods=['POST'])
def api_curate():
    data = request.get_json(silent=True) or {}
    topic = (data.get('topic') or request.args.get('topic') or '').strip()
    if not topic:
        return jsonify({'error': 'Missing topic'}), 400
    return jsonify(Neurosync_main('curate', topic))

# --- Local Dev Server ---
if __name__ == '__main__':
    print('\n🌐 Starting NeuroSync web server on http://localhost:5000')
    app.run(debug=True, port=5000)
