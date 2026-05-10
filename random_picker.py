import os
import sys
import json
import random
import argparse
import requests
import difflib
from typing import List, Dict, Optional

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

    def filter_releases(self, releases: List[Dict], label_query: Optional[str] = None, wildcard_query: Optional[str] = None) -> List[Dict]:
        filtered = releases

        if label_query:
            # Extract all unique labels
            all_labels = set()
            for r in releases:
                for label in r["basic_information"]["labels"]:
                    all_labels.add(label["name"])
            
            # Fuzzy match labels
            matches = difflib.get_close_matches(label_query, list(all_labels), n=5, cutoff=0.5)
            if not matches:
                print(f"No labels found matching '{label_query}'.")
                return []
            
            if matches[0].lower() != label_query.lower():
                print(f"Matching labels found: {', '.join(matches)}")
                print(f"Using: {matches[0]}")
            
            best_label = matches[0]
            filtered = [
                r for r in filtered 
                if any(label["name"] == best_label for label in r["basic_information"]["labels"])
            ]

        if wildcard_query:
            q = wildcard_query.lower().replace("*", ".*")
            import re
            pattern = re.compile(q)
            
            filtered = [
                r for r in filtered
                if pattern.search(r["basic_information"]["title"].lower()) or
                   any(pattern.search(artist["name"].lower()) for artist in r["basic_information"]["artists"])
            ]

        return filtered

    def display_release(self, release: Dict):
        info = release["basic_information"]
        artist = info["artists"][0]["name"]
        title = info["title"]
        year = info.get("year", "Unknown")
        label = info["labels"][0]["name"]
        id = release["id"]

        print("-" * 40)
        print("🎵 YOUR RANDOM ALBUM:")
        print("-" * 40)
        print(f"Artist: {artist}")
        print(f"Title:  {title}")
        print(f"Year:   {year}")
        print(f"Label:  {label}")
        print(f"URL:    https://www.discogs.com/release/{id}")
        print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Discogs Random Album Picker")
    parser.add_argument("username", help="Discogs username")
    parser.add_argument("--token", help="Discogs API token (optional, or use DISCOGS_TOKEN env var)")
    parser.add_argument("--label", help="Filter by label (fuzzy matching)")
    parser.add_argument("--wildcard", help="Wildcard search in artist or title")
    parser.add_argument("--refresh", action="store_true", help="Force refresh of the collection cache")

    args = parser.parse_args()

    token = args.token or os.environ.get("DISCOGS_TOKEN")
    
    picker = DiscogsPicker(args.username, token)
    
    try:
        releases = picker.fetch_collection(force_refresh=args.refresh)
    except Exception as e:
        print(f"Error fetching collection: {e}")
        sys.exit(1)

    filtered = picker.filter_releases(releases, label_query=args.label, wildcard_query=args.wildcard)

    if not filtered:
        print("No albums found matching your criteria.")
        sys.exit(0)

    print(f"Found {len(filtered)} matching albums.")
    selected = random.choice(filtered)
    picker.display_release(selected)

if __name__ == "__main__":
    main()
