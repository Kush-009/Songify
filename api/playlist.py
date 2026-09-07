import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
import urllib.request
import re

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

        tracks = []

        if 'spotify.com' in url:
            try:
                # Bypass the blocked Spotify API by scraping their public Embed player
                match = re.search(r'playlist/([a-zA-Z0-9]+)', url)
                if not match:
                    self.wfile.write(json.dumps({'error': 'Invalid Spotify Playlist URL format.'}).encode())
                    return
                
                playlist_id = match.group(1)
                embed_url = f'https://open.spotify.com/embed/playlist/{playlist_id}'
                
                req = urllib.request.Request(
                    embed_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                html = urllib.request.urlopen(req).read().decode('utf-8')
                
                # Extract the track list JSON embedded inside the HTML
                json_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
                
                if json_match:
                    data = json.loads(json_match.group(1))
                    items = data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity', {}).get('trackList', [])
                    
                    for idx, item in enumerate(items):
                        title = item.get('title', 'Unknown Title')
                        artist = item.get('subtitle', 'Unknown Artist')
                        tracks.append({
                            'id': f"spot_{playlist_id}_{idx}",
                            'title': title,
                            'artist': artist
                        })
                
                # Backup regex fallback if the embed structure changes
                if not tracks:
                    titles = re.findall(r'"title":"([^"]+)"', html)
                    for idx, t in enumerate(titles): 
                        tracks.append({
                            'id': f"spot_{playlist_id}_{idx}",
                            'title': t,
                            'artist': 'Official Audio'
                        })

                if not tracks:
                    self.wfile.write(json.dumps({'error': 'Could not extract tracks. Make sure the playlist is public.'}).encode())
                    return
                    
                self.wfile.write(json.dumps({'tracks': tracks}).encode())
                return
                
            except Exception as e:
                self.wfile.write(json.dumps({'error': f'Embed scraping failed: {str(e)}'}).encode())
                return
