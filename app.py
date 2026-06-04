from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

ACCENT_COLORS = ['#10f090', '#107bf0', '#ff4060', '#ffb020', '#a040ff', '#00d4ff']

@app.template_filter('accent_color')
def accent_color(index):
    return ACCENT_COLORS[(index - 1) % len(ACCENT_COLORS)]

@app.template_filter('filterby')
def filterby(iterable, attr, value):
    return [item for item in iterable if item.get(attr) == value]

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'games.json')

def load_games():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Auto-populate categories from actual games data
    used_cats = {g['category'] for g in data['games']}
    data['categories'] = [c for c in data['categories'] if c['id'] in used_cats]
    
    return data

@app.route('/')
def index():
    data = load_games()
    return render_template('index.html', data=data)

@app.route('/api/games')
def api_games():
    data = load_games()
    return jsonify(data)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
