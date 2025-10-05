import requests
import xml.etree.ElementTree as ET
import subprocess
import html
import os
import time
import re
import sys
import datetime
import json

# Add /root/.local/bin and /usr/local/bin to the PATH
os.environ["PATH"] = "/root/.local/bin:/usr/local/bin:" + os.environ.get("PATH", "")

# Define the base path for music files and playlist configurations
BASE_PATH = os.getenv("LISTENBRAINZ_BASE_PATH", "/app/music/")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "86400"))

# Parse playlist configurations from environment variable
def get_playlist_configs():
    playlists_json = os.getenv("LISTENBRAINZ_PLAYLISTS", '[]')
    try:
        playlists = json.loads(playlists_json)
        if not playlists:
            # Fallback to old single playlist configuration
            url = os.getenv("LISTENBRAINZ_URL", "")
            filename = os.getenv("LISTENBRAINZ_M3U_FILENAME", "@Created for You.m3u8")
            if url:
                playlists = [{"url": url, "m3u_filename": filename}]
        return playlists
    except json.JSONDecodeError as e:
        log(f"Error parsing LISTENBRAINZ_PLAYLISTS JSON: {e}", "ERROR")
        return []

def log(message, level="INFO"):
    """
    Log messages based on the specified log level, with date and time.
    """
    levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    if levels.index(level) >= levels.index(LOG_LEVEL):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] [{level}] {message}", flush=True)

