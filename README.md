# Discogs Random Album Picker

Tools to pick a random album from your Discogs collection.

## Python Script (Recommended)

The Python version (`random_picker.py`) supports advanced features like fuzzy matching and wildcard searches.

### Prerequisites

- **Python 3.x**
- **requests** library: `pip3 install requests`

### Usage

1. **Basic usage:**
   ```bash
   python3 random_picker.py <username>
   ```

2. **Filter by label (with fuzzy matching):**
   Handles typos automatically (e.g., "bluenote" -> "Blue Note").
   ```bash
   python3 random_picker.py <username> --label "Blue Note"
   ```

3. **Wildcard search:**
   Search for patterns in artist or title.
   ```bash
   python3 random_picker.py <username> --wildcard "*Jazz*"
   ```

4. **Combine filters:**
   ```bash
   python3 random_picker.py <username> --label "Columbia" --wildcard "*Miles*"
   ```

5. **Token and Refresh:**
   Use `--token` or the `DISCOGS_TOKEN` env var for private collections. Use `--refresh` to bypass the local cache and fetch latest collection data.

---

## Bash Script (Simple)

A simple Bash script for macOS for quick random picks.

### Prerequisites

- **curl**, **jq**, **jot** (Standard on macOS, or `brew install jq`)

### Usage

```bash
./random-album.sh <username> [token]
```

---

## How to get a Discogs Token

1. Log in to your Discogs account.
2. Go to **Settings > Developers**.
3. Click **Generate new token**.
4. Copy the token and use it with these scripts.
