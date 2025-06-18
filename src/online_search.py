import requests
from bs4 import BeautifulSoup
import urllib.parse # For quoting search query and urlencode

USER_AGENT = 'InteractivePianoTeacherApp/0.1 (Python Requests)'

def _construct_freemidi_search_url(song_title: str, base_url: str = "https://freemidi.org") -> str:
    """
    Constructs the search URL for freemidi.org (or a similar engine).
    Sanitizes the song title for URL query parameters.
    """
    if not base_url.endswith('/'):
        base_url += '/'
    # freemidi.org uses /search?query=<song_title>
    # Other sites might use /search/<song_title> or other patterns.
    # This helper is specific to query parameter based search.

    # Quote the song title to make it URL-safe, ensuring '/' is also encoded
    quoted_title = urllib.parse.quote(song_title, safe='')

    # Using urlencode for query parameters is generally safer if there are multiple params
    # For a single 'query' param, direct f-string is also common.
    # params = {'query': song_title} # urlencode handles quoting internally
    # return f"{base_url}search?{urllib.parse.urlencode(params)}"
    return f"{base_url}search?query={quoted_title}"


def find_midi_links(song_title: str, search_engine_url="https://freemidi.org") -> list[dict]:
    """
    Searches for MIDI files on a given search engine URL (defaults to freemidi.org)
    and attempts to find direct .mid file links.

    Args:
        song_title: The title of the song to search for.
        search_engine_url: The base URL of the MIDI search engine.

    Returns:
        A list of dictionaries, where each dictionary contains 'title' and 'url'
        of a found MIDI file. Returns an empty list if no results or an error occurs.
    """
    results = []
    if not song_title:
        print("Search query is empty.")
        return results

    # Step 1: Perform the search on the site
    search_url = _construct_freemidi_search_url(song_title, search_engine_url)

    print(f"Searching on: {search_url}")
    headers = {'User-Agent': USER_AGENT}

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
    except requests.exceptions.RequestException as e:
        print(f"Error during search request to {search_url}: {e}")
        return results

    # Step 2: Parse the search results page to find links to song detail pages
    soup = BeautifulSoup(response.content, 'html.parser')
    song_page_links = []

    # This part is specific to freemidi.org's structure (as of late 2023/early 2024)
    # It looks for <div class="song-listing"> then an <a> tag within it.
    for song_div in soup.find_all('div', class_='song-listing'):
        link_tag = song_div.find('a', href=True)
        if link_tag:
            title_text = link_tag.get_text(strip=True)
            relative_song_page_url = link_tag['href']
            if relative_song_page_url:
                # Ensure the URL is absolute
                full_song_page_url = urllib.parse.urljoin(search_engine_url, relative_song_page_url)
                song_page_links.append({'title': title_text, 'page_url': full_song_page_url})

    if not song_page_links:
        print("No song detail page links found in search results.")
        return results

    print(f"Found {len(song_page_links)} potential song pages. Fetching MIDI links...")

    # Step 3: Visit each song detail page to find the direct MIDI download link
    for song_info in song_page_links:
        print(f"  Visiting song page: {song_info['page_url']} for title: {song_info['title']}")
        try:
            page_response = requests.get(song_info['page_url'], headers=headers, timeout=10)
            page_response.raise_for_status()

            page_soup = BeautifulSoup(page_response.content, 'html.parser')

            # Look for a download link. This is also specific to freemidi.org.
            # Often, it's an <a> tag with href ending in .mid, or specific text/ID.
            # Example: <a id="downloadmidi" href="download-midi/?id=12345">Download MIDI</a>
            # The actual .mid link might be revealed after clicking this, or this link itself might redirect.
            # For freemidi.org, the download link is often of the form:
            # <a ... href="/download-midi/?file=Artist_-_Song.mid&id=12345">Download MIDI</a>
            # The actual file name is in the 'file' query param.

            download_link_tag = page_soup.find('a', id='downloadmidi') # Common ID on freemidi
            if not download_link_tag: # Fallback: look for links with .mid in href
                 download_link_tag = page_soup.find('a', href=lambda href: href and href.endswith('.mid'))

            if download_link_tag and download_link_tag.get('href'):
                midi_url_path = download_link_tag['href']
                # The URL might be relative, so join it with the base URL
                direct_midi_url = urllib.parse.urljoin(search_engine_url, midi_url_path)

                # Extract a display title, prefer the one from the search result link if it's good
                display_title = song_info['title']

                # Sometimes the link text itself is better or contains more info
                link_text = download_link_tag.get_text(strip=True)
                if "download" in link_text.lower(): # If it's a generic "Download MIDI"
                    # Use the title we got from the search results page
                    pass
                else: # If the link text is more descriptive, use that
                    display_title = link_text if link_text else display_title

                results.append({'title': display_title, 'url': direct_midi_url})
                print(f"    Found MIDI link: {display_title} -> {direct_midi_url}")
            else:
                print(f"    No direct MIDI download link found on page {song_info['page_url']}")

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching song page {song_info['page_url']}: {e}")
        except Exception as e:
            print(f"  An unexpected error occurred while processing {song_info['page_url']}: {e}")

    if not results:
        print(f"No direct MIDI file links found after checking {len(song_page_links)} song pages.")
    else:
        print(f"Found {len(results)} MIDI file(s) in total.")
    return results

