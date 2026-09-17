"""Small no-dependency server for the 1930 Public Domain search page."""

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json

PAGE_FILE = Path(__file__).with_name("index.html")
DATA_FILE = Path(__file__).parent.parent / "data" / "scraped_data_web_law_duke_edu_1.json"


def load_entries():
    with DATA_FILE.open(encoding="utf-8") as data_file:
        return [entry for entry in json.load(data_file) if entry.get("text")]


def make_results(entries):
    if not entries:
        return "<p>No matching entries.</p>"

    items = []
    for entry in entries:
        text = escape(entry["text"])
        link = entry.get("link")
        if link:
            items.append(f'<li><a href="{escape(link, quote=True)}">{text}</a></li>')
        else:
            items.append(f"<li>{text} (no source link available)</li>")
    return "<ul>" + "\n".join(items) + "</ul>"


class SearchHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path != "/":
            self.send_error(404, "Page not found")
            return

        query = parse_qs(parsed_url.query).get("q", [""])[0].strip()
        entries = load_entries()
        matches = [entry for entry in entries if query.casefold() in entry["text"].casefold()]

        page = PAGE_FILE.read_text(encoding="utf-8")
        page = page.replace("{{QUERY}}", escape(query, quote=True))
        page = page.replace("{{RESULTS}}", make_results(matches))
        if query:
            status = f"{len(matches)} matching entr{'y' if len(matches) == 1 else 'ies'} for: {escape(query)}"
        else:
            status = f"Showing all {len(entries)} entries. Enter a search term to narrow the list."
        page = page.replace("{{STATUS}}", status)

        encoded_page = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_page)))
        self.end_headers()
        self.wfile.write(encoded_page)


if __name__ == "__main__":
    address = ("127.0.0.1", 8000)
    print("Open http://127.0.0.1:8000 in your browser. Press Ctrl+C to stop.")
    ThreadingHTTPServer(address, SearchHandler).serve_forever()
