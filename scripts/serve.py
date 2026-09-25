# /// script
# dependencies = []
# ///
"""
Serve a built site as Cloudflare Pages does, with /path served from path.html.

    uv run scripts/serve.py _site/en [PORT]
"""

import functools
import http.server
import sys
from pathlib import Path


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        local = Path(self.directory) / path.strip("/")
        # A page with subpages is both path.html and a directory, and the page takes precedence.
        if path != "/" and local.with_name(local.name + ".html").is_file():
            self.path = path.rstrip("/") + ".html"
        return super().send_head()

    def log_message(self, *args):
        pass


def main():
    directory = sys.argv[1]
    port = int(sys.argv[2]) if sys.argv[2:] else 8000
    print(f"Serving {directory} at http://127.0.0.1:{port}/")
    handler = functools.partial(Handler, directory=directory)
    http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()


if __name__ == "__main__":
    main()
