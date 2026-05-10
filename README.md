# Discogs Toolbox

A modern Python-based toolbox to manage your Discogs collection via CLI and Web interface.

## Features

- **Advanced Search:** Search by artist, title, label, year, or format with wildcard support.
- **Random Picker:** Pick a random album from your entire library or a filtered search result.
- **Marketplace Sync:** Identify items you've sold on the marketplace that are still in your digital collection.
- **Web GUI:** A responsive web interface for easy access on any device.
- **Auto-Deployment:** One-script setup for Debian servers.

---

## Quick Start (Debian Server)

If you are on a Debian system, you can set up the entire project (including the Web GUI) with one command:

```bash
chmod +x deploy.sh
sudo ./deploy.sh
```

---

## CLI Usage

The CLI tool `random_picker.py` is the core of the toolbox.

### Prerequisites
- Python 3.x
- `pip install -r requirements.txt`

### Examples
- **List matching albums:** `python3 random_picker.py "Miles Davis"` (uses default user from `.env`)
- **Pick a random album:** `python3 random_picker.py "Jazz" -r`
- **Check for sold items:** `python3 random_picker.py --check-sold`
- **Override user:** `python3 random_picker.py other_user "Search Term"`
- **Advanced search:** `python3 random_picker.py -s "*199*" -r`

---

## Web Interface

The project includes a Flask-based web interface. 
- **Setup:** See [README_WEB.md](README_WEB.md) for detailed Gunicorn/Nginx instructions.
- **Security:** Supports Basic Authentication and default user configuration via `.env`.

---

## Technical Details

For developers and AI agents, see [AI_README.md](AI_README.md) for a deep dive into the architecture and extension points.

## How to get a Discogs Token

1. Log in to your Discogs account.
2. Go to **Settings > Developers**.
3. Click **Generate new token**.
4. Copy the token and set it in your `.env` file or `DISCOGS_TOKEN` environment variable.