if __name__ == '__main__':
    # Test the function
    # test_song = "Counting Stars"
    test_song = "Beethoven Fur Elise" # A common, popular piece
    # test_song = "Invalid Song Name XYZ123" # Test no results
    # test_song = "test" # Test for placeholder if implemented that way

    print(f"\n--- Testing find_midi_links for '{test_song}' ---")
    found_files = find_midi_links(test_song)

    if found_files:
        print(f"\n--- Found {len(found_files)} MIDI files for '{test_song}': ---")
        for i, item in enumerate(found_files):
            print(f"{i+1}. Title: {item['title']}")
            print(f"   URL: {item['url']}")
    else:
        print(f"\n--- No MIDI files found for '{test_song}'. ---")

    print("\n--- Testing with an empty query ---")
    empty_query_results = find_midi_links("")
    print(f"Results for empty query: {len(empty_query_results)}")

    # Example of how the placeholder could be used if the main function was a wrapper
    # print("\n--- Testing placeholder directly (example) ---")
    # from online_search import find_midi_links_placeholder # Assuming it's in the same file for testing
    # placeholder_results = find_midi_links_placeholder("test placeholder")
    # if placeholder_results:
    #     for item in placeholder_results:
    #         print(f"Placeholder: {item['title']} - {item['url']}")


# --- MIDI Download Function ---
import os # For path operations

