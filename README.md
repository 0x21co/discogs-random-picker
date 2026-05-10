# Discogs Random Album Picker

Tools to pick a random album from your Discogs collection.

## Python Script (Recommended)

The Python version (`random_picker.py`) supports advanced features like fuzzy matching and wildcard searches.

### Prerequisites

- **Python 3.x**
- **requests** library: `pip3 install requests`

### Usage

1. **List entire collection:**
   ```bash
   python3 random_picker.py <username>
   ```

2. **Search and List matching albums (Default):**
   Simply provide a search term after the username.
   ```bash
   python3 random_picker.py <username> "Miles"
   ```

3. **Pick a random album from the matches:**
   Use the `--random` or `-r` flag.
   ```bash
   python3 random_picker.py <username> "Jazz" --random
   ```

4. **Advanced Search (with wildcards):**
   Search for patterns in artist, title, label, year, or format.
   ```bash
   python3 random_picker.py <username> --search "*199*" --random
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
