import os
import json
import random
import requests
import fnmatch
from typing import List, Dict, Optional

CACHE_FILE = ".discogs_cache.json"
USER_AGENT = "DiscogsRandomPicker/2.0"

class DiscogsService:
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

        with open(CACHE_FILE, "w") as f:
            json.dump(releases, f)
        
        return releases

    def fetch_sold_items(self) -> List[Dict]:
        """Fetches all sold items from marketplace orders."""
        if not self.token:
            raise ValueError("Discogs API token is required for fetching sold items.")

        orders_url = "https://api.discogs.com/marketplace/orders"
        sold_items = []
        page = 1
        per_page = 50

        while True:
            params = {"page": page, "per_page": per_page, "status": "All"}
            response = requests.get(orders_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            for order in data["orders"]:
                for item in order["items"]:
                    sold_items.append({
                        "id": item["release"]["id"],
                        "title": item["release"]["description"],
                        "order_id": order["id"],
                        "status": order["status"],
                        "date": order["created"]
                    })
            
            pagination = data["pagination"]
            if page >= pagination["pages"]:
                break
            page += 1

        return sold_items

    def search_library(self, releases: List[Dict], query: Optional[str] = None) -> List[Dict]:
        if not query:
            return releases

        q = query.lower()
        # If no wildcard characters, assume substring match
        if "*" not in q and "?" not in q:
            q = f"*{q}*"
        
        def item_matches(r):
            info = r["basic_information"]
            search_texts = [
                info["title"].lower(),
                *[a["name"].lower() for a in info["artists"]],
                *[l["name"].lower() for l in info["labels"]],
                str(info.get("year", "")),
                *[f["name"].lower() for f in info.get("formats", [])]
            ]
            return any(fnmatch.fnmatch(text, q) for text in search_texts)
        
        return [r for r in [r for r in releases] if item_matches(r)]

    def get_sold_comparison(self, collection: List[Dict], sold_items: List[Dict]) -> List[Dict]:
        """Compares sold items with collection and returns structured overlap data."""
        from collections import defaultdict
        
        collection_groups = defaultdict(list)
        for r in collection:
            collection_groups[r["id"]].append(r)
            
        sold_groups = defaultdict(list)
        for sold in sold_items:
            sold_groups[sold["id"]].append(sold)
        
        overlaps = []
        for rid, col_instances in collection_groups.items():
            if rid in sold_groups:
                info = col_instances[0]["basic_information"]
                col_count = len(col_instances)
                sold_count = len(sold_groups[rid])
                
                # Sort sold history by date descending
                sold_history = sorted(sold_groups[rid], key=lambda x: x["date"], reverse=True)
                
                overlaps.append({
                    "release_id": rid,
                    "artist": info["artists"][0]["name"],
                    "title": info["title"],
                    "year": info.get("year", "Unknown"),
                    "label": info["labels"][0]["name"],
                    "collection_count": col_count,
                    "sold_count": sold_count,
                    "should_remove": sold_count >= col_count,
                    "instance_ids": [inst["instance_id"] for inst in col_instances],
                    "last_sold_date": sold_history[0]["date"][:10],
                    "last_order_id": sold_history[0]["order_id"]
                })

        # Sort by artist/title
        return sorted(overlaps, key=lambda x: (x["artist"], x["title"]))
