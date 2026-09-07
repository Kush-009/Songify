import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
import yt_dlp

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        url = query.get('url', [''])[0]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if not url:
            self.wfile.write(json.dumps({'error': 'Please provide a playlist URL.'}).encode())
            return

        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'skip_download': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                tracks = []
                
                if 'entries' in info:
                    for idx, entry in enumerate(info['entries']):
                        title = entry.get('title')
                        if not title:
                            title = entry.get('url', 'Unknown Track')
                        uploader = entry.get('uploader', entry.get('channel', 'Unknown Artist'))
                        tracks.append({
                            'id': entry.get('id', f'track_{idx}'),
                            'title': title,
                            'artist': uploader
                        })
                else:
                    tracks.append({
                        'id': info.get('id', 'track_single'),
                        'title': info.get('title', 'Unknown Track'),
                        'artist': info.get('uploader', 'Unknown Artist')
                    })
            
            self.wfile.write(json.dumps({'tracks': tracks}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({'error': str(e)}).encode())
