import os
import sys
import json
import random
import argparse
import requests
import difflib
import warnings
from typing import List, Dict, Optional

# Suppress urllib3 NotOpenSSLWarning
warnings.filterwarnings("ignore", category=ImportWarning, module="urllib3")
# Also handle specific urllib3/requests warnings if the above is not enough
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)
except (ImportError, AttributeError):
    pass

CACHE_FILE = ".discogs_cache.json"
USER_AGENT = "DiscogsRandomPicker/2.0"

class DiscogsPicker:
    def __init__(self, username: str, token: Optional[str] = None):
        self.username = username
        self.token = token
        self.base_url = f"https://api.discogs.com/users/{username}/collection/folders/0/releases"
        self.headers = {"User-Agent": USER_AGENT}
        if token:
            self.headers["Authorization"] = f"Discogs token={token}"

    def fetch_collection(self, force_refresh: bool = False) -> List[Dict]:
        if not force_refresh and os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                return json.load(f)

        print(f"Fetching collection for {self.username}...")
        releases = []
        page = 1
        per_page = 100

        while True:
            params = {"page": page, "per_page": per_page}
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            releases.extend(data["releases"])
            
            pagination = data["pagination"]
            if page >= pagination["pages"]:
                break
            page += 1
            print(f"Fetched page {page-1}/{pagination['pages']}...")

        with open(CACHE_FILE, "w") as f:
            json.dump(releases, f)
        
        return releases

    def search_library(self, releases: List[Dict], wildcard_query: Optional[str] = None) -> List[Dict]:
        filtered = releases

        if wildcard_query:
            import fnmatch
            q = wildcard_query.lower()
            # If no wildcard characters, assume substring match
            if "*" not in q and "?" not in q:
                q = f"*{q}*"
            
            def item_matches(r):
                info = r["basic_information"]
                # Searchable fields: artist, title, labels, year, formats
                search_texts = [
                    info["title"].lower(),
                    *[a["name"].lower() for a in info["artists"]],
                    *[l["name"].lower() for l in info["labels"]],
                    str(info.get("year", "")),
                    *[f["name"].lower() for f in info.get("formats", [])]
                ]
                return any(fnmatch.fnmatch(text, q) for text in search_texts)
            
            filtered = [r for r in filtered if item_matches(r)]

        return filtered

    def display_release(self, release: Dict, index: Optional[int] = None):
        info = release["basic_information"]
        artist = info["artists"][0]["name"]
        title = info["title"]
        year = info.get("year", "Unknown")
        label = info["labels"][0]["name"]
        id = release["id"]

        prefix = f"{index}. " if index is not None else ""
        print(f"{prefix}{artist} - {title} ({year}) [{label}]")
        if index is None: # Only show full details for single random pick
            print(f"   URL: https://www.discogs.com/release/{id}")

def main():
    parser = argparse.ArgumentParser(description="Discogs Library Search & Random Picker")
    parser.add_argument("username", help="Discogs username")
    parser.add_argument("query", nargs="?", help="Search query (wildcard/substring)")
    parser.add_argument("--token", help="Discogs API token")
    parser.add_argument("--search", "-s", help="Search query (alternative to positional query)")
    parser.add_argument("--random", "-r", action="store_true", help="Pick a random album from the matches")
    parser.add_argument("--refresh", action="store_true", help="Force refresh of the collection cache")

    args = parser.parse_args()

    token = args.token or os.environ.get("DISCOGS_TOKEN")
    
    picker = DiscogsPicker(args.username, token)
    
    try:
        releases = picker.fetch_collection(force_refresh=args.refresh)
    except Exception as e:
        print(f"Error fetching collection: {e}")
        sys.exit(1)

    # Combine positional query and --search flag
    search_query = args.query or args.search

    filtered = picker.search_library(releases, wildcard_query=search_query)

    if not filtered:
        print("No albums found matching your criteria.")
        sys.exit(0)

    if args.random:
        print(f"Found {len(filtered)} matching albums. Picking one randomly...")
        selected = random.choice(filtered)
        print("-" * 40)
        print("🎵 YOUR RANDOM ALBUM:")
        picker.display_release(selected)
        print(f"   URL: https://www.discogs.com/release/{selected['id']}")
        print("-" * 40)
    else:
        print(f"\nFound {len(filtered)} matching albums:")
        print("-" * 40)
        for i, r in enumerate(filtered, 1):
            picker.display_release(r, index=i)
        print("-" * 40)
        print(f"Use '--random' or '-r' to pick one of these {len(filtered)} albums at random.")

if __name__ == "__main__":
    main()
