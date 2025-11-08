#!/usr/bin/env python3
"""
Simple HTTP server for serving the wave forecast visualization

Usage:
    python simple_server.py [port]

Default port is 8000
"""

import sys
import http.server
import socketserver
import os

# Change to parent directory so we can serve all files
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

Handler = MyHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  GFS Wave Forecast Visualization Server                 ║
╚══════════════════════════════════════════════════════════╝

Server running at: http://localhost:{PORT}

Open your browser and navigate to:
  → http://localhost:{PORT}/index.html

Press Ctrl+C to stop the server
""")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)
