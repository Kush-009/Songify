import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
import urllib.request
import re
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

        tracks = []

        if 'spotify.com' in url:
            try:
                match = re.search(r'playlist/([a-zA-Z0-9]+)', url)
                if not match:
                    self.wfile.write(json.dumps({'error': 'Invalid Spotify Playlist URL format.'}).encode())
                    return
                
                playlist_id = match.group(1)
                
                # Fetching access token dynamically from the Spotify homepage to guarantee access
                home_req = urllib.request.Request(
                    'https://open.spotify.com/', 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
                )
                home_html = urllib.request.urlopen(home_req).read().decode('utf-8')
                
                token_match = re.search(r'"accessToken":"(.*?)"', home_html)
                
                if not token_match:
                    # Backup token extraction technique
                    token_req = urllib.request.Request(
                        'https://open.spotify.com/get_access_token?reason=transport&productType=web_player', 
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    token_resp = urllib.request.urlopen(token_req).read()
                    access_token = json.loads(token_resp).get('accessToken')
                else:
                    access_token = token_match.group(1)

                if access_token:
                    api_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=100'
                    api_req = urllib.request.Request(
                        api_url,
                        headers={
                            'Authorization': f'Bearer {access_token}',
                            'User-Agent': 'Mozilla/5.0'
                        }
                    )
                    tracks_resp = urllib.request.urlopen(api_req).read()
                    items = json.loads(tracks_resp).get('items', [])
                    
                    for idx, item in enumerate(items):
                        track_info = item.get('track')
                        if track_info:
                            title = track_info.get('name', 'Unknown Title')
                            artist = track_info['artists'][0]['name'] if track_info.get('artists') else 'Unknown Artist'
                            tracks.append({
                                'id': f"spot_{playlist_id}_{idx}",
                                'title': title,
                                'artist': artist
                            })
                    
                    self.wfile.write(json.dumps({'tracks': tracks}).encode())
                    return
                else:
                    self.wfile.write(json.dumps({'error': 'Failed to authenticate with Spotify anonymously.'}).encode())
                    return
                    
            except Exception as e:
                self.wfile.write(json.dumps({'error': f'Spotify Error: {str(e)}'}).encode())
                return

        # Fallback to standard extraction for YouTube or SoundCloud
        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'skip_download': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    for idx, entry in enumerate(info['entries']):
                        title = entry.get('title', entry.get('url', 'Unknown Track'))
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
            self.wfile.write(json.dumps({'error': f'Extraction Error: {str(e)}'}).encode())