def retry_request(url, params=None, max_retries=3, delay=5):
    """
    Perform an HTTP request with retries in case of failure.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response
            else:
                log(f"[Retry {attempt + 1}/{max_retries}] HTTP {response.status_code} for URL: {url}", "WARNING")
        except requests.exceptions.RequestException as e:
            log(f"[Retry {attempt + 1}/{max_retries}] Request failed: {e}", "WARNING")

        if attempt < max_retries - 1:
            time.sleep(delay)

    raise Exception(f"Failed to connect to {url} after {max_retries} attempts.")

def get_updated_date_from_xml(url):
    """
    Retrieve the <updated> date from the ListenBrainz XML feed.
    """
    try:
        response = retry_request(url, max_retries=3, delay=5)
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        entry = root.find("atom:entry", ns)
        if entry is not None:
            updated = entry.find("atom:updated", ns)
            if updated is not None:
                log(f"Retrieved <updated> date: {updated.text.strip()}", "DEBUG")
                return updated.text.strip()

        log("<updated> date not found in the XML feed.", "ERROR")
        return None
    except Exception as e:
        log(f"Error retrieving <updated> date: {e}", "ERROR")
        return None

def get_stored_date_from_m3u(filename):
    """
    Retrieve the stored <updated> date from the .m3u8 file.
    """
    m3u_filepath = os.path.join(BASE_PATH, filename)
    if not os.path.exists(m3u_filepath):
        log(f"File {filename} does not exist. No stored date found.", "DEBUG")
        return None

    with open(m3u_filepath, "r", encoding="utf-8") as m3u_file:
        for line in m3u_file:
            if line.startswith("# Updated:"):
                stored_date = line.split(": ", 1)[1].strip()
                log(f"Stored date retrieved from file: {stored_date}", "DEBUG")
                return stored_date
    return None

def fetch_recommendations(url):
    """
    Fetch song recommendations from the ListenBrainz feed.
    """
    try:
        response = retry_request(url, max_retries=3, delay=5)
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall("atom:entry", ns)

        recommendations = []
        for entry in entries:
            content = entry.find("atom:content", ns)
            if content is not None and content.text:
                content_html = content.text
                songs = extract_songs(content_html)

                for song in songs:
                    deezer_url = search_deezer_url(song['artist_name'], song['song_title'])
                    if deezer_url:
                        song['song_url'] = deezer_url
                        recommendations.append(song)

        log(f"Fetched {len(recommendations)} recommendations.", "INFO")
        return recommendations
    except Exception as e:
        log(f"Error fetching recommendations: {e}", "ERROR")
        return []

def extract_songs(content_html):
    """
    Extract song information from the HTML content of the ListenBrainz feed.
    """
    song_pattern = re.compile(r'<a href="(.*?)">(.*?)</a>\s*by\s*<a href="(.*?)">(.*?)</a>', re.DOTALL)
    matches = song_pattern.findall(content_html)

    log(f"Extracted {len(matches)} songs from the feed.", "DEBUG")
    return [
        {
            'song_url': html.unescape(m[0]),
            'song_title': html.unescape(m[1]),
            'artist_url': html.unescape(m[2]),
            'artist_name': html.unescape(m[3])
        }
        for m in matches
    ]

def search_deezer_url(artist_name, song_title):
    """
    Search for a Deezer URL for the given artist and song title.
    """
    base_url = "https://api.deezer.com/search"
    query = f"{song_title} {artist_name}"

    try:
        response = retry_request(base_url, params={"q": query}, max_retries=3, delay=5)
        data = response.json()

        log(f"Deezer API response for '{query}': {str(data)[:100]}", "DEBUG")

        if "data" in data and data["data"]:
            link = data["data"][0]["link"]
            log(f"Found Deezer link: {link}", "INFO")
            return link
        else:
            log(f"No match found for: {artist_name} - {song_title}", "WARNING")

            if "," in artist_name:
                first_artist = artist_name.split(",")[0].strip()
                query = f"{song_title} {first_artist}"
                log(f"Retrying with: {first_artist} - {song_title}", "DEBUG")
                response = retry_request(base_url, params={"q": query}, max_retries=3, delay=5)
                data = response.json()

                if "data" in data and data["data"]:
                    link = data["data"][0]["link"]
                    log(f"Found Deezer link: {link}", "INFO")
                    return link
                else:
                    log(f"No match found for: {first_artist} - {song_title}", "WARNING")
    except Exception as e:
        log(f"Error searching Deezer: {e}", "ERROR")

    return None

def download_with_deemix_cli(recommendations, template, m3u_filename, dry_run=False):
    """
    Download songs using the Deemix CLI and append their paths to the .m3u8 file.
    Returns the number of successful downloads.
    """
    arl = os.getenv("DEEMIX_ARL")
    if not arl:
        raise ValueError("❌ DEEMIX_ARL environment variable is not set.")

    deemix_arl_path = "/app/config/.arl"
    os.makedirs(os.path.dirname(deemix_arl_path), exist_ok=True)
    with open(deemix_arl_path, "w") as arl_file:
        arl_file.write(arl)

    success_count = 0

    for rec in recommendations:
        song_url = rec['song_url']
        log(f"Downloading: {rec['song_title']} by {rec['artist_name']}", "INFO")
        try:
            result = subprocess.run(
                [
                    "deemix",
                    "--portable",
                    "-b", "128",
                    "-p", BASE_PATH,
                    song_url
                ],
                capture_output=True,
                text=True,
                check=True
            )
            log(f"Download result: {result.stdout}", "DEBUG")
            for line in result.stdout.splitlines():
                if "Completed download of" in line:
                    downloaded_file = line.split("Completed download of ")[1].strip()
                    log(f"Adding downloaded file to .m3u8: {downloaded_file}", "DEBUG")
                    append_to_m3u(downloaded_file, m3u_filename)
                    success_count += 1
        except subprocess.CalledProcessError as e:
            log(f"Error downloading {rec['song_title']}: {e}", "ERROR")
            log(e.stderr, "DEBUG")
    return success_count

def ensure_m3u_header(m3u_filename, updated_date=None):
    """
    Add or update the header of the .m3u8 file with the updated date.
    """
    m3u_filepath = os.path.join(BASE_PATH, m3u_filename)

    if os.path.exists(m3u_filepath):
        with open(m3u_filepath, "r", encoding="utf-8") as m3u_file:
            lines = m3u_file.readlines()
    else:
        lines = ["#EXTM3U\n"]

    updated_line = f"# Updated: {updated_date}\n"
    lines = [line for line in lines if not line.startswith("# Updated:")]
    lines.insert(1, updated_line)

    with open(m3u_filepath, "w", encoding="utf-8") as m3u_file:
        m3u_file.writelines(lines)

    log(f"Updated header with date: {updated_date}")

def append_to_m3u(filepath, m3u_filename="@Created for You.m3u8"):
    """
    Append a file path to the .m3u8 playlist file if it is not already present.
    """
    m3u_filepath = os.path.join(BASE_PATH, m3u_filename)

    # Read the existing content of the .m3u8 file
    if os.path.exists(m3u_filepath):
        with open(m3u_filepath, "r", encoding="utf-8") as m3u_file:
            existing_lines = m3u_file.readlines()
    else:
        existing_lines = []

    # Check if the file is already present
    filename = os.path.basename(filepath)
    if any(filename in line for line in existing_lines):
        log(f"⚠️ File already exists in the playlist: {filename}", "WARNING")
        return

    # Append the file to the .m3u
    with open(m3u_filepath, "a", encoding="utf-8") as m3u_file:
        m3u_file.write(f"{filename}\n")
    log(f"✅ File added to the playlist: {filename}", "INFO")

def clear_m3u_content(m3u_filename):
    """
    Remove all entries from the .m3u8 file except the header lines.
    """
    m3u_filepath = os.path.join(BASE_PATH, m3u_filename)
    if not os.path.exists(m3u_filepath):
        return
    with open(m3u_filepath, "r", encoding="utf-8") as m3u_file:
        lines = m3u_file.readlines()
    header_lines = [line for line in lines if line.startswith("#")]
    with open(m3u_filepath, "w", encoding="utf-8") as m3u_file:
        m3u_file.writelines(header_lines)

def process_playlist(playlist_config):
    """
    Process a single playlist configuration.
    """
    url = playlist_config.get("url", "")
    m3u_filename = playlist_config.get("m3u_filename", "@Created for You.m3u8")
    
    if not url:
        log(f"No URL provided for playlist {m3u_filename}", "ERROR")
        return False

    try:
        log(f"Processing playlist: {m3u_filename}", "INFO")
        
        updated_date = get_updated_date_from_xml(url)
        if not updated_date:
            log(f"Unable to retrieve <updated> date from the feed for {m3u_filename}", "ERROR")
            return False

        stored_date = get_stored_date_from_m3u(m3u_filename)

        if stored_date and stored_date.split("T")[0] == updated_date.split("T")[0]:
            log(f"Playlist {m3u_filename} is already up to date. No synchronization needed.", "INFO")
            return True

        recommendations = fetch_recommendations(url)
        if not recommendations:
            log(f"No recommendations found for {m3u_filename}", "WARNING")
            return False

        clear_m3u_content(m3u_filename)

        template = "%artist% - %title%"
        success_count = download_with_deemix_cli(recommendations, template, m3u_filename)
        ensure_m3u_header(m3u_filename, updated_date)
        
        if success_count > 0:
            log(f"Synchronization completed successfully for {m3u_filename}. {success_count} tracks downloaded.", "INFO")
            return True
        else:
            log(f"Synchronization completed for {m3u_filename}, but no tracks were downloaded successfully.", "WARNING")
            return False
            
    except Exception as e:
        log(f"An error occurred processing {m3u_filename}: {e}", "ERROR")
        return False

def main():
    """
    Main function to synchronize multiple playlists from ListenBrainz and download songs using Deemix.
    """
    playlist_configs = get_playlist_configs()
    if not playlist_configs:
        log("No playlist configurations found.", "ERROR")
        return

    log(f"Found {len(playlist_configs)} playlist configurations to process.", "INFO")
    
    success_count = 0
    for config in playlist_configs:
        if process_playlist(config):
            success_count += 1
    
    log(f"Processed {success_count}/{len(playlist_configs)} playlists successfully.", "INFO")

if __name__ == "__main__":
    while True:
        main()
        log(f"Waiting {SYNC_INTERVAL} seconds before next sync...", "INFO")
        time.sleep(SYNC_INTERVAL)