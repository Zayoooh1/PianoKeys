# PianoKeys

## Features

*   **Interactive Piano Keyboard:** Play a 2-octave virtual piano using your mouse or computer keyboard.
*   **Visual Feedback:** Keys light up and sounds play when notes are activated.
*   **Piano Roll Display:** Watch notes scroll down in a "piano roll" fashion for loaded songs.
*   **Online Song Search:** Search for MIDI files online (currently uses freemidi.org).
*   **MIDI Playback:** Select songs from search results to download, parse, and play them on the piano roll.
*   **Built-in Song:** Starts with a default song ("Counting Stars" placeholder) loaded.
*   **Playback Controls:** Pause/resume song scrolling ('P' key) and reset the current song ('R' key).
*   **Animated Background:** Aesthetically pleasing dark theme with twinkling stars.

## Requirements

*   Python 3.7+
*   Pygame
*   Mido
*   Requests
*   BeautifulSoup4

(These can be installed using: `pip install pygame mido requests beautifulsoup4`)
(Or via `pip install -r requirements.txt` if `requirements.txt` is up-to-date)

## How to Run from Source

1.  **Clone the Repository:**
    (Instructions for cloning would typically be here, e.g., `git clone <URL>`)
    ```bash
    # Example:
    # git clone https://github.com/yourusername/InteractivePianoTeacher.git
    # cd InteractivePianoTeacher
    ```

2.  **Install Dependencies:**
    It's highly recommended to use a Python virtual environment.
    ```bash
    # Create a virtual environment (e.g., named 'venv')
    python -m venv venv

    # Activate the virtual environment
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate

    # Install dependencies from requirements.txt
    pip install -r requirements.txt
    ```
    (The `requirements.txt` file should list `pygame`, `mido`, `requests`, and `beautifulsoup4`).

3.  **Run the Application:**
    ```bash
    python src/main.py
    ```

## Manual Testing Checklist

- Application starts without errors.
- Stars animation is visible in the background.
- UI layout (Header, Main Section, Control Panel) is correctly displayed.
- Piano keyboard is visible and responds to mouse clicks (visual press + sound).
- Piano keyboard responds to computer keyboard presses (e.g., A, S, D, W, E, R keys - check mapping in `main.py`) with visual press and sound.
- Default song ('Counting Stars' placeholder or a simple scale) loads and notes scroll in the piano roll.
- Piano roll 'hit effects' are visible when notes are played on the keyboard at the hit line.
- 'P' key pauses/resumes song scrolling in piano roll (when text input/search results are not active).
- 'R' key resets the current song in piano roll to the beginning (when text input/search results are not active).
- Search input box in control panel allows text entry.
- Clicking 'Search' button or pressing Enter in search box initiates a search (console log for now, UI may freeze during search).
- Search results (if any from freemidi.org) are displayed in a scrollable list.
- Scrollable list can be scrolled with mouse wheel if many results.
- Clicking a song in the search results list:
    - Prints its details to console.
    - Attempts to download and parse the MIDI file.
    - Loads the new song into the piano roll, replacing the previous one.
    - Resets song time and playback state.
- Test with various search queries, including those likely to yield no results (e.g., "asdfghjkl").
- Test input focus:
    - When search input box is active, piano keys (computer keyboard) should not respond.
    - When search results list is active/visible, piano keys (computer keyboard and mouse) should not respond.
- Application closes cleanly when the window is closed or the Escape key is pressed (when not typing in input box).
- Placeholder sound files are created in `assets/sounds/` if actual files are missing, preventing crashes.
- Temporary MIDI files downloaded from online search are stored in `temp_midi/` and cleaned up after attempting to load.

## Packaging for Distribution

To create a standalone executable for this application (e.g., a `.exe` file on Windows), you can use PyInstaller.

1.  **Install PyInstaller:**
    If you don't have PyInstaller installed, open your terminal or command prompt and run:
    ```bash
    pip install pyinstaller
    ```

2.  **Bundle the Application:**
    Navigate to the root directory of this project in your terminal. Then, run the following command:
    ```bash
    pyinstaller --name InteractivePianoTeacher --windowed --add-data "assets:assets" src/main.py
    ```
    Let's break down this command:
    *   `pyinstaller`: Invokes the PyInstaller tool.
    *   `--name InteractivePianoTeacher`: Sets the name of your application. The output executable and folder in `dist` will use this name.
    *   `--windowed`: This is important for GUI applications. It ensures that no console window appears when your application is run. For debugging, you might omit this or use `--console`.
    *   `--add-data "assets:assets"`: This command tells PyInstaller to include the `assets` folder (and its contents) in the bundled application. The format is `SOURCE_PATH:DESTINATION_FOLDER_IN_BUNDLE`. Here, it copies the local `assets` folder into an `assets` folder within the bundle. This is crucial for sounds, MIDI files, and any images.
    *   `src/main.py`: This is the main script (entry point) of your application.

3.  **Run the Executable:**
    After PyInstaller finishes, you will find a `dist` folder in your project directory. Inside `dist`, there will be a folder named `InteractivePianoTeacher` (or whatever you set with `--name`). Your standalone executable will be inside this folder.

**Notes:**
*   It's recommended to run the PyInstaller command from a virtual environment where you have installed all the project dependencies (`pygame`, `mido`, `requests`, `beautifulsoup4`).
*   The first time you run PyInstaller, it might take a few minutes. Subsequent runs can be faster.
*   If you encounter issues with missing files or modules in the bundled application, you might need to create and edit a `.spec` file for more detailed configuration. You can generate one using `pyi-makespec src/main.py --name InteractivePianoTeacher` and then modify it before running `pyinstaller YourApp.spec`.