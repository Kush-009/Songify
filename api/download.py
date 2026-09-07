import urllib.parse
from http.server import BaseHTTPRequestHandler
import yt_dlp
import requests

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        search_query = query.get('query', [''])[0]

        if not search_query:
            self.send_response(400)
            self.end_headers()
            return

        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch1'
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
                
                if 'entries' in info and len(info['entries']) > 0:
                    stream_url = info['entries'][0].get('url')
                    
                    # Proxy stream bypasses CORS and IP blocks
                    req = requests.get(stream_url, stream=True)
                    
                    self.send_response(200)
                    self.send_header('Content-type', req.headers.get('content-type', 'audio/mp4'))
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    # Stream the audio file in chunks to respect serverless memory limits
                    for chunk in req.iter_content(chunk_size=8192):
                        if chunk:
                            self.wfile.write(chunk)
                else:
                    self.send_response(404)
                    self.end_headers()
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
