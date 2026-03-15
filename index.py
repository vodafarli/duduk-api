from flask import Flask, jsonify
from flask_cors import CORS
import urllib.request
import json
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

def get_matches_from_sporekrani():
    url = "https://sporekrani.com/"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        idx = html.find('"@type":"BroadcastEvent"')
        if idx == -1: return []
        script_start = html.rfind('<script type="application/ld+json"', 0, idx)
        script_end = html.find('</script>', idx)
        if script_start == -1 or script_end == -1: return []
        content_start = html.find('>', script_start) + 1
        script_content = html[content_start:script_end].strip()
        data = json.loads(script_content)
        items = data if isinstance(data, list) else data.get('@graph', [])
        if not isinstance(items, list): items = [items]
        results = []
        for item in items:
            if item.get('@type') == 'BroadcastEvent':
                b_chan = item.get('broadcastChannel', [])
                if isinstance(b_chan, dict): b_chan = [b_chan]
                channels = [c.get('name', 'Unknown') for c in b_chan if isinstance(c, dict)]
                event = item.get('broadcastOfEvent', {})
                name = event.get('name', 'Unknown Match')
                start_date = event.get('startDate', '')
                time_str = start_date
                if start_date:
                    try:
                        dt = datetime.fromisoformat(start_date)
                        time_str = dt.strftime("%H:%M")
                    except Exception: pass
                league = ""
                org = event.get('organizer', {})
                if isinstance(org, dict):
                    league = org.get('url', '').split('/')[-1].replace('%20', ' ')
                home_team = name
                away_team = ""
                if " - " in name:
                    parts = name.split(" - ", 1)
                    home_team = parts[0].strip()
                    away_team = parts[1].strip()
                results.append({
                    "id": str(uuid.uuid4()),
                    "match_name": name,
                    "home_team": home_team,
                    "away_team": away_team,
                    "league": league,
                    "time": time_str,
                    "channels": channels
                })
        results.sort(key=lambda x: x['time'])
        return results
    except Exception as e:
        return []

@app.route('/')
def home():
    return "DÜDÜK API Canlıda! /api/matches/today adresini kontrol edin."

@app.route('/api/matches/today', methods=['GET'])
def get_today_matches():
    matches = get_matches_from_sporekrani()
    return jsonify({"success": True, "count": len(matches), "data": matches})

if __name__ == '__main__':
    app.run(debug=True)