def download_midi_file(url: str, temp_dir: str = "temp_midi") -> str | None:
    """
    Downloads a MIDI file from a given URL into a temporary directory.

    Args:
        url: The direct URL to the .mid file.
        temp_dir: The directory to save the downloaded file. Defaults to "temp_midi".

    Returns:
        The local filepath to the downloaded MIDI file on success, None on failure.
    """
    if not url:
        print("Download URL is empty.")
        return None

    os.makedirs(temp_dir, exist_ok=True)

    # Generate a filename
    try:
        # Try to get filename from URL path
        parsed_url = urllib.parse.urlparse(url)
        filename_from_path = os.path.basename(parsed_url.path)
        if filename_from_path and filename_from_path.lower().endswith((".mid", ".midi")):
            # Basic sanitization (very basic, a library might be better for robust sanitization)
            filename = "".join(c for c in filename_from_path if c.isalnum() or c in ['.', '_', '-']).strip()
            if not filename: # If sanitization results in empty string
                 filename = urllib.parse.quote_plus(url) + ".mid" # Fallback
        else: # If no .mid extension or empty path, create one from query or hash
            # Fallback to a more generic name if path doesn't yield a good filename
            # Using a part of the URL, quoted, can be an option. Or UUID.
            # For simplicity, let's use the last part of the URL if possible, or a UUID.
            if parsed_url.query: # e.g. download?file=Song.mid&id=123
                query_dict = urllib.parse.parse_qs(parsed_url.query)
                if 'file' in query_dict and query_dict['file'][0].lower().endswith((".mid",".midi")):
                    filename = "".join(c for c in query_dict['file'][0] if c.isalnum() or c in ['.', '_', '-']).strip()
                else: # Fallback to a unique name if 'file' param is not good
                    import uuid
                    filename = str(uuid.uuid4().hex) + ".mid"
            else:
                import uuid
                filename = str(uuid.uuid4().hex) + ".mid"

        if not filename.lower().endswith((".mid", ".midi")): # Ensure it has an extension
            filename += ".mid"

    except Exception as e:
        print(f"Error generating filename from URL '{url}': {e}")
        import uuid # Ensure uuid is imported for fallback
        filename = str(uuid.uuid4().hex) + ".mid"

    local_filepath = os.path.join(temp_dir, filename)
    print(f"Attempting to download MIDI from '{url}' to '{local_filepath}'")

    headers = {'User-Agent': USER_AGENT} # USER_AGENT should be defined at module level

    try:
        response = requests.get(url, stream=True, headers=headers, timeout=20) # Increased timeout
        response.raise_for_status()  # Check for HTTP errors

        with open(local_filepath, 'wb') as f:
            # It's common to iterate over response.iter_content for large files,
            # but MIDI files are usually small, so response.content is often fine.
            f.write(response.content)

        print(f"Successfully downloaded MIDI to '{local_filepath}' ({os.path.getsize(local_filepath)} bytes).")
        return local_filepath

    except requests.exceptions.Timeout:
        print(f"Error: Timeout while trying to download '{url}'.")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading MIDI from '{url}': {e}")
    except IOError as e:
        print(f"Error writing MIDI file to '{local_filepath}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")

    # Cleanup if download failed partway
    if os.path.exists(local_filepath):
        try:
            file_size = os.path.getsize(local_filepath)
            if file_size == 0: # Or some other check to see if it's an invalid/empty file
                os.remove(local_filepath)
                print(f"Cleaned up empty/failed download: {local_filepath}")
        except OSError:
            pass # Ignore errors during cleanup attempt

    return None


if __name__ == '__main__':
    # Test the find_midi_links function
    # test_song = "Counting Stars"
    test_song = "Beethoven Fur Elise"
    # test_song = "Invalid Song Name XYZ123"
    # test_song = "test"

    print(f"\n--- Testing find_midi_links for '{test_song}' ---")
    found_files = find_midi_links(test_song)

    if found_files:
        print(f"\n--- Found {len(found_files)} MIDI files for '{test_song}': ---")
        for i, item in enumerate(found_files):
            print(f"{i+1}. Title: {item['title']}")
            print(f"   URL: {item['url']}")

        # Test downloading the first result if any
        if found_files[0].get('url'):
            print(f"\n--- Testing download_midi_file for: {found_files[0]['title']} ---")
            downloaded_file_path = download_midi_file(found_files[0]['url'])
            if downloaded_file_path:
                print(f"Downloaded test file to: {downloaded_file_path}")
                # Here you could try to parse it with mido or music_logic.parse_midi_file
                # For example:
                # from music_logic import parse_midi_file as parse_local_midi
                # parsed_info = parse_local_midi(downloaded_file_path)
                # if parsed_info:
                #     print(f"Successfully parsed downloaded file: {len(parsed_info['notes'])} notes.")
                # else:
                #     print("Failed to parse the downloaded file.")
                # try:
                #     os.remove(downloaded_file_path) # Clean up test download
                #     print(f"Cleaned up: {downloaded_file_path}")
                # except OSError as e:
                #     print(f"Error cleaning up {downloaded_file_path}: {e}")

            else:
                print("Download test failed.")

    else:
        print(f"\n--- No MIDI files found for '{test_song}'. ---")

    print("\n--- Testing with an empty query ---")
    empty_query_results = find_midi_links("")
    print(f"Results for empty query: {len(empty_query_results)}")

    print("\n--- Testing download with invalid URL ---")
    invalid_url_path = download_midi_file("http://invalid.url/test.mid")
    print(f"Result for invalid URL download: {invalid_url_path}")
