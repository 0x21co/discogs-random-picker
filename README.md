# Discogs Random Album Picker

A simple Bash script for macOS to pick a random album from your Discogs collection.

## Prerequisites

- **curl**: Used for API requests (installed by default on macOS).
- **jq**: Used for parsing JSON data.
  - Install via Homebrew: `brew install jq`
- **jot**: Used for random number generation (installed by default on macOS).

## Usage

1. **Basic usage (for public collections):**
   ```bash
   ./random-album.sh <your_discogs_username>
   ```

2. **With a Personal Access Token (recommended for private collections or higher rate limits):**
   You can pass the token as a second argument:
   ```bash
   ./random-album.sh <username> <token>
   ```
   Or set it as an environment variable:
   ```bash
   export DISCOGS_TOKEN="your_token_here"
   ./random-album.sh <username>
   ```

## How to get a Discogs Token

1. Log in to your Discogs account.
2. Go to **Settings > Developers**.
3. Click **Generate new token**.
4. Copy the token and use it with this script.

## Customization

The script is a single file (`random-album.sh`). You can move it to your `/usr/local/bin` or add an alias in your `.zshrc` or `.bash_profile` to run it from anywhere:

```bash
alias random-album='/path/to/random-album.sh <your_username>'
```
