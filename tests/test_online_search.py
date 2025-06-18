import unittest
import sys
import os

# Adjusting import path for src.online_search
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the internal function we want to test
from src.online_search import _construct_freemidi_search_url

class TestConstructSearchUrl(unittest.TestCase):

    def test_basic_url_construction(self):
        """Test basic URL construction with a simple song title."""
        song_title = "test song"
        base_url = "https://example.com" # Using example.com for test, not hitting actual site
        expected_url = "https://example.com/search?query=test%20song"

        # The helper function adds a trailing slash if not present
        # So, if base_url is "https://example.com", it becomes "https://example.com/"
        # before appending "search?query=..."
        # Let's adjust expectation or ensure helper function's behavior is consistent.
        # Based on implementation: base_url += '/' if not base_url.endswith('/')
        # So "https://example.com" becomes "https://example.com/"

        url = _construct_freemidi_search_url(song_title, base_url)
        self.assertEqual(url, expected_url, "Basic URL construction mismatch.")

    def test_url_construction_with_special_chars(self):
        """Test URL construction with special characters in the song title."""
        song_title = "song&title/\\name" # Includes '&', '/', '\'
        base_url = "https://example.com"
        # Expected: '&' -> %26, '/' -> %2F, '\' -> %5C (though quote handles this as needed)
        expected_url = "https://example.com/search?query=song%26title%2F%5Cname"

        url = _construct_freemidi_search_url(song_title, base_url)
        self.assertEqual(url, expected_url, "URL construction with special characters mismatch.")

    def test_url_construction_default_base(self):
        """Test URL construction using the default base_url (freemidi.org)."""
        song_title = "another test"
        # Default base_url is "https://freemidi.org"
        # The helper will make it "https://freemidi.org/"
        expected_url = "https://freemidi.org/search?query=another%20test"

        url = _construct_freemidi_search_url(song_title) # No base_url provided, use default
        self.assertEqual(url, expected_url, "Default base URL construction mismatch.")

    def test_base_url_with_trailing_slash(self):
        """Test that if base_url already has a trailing slash, it's handled correctly."""
        song_title = "slash test"
        base_url = "https://testsite.com/" # Already has trailing slash
        expected_url = "https://testsite.com/search?query=slash%20test"

        url = _construct_freemidi_search_url(song_title, base_url)
        self.assertEqual(url, expected_url, "Base URL with trailing slash handling mismatch.")

    def test_empty_song_title(self):
        """Test URL construction with an empty song title."""
        song_title = ""
        base_url = "https://empty.org"
        expected_url = "https://empty.org/search?query=" # Empty query param

        url = _construct_freemidi_search_url(song_title, base_url)
        self.assertEqual(url, expected_url, "Empty song title construction mismatch.")


if __name__ == '__main__':
    unittest.main(verbosity=2)
