import requests
from bs4 import BeautifulSoup
import urllib.parse # For quoting search query

USER_AGENT = 'InteractivePianoTeacherApp/0.1 (Python Requests)'

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
    # freemidi.org uses /search?query=<song_title>
    search_query_path = "/search" # Path for search functionality
    query_params = {'query': song_title}

    # Correctly join the base URL with the search path
    if search_engine_url.endswith('/'):
        search_engine_url = search_engine_url[:-1]

    search_url = f"{search_engine_url}{search_query_path}?{urllib.parse.urlencode(query_params)}"

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
