import os
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
import urllib.request
import base64
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
                
                client_id = os.environ.get('SPOTIFY_CLIENT_ID')
                client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
                
                if not client_id or not client_secret:
                    self.wfile.write(json.dumps({'error': 'Spotify Auth Error: Missing API keys in Vercel settings.'}).encode())
                    return

                # Authenticate with Spotify Developer API using Client Credentials Flow
                auth_string = f"{client_id}:{client_secret}"
                auth_base64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
                
                token_req = urllib.request.Request(
                    'https://accounts.spotify.com/api/token',
                    data=b'grant_type=client_credentials',
                    headers={
                        'Authorization': f'Basic {auth_base64}',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    method='POST'
                )
                
                token_resp = urllib.request.urlopen(token_req).read()
                access_token = json.loads(token_resp).get('access_token')

                if access_token:
                    # Fetch the playlist tracks with the official access token
                    api_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=100'
                    api_req = urllib.request.Request(
                        api_url,
                        headers={
                            'Authorization': f'Bearer {access_token}'
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
                    self.wfile.write(json.dumps({'error': 'Failed to retrieve Access Token from Spotify API.'}).encode())
                    return
                    
            except urllib.error.HTTPError as e:
                self.wfile.write(json.dumps({'error': f'Spotify API Error {e.code}: Double check your Client ID and Secret.'}).encode())
                return
            except Exception as e:
                self.wfile.write(json.dumps({'error': f'System Error: {str(e)}'}).encode())
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
