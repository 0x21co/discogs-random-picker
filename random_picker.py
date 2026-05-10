import warnings
# Suppress urllib3 NotOpenSSLWarning (must be done before other imports)
warnings.filterwarnings("ignore", category=ImportWarning, module="urllib3")
try:
    import urllib3
    if hasattr(urllib3.exceptions, 'NotOpenSSLWarning'):
        warnings.filterwarnings("ignore", category=urllib3.exceptions.NotOpenSSLWarning)
except (ImportError, AttributeError):
    pass

import os
import sys
import argparse
import random
from app.services.discogs_api import DiscogsService

def main():
    parser = argparse.ArgumentParser(description="Discogs Library Search & Random Picker (CLI)")
    parser.add_argument("username", help="Discogs username")
    parser.add_argument("query", nargs="?", help="Search query (wildcard/substring)")
    parser.add_argument("--token", help="Discogs API token")
    parser.add_argument("--search", "-s", help="Search query (alternative to positional query)")
    parser.add_argument("--random", "-r", action="store_true", help="Pick a random album from the matches")
    parser.add_argument("--check-sold", action="store_true", help="Compare sold items (orders) with collection")
    parser.add_argument("--refresh", action="store_true", help="Force refresh of the collection cache")

    args = parser.parse_args()

    token = args.token or os.environ.get("DISCOGS_TOKEN")
    service = DiscogsService(args.username, token)
    
    try:
        print(f"Loading collection for {args.username}...")
        releases = service.fetch_collection(force_refresh=args.refresh)
    except Exception as e:
        print(f"Error fetching collection: {e}")
        sys.exit(1)

    if args.check_sold:
        try:
            print("Fetching sold items...")
            sold_items = service.fetch_sold_items()
            overlaps = service.get_sold_comparison(releases, sold_items)
            
            if not overlaps:
                print("\n✅ No sold items found in your collection.")
            else:
                print(f"\n⚠️ FOUND {len(overlaps)} RELEASES IN YOUR COLLECTION THAT YOU HAVE SOLD:")
                print("-" * 70)
                for item in overlaps:
                    status = "🔴 SHOULD BE REMOVED" if item["should_remove"] else "🟡 PARTIAL"
                    count_info = f"(Sold {item['sold_count']}, Collection has {item['collection_count']})"
                    print(f"📍 {item['artist']} - {item['title']}")
                    print(f"   Status:     {status} {count_info}")
                    print(f"   Release ID: {item['release_id']}")
                    if item['collection_count'] > 1:
                        print(f"   Instances:  {', '.join(map(str, item['instance_ids']))}")
                    print(f"   Last Sold:  Order {item['last_order_id']} on {item['last_sold_date']}")
                    print(f"   URL:        https://www.discogs.com/release/{item['release_id']}")
                    print("-" * 70)
        except Exception as e:
            print(f"Error checking sold items: {e}")
            sys.exit(1)
        return

    search_query = args.query or args.search
    filtered = service.search_library(releases, query=search_query)

    if not filtered:
        print("No albums found matching your criteria.")
        sys.exit(0)

    if args.random:
        print(f"Found {len(filtered)} matching albums. Picking one randomly...")
        selected = random.choice(filtered)
        info = selected["basic_information"]
        print("-" * 40)
        print("🎵 YOUR RANDOM ALBUM:")
        print(f"{info['artists'][0]['name']} - {info['title']} ({info.get('year', 'Unknown')}) [{info['labels'][0]['name']}]")
        print(f"   URL: https://www.discogs.com/release/{selected['id']}")
        print("-" * 40)
    else:
        print(f"\nFound {len(filtered)} matching albums:")
        print("-" * 40)
        for i, r in enumerate(filtered, 1):
            info = r["basic_information"]
            print(f"{i}. {info['artists'][0]['name']} - {info['title']} ({info.get('year', 'Unknown')}) [{info['labels'][0]['name']}]")
        print("-" * 40)
        print(f"Use '--random' or '-r' to pick one of these {len(filtered)} albums at random.")

if __name__ == "__main__":
    main()
