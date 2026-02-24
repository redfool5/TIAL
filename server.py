from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.google.com/',
}

@app.route('/')
def index():
    imdb = request.args.get('imdb', '')
    kp   = request.args.get('kp', '')

    if not imdb and not kp:
        return jsonify({'error': 'need imdb or kp param'})

    results = {}
    errors  = {}

    # ALLOHA
    try:
        param = f'kp={kp}' if kp else f'imdb={imdb}'
        r = requests.get(f'https://api.alloha.tv/?token=04941a9a3ca3ac16e2b4327347bbc1&{param}', headers=HEADERS, timeout=8)
        d = r.json()
        if d.get('data', {}).get('iframe'):
            results['alloha'] = d['data']['iframe']
        else:
            errors['alloha'] = f'no iframe: {str(d)[:200]}'
    except Exception as e:
        errors['alloha'] = str(e)

    # KODIK
    try:
        param = f'kinopoisk_id={kp}' if kp else f'imdb_id={imdb}'
        r = requests.get(f'https://kodikapi.com/search?token=447d179e875aba3a85d6461f7e0b68c7&{param}&limit=5&with_material_data=false', headers=HEADERS, timeout=8)
        d = r.json()
        voices = []
        seen = set()
        for item in d.get('results', []):
            t = item.get('translation', {})
            if not t or t['id'] in seen or t.get('type') == 'subtitles':
                continue
            seen.add(t['id'])
            link = item['link']
            if link.startswith('//'):
                link = 'https:' + link
            voices.append({'id': t['id'], 'title': t['title'], 'url': link})
        if voices:
            results['kodik'] = voices
        else:
            errors['kodik'] = f'no results: {str(d)[:200]}'
    except Exception as e:
        errors['kodik'] = str(e)

    # VIDEOCDN
    try:
        param = f'kinopoisk_id={kp}' if kp else f'imdb_id={imdb}'
        r = requests.get(f'https://videocdn.tv/api/short?api_token=C7ZxDHun4c6MDmNNyivDuLdVQPUkJH7i&{param}', headers=HEADERS, timeout=8)
        d = r.json()
        if d.get('data') and d['data'][0].get('iframe_src'):
            results['videocdn'] = d['data'][0]['iframe_src']
        else:
            errors['videocdn'] = f'no data: {str(d)[:200]}'
    except Exception as e:
        errors['videocdn'] = str(e)

    # COLLAPS
    try:
        param = f'kinopoisk_id={kp}' if kp else f'imdb_id={imdb}'
        r = requests.get(f'https://api.bhcesh.me/list?token=4c250f7ac0a8c8a658c789186b9a58a5&{param}', headers=HEADERS, timeout=8)
        d = r.json()
        if d.get('results') and d['results'][0].get('iframe_url'):
            results['collaps'] = d['results'][0]['iframe_url']
        else:
            errors['collaps'] = f'no data: {str(d)[:200]}'
    except Exception as e:
        errors['collaps'] = str(e)

    if imdb:
        results['embedmaster'] = f'https://embedmaster.link/movie/{imdb}'

    return jsonify({'results': results, 'errors': errors})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
