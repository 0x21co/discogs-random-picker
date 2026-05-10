#!/bin/bash

# Discogs Random Album Picker
# Usage: ./random-album.sh <username> [token]

set -e

USERNAME=$1
TOKEN=$2

# If token is not provided as argument, check environment variable
if [ -z "$TOKEN" ]; then
    TOKEN=$DISCOGS_TOKEN
fi

if [ -z "$USERNAME" ]; then
    echo "Usage: $0 <username> [token]"
    echo "Or set DISCOGS_TOKEN environment variable."
    exit 1
fi

USER_AGENT="DiscogsRandomPicker/1.0"
BASE_URL="https://api.discogs.com/users/$USERNAME/collection/folders/0/releases"

# Function to make API calls
fetch_discogs() {
    local url=$1
    if [ -n "$TOKEN" ]; then
        curl -s -H "User-Agent: $USER_AGENT" -H "Authorization: Discogs token=$TOKEN" "$url"
    else
        curl -s -H "User-Agent: $USER_AGENT" "$url"
    fi
}

echo "Searching collection for $USERNAME..."

# 1. Get total count
RESPONSE=$(fetch_discogs "$BASE_URL?per_page=1")
TOTAL=$(echo "$RESPONSE" | jq -r '.pagination.items')

if [ "$TOTAL" == "null" ] || [ "$TOTAL" -eq 0 ]; then
    echo "Error: No albums found or user not found."
    echo "Check the username and if the collection is public (if no token provided)."
    exit 1
fi

echo "Found $TOTAL albums. Picking one for you..."

# 2. Pick a random index
# jot is standard on macOS and better for large ranges than $RANDOM
RANDOM_INDEX=$(jot -r 1 1 "$TOTAL")

# 3. Fetch the random album
ALBUM_RESPONSE=$(fetch_discogs "$BASE_URL?per_page=1&page=$RANDOM_INDEX")

# 4. Extract and print details
ARTIST=$(echo "$ALBUM_RESPONSE" | jq -r '.releases[0].basic_information.artists[0].name')
TITLE=$(echo "$ALBUM_RESPONSE" | jq -r '.releases[0].basic_information.title')
YEAR=$(echo "$ALBUM_RESPONSE" | jq -r '.releases[0].basic_information.year')
LABEL=$(echo "$ALBUM_RESPONSE" | jq -r '.releases[0].basic_information.labels[0].name')
ID=$(echo "$ALBUM_RESPONSE" | jq -r '.releases[0].id')

echo "----------------------------------------"
echo "🎵 YOUR RANDOM ALBUM:"
echo "----------------------------------------"
echo "Artist: $ARTIST"
echo "Title:  $TITLE"
echo "Year:   $YEAR"
echo "Label:  $LABEL"
echo "URL:    https://www.discogs.com/release/$ID"
echo "----------------------------------------"
