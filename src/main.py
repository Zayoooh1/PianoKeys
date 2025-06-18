# src/main.py
import pygame
import random
import math
import mido
import os # For creating dummy sound files
from keyboard import Keyboard
from music_logic import parse_midi_file, Note
from piano_roll import PianoRoll, create_test_midi
from gui_elements import TextInputBox, Button
from online_search import find_midi_links # Added online search

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLACK = (5, 5, 20)  # Dark blueish-black for night sky
STAR_COLORS = [
    (200, 200, 200), (220, 220, 255), (255, 255, 220), # Various shades of white/light yellow/blue
    (180, 180, 210) # Fainter stars
]
NUM_STARS = 150
FPS = 60

# Layout Area Heights
HEADER_HEIGHT = 60
CONTROL_PANEL_HEIGHT = 100
MAIN_SECTION_Y_START = HEADER_HEIGHT
MAIN_SECTION_HEIGHT = SCREEN_HEIGHT - HEADER_HEIGHT - CONTROL_PANEL_HEIGHT
CONTROL_PANEL_Y_START = HEADER_HEIGHT + MAIN_SECTION_HEIGHT

# Layout Area Colors
HEADER_COLOR = (20, 20, 40)
MAIN_SECTION_COLOR = (10, 10, 30) # This will be mostly covered by keyboard/piano roll
CONTROL_PANEL_COLOR = (25, 25, 50)
BORDER_COLOR = (80, 80, 100)
BORDER_WIDTH = 1 # Thin border

# Text Colors
TITLE_TEXT_COLOR = (220, 220, 255) # Light, slightly bluish white

# Keyboard layout properties
KEYBOARD_HEIGHT_RATIO = 0.30
KEYBOARD_WIDTH_RATIO = 0.95 # Keep it slightly less than full screen width
KEYBOARD_Y_POSITION_RATIO = 0.75 # Place keyboard lower in Main Section

# Piano Roll layout properties
PIANO_ROLL_HEIGHT_RATIO = 0.60 # Adjusted to fill more space above keyboard
PIANO_ROLL_Y_OFFSET_FROM_HEADER = 5 # Small gap from header
PIANO_ROLL_WIDTH_RATIO = KEYBOARD_WIDTH_RATIO # Match keyboard width


# --- Sound Asset Creation ---
SOUND_ASSETS_PATH = "assets/sounds"
PLACEHOLDER_SOUND_FILE = os.path.join(SOUND_ASSETS_PATH, "placeholder_sound.wav")

def create_dummy_sound_files(midi_notes_for_keyboard: list[int]):
    """
    Creates empty .wav files for given MIDI notes if they don't exist.
    Also creates a placeholder sound. This is to prevent Pygame errors
    if actual sound files are missing during development.
    """
    os.makedirs(SOUND_ASSETS_PATH, exist_ok=True)

    if not os.path.exists(PLACEHOLDER_SOUND_FILE):
        try:
            placeholder_data = bytes([
                ord('R'), ord('I'), ord('F'), ord('F'), 0x24, 0x00, 0x00, 0x00, ord('W'), ord('A'), ord('V'), ord('E'),
                ord('f'), ord('m'), ord('t'), ord(' '), 0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00,
                0x2B, 0x11, 0x00, 0x00, # SampleRate 11025 Hz
                0x2B, 0x11, 0x00, 0x00, # ByteRate 11025 bytes/sec
                0x01, 0x00, 0x08, 0x00,
                ord('d'), ord('a'), ord('t'), ord('a'), 0x00, 0x00, 0x00, 0x00
            ])
            with open(PLACEHOLDER_SOUND_FILE, 'wb') as f:
                f.write(placeholder_data)
            print(f"Created placeholder sound: {PLACEHOLDER_SOUND_FILE}")
        except Exception as e:
            print(f"Error creating placeholder sound {PLACEHOLDER_SOUND_FILE}: {e}")

    for note in midi_notes_for_keyboard:
        sound_file_path = os.path.join(SOUND_ASSETS_PATH, f"{note}.wav")
        if not os.path.exists(sound_file_path):
            try:
                if os.path.exists(PLACEHOLDER_SOUND_FILE):
                    import shutil
                    shutil.copy(PLACEHOLDER_SOUND_FILE, sound_file_path)
                else:
                    open(sound_file_path, 'a').close()
            except Exception as e:
                print(f"Error creating dummy sound file {sound_file_path}: {e}")
    # print(f"Checked/created dummy sound files for {len(midi_notes_for_keyboard)} notes in {SOUND_ASSETS_PATH}.")


# --- Star Class ---
class Star:
    """Represents a single star in the background."""
    def __init__(self):
        """Initializes a star with random properties."""
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.radius = random.uniform(0.5, 2) # Can be float for smoother edges if antialiasing is used
        self.color = random.choice(STAR_COLORS)
        # For twinkling: alpha will oscillate
        self.base_alpha = random.randint(70, 180) # Base brightness (can be lower for more subtlety)
        self.alpha_variation = random.randint(50, 100) # How much it twinkles
        self.twinkle_speed = random.uniform(0.01, 0.05) # How fast it twinkles (radians per frame)
        self.current_alpha = float(self.base_alpha)
        self._twinkle_angle = random.uniform(0, 2 * math.pi) # Initial phase for sine wave

    def update(self):
        """Updates the star's twinkle animation."""
        self._twinkle_angle += self.twinkle_speed
        if self._twinkle_angle > 2 * math.pi: # Keep angle in [0, 2pi]
            self._twinkle_angle -= 2 * math.pi

        # Alpha oscillates using a sine wave
        self.current_alpha = self.base_alpha + self.alpha_variation * math.sin(self._twinkle_angle)
        # Clamp alpha to be within [0, 255]
        self.current_alpha = max(0, min(255, self.current_alpha))

    def draw(self, surface):
        """Draws the star on the given surface."""
        # Create a temporary surface for this star. This allows per-pixel alpha
        # and avoids issues if the main surface doesn't support it directly for drawing primitives.
        # The size of the surface should be 2*radius by 2*radius.
        star_surf = pygame.Surface((int(self.radius * 2) + 1, int(self.radius * 2) + 1), pygame.SRCALPHA)

        # The color needs to have an alpha component for transparency.
        # We take the star's base color and set its alpha to current_alpha.
        # Ensure color is (R, G, B), then add alpha.
        try:
            final_color = (self.color[0], self.color[1], self.color[2], int(self.current_alpha))
        except IndexError: # Should not happen if STAR_COLORS are defined as (R,G,B)
            final_color = (255, 255, 255, int(self.current_alpha))

        # Draw the circle onto the temporary surface.
        # The position for drawing is the center of this small surface.
        pygame.draw.circle(star_surf, final_color, (self.radius, self.radius), self.radius)

        # Blit the temporary star surface onto the main screen.
        # The position needs to be adjusted by self.radius to center the star.
        surface.blit(star_surf, (self.x - self.radius, self.y - self.radius))

# --- Main Application ---
def main():
    """Main function to run the Pygame application."""
    # Initialize Pygame mixer with recommended settings BEFORE pygame.init()
    try:
        pygame.mixer.pre_init(44100, -16, 2, 512)
        # print("Mixer pre-initialized successfully.")
    except pygame.error as e:
        print(f"Error during mixer pre-init: {e}. Sound might not work.")

    pygame.init() # Initialize all other Pygame modules

    # After pygame.init(), set number of channels if mixer initialized
    if pygame.mixer.get_init():
        pygame.mixer.set_num_channels(32) # More channels for polyphony
    else:
        print("Mixer failed to initialize. No sound will be played.")

    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Interactive Piano Teacher")
    clock = pygame.time.Clock()

    # Create stars
    stars = [Star() for _ in range(NUM_STARS)]

    # Fonts
    try:
        title_font = pygame.font.SysFont("Arial", 32)
        ui_font = pygame.font.SysFont("Arial", 22) # Font for GUI elements
        ui_font_small = pygame.font.SysFont("Arial", 18)
    except pygame.error:
        print("Arial font not found, using default Pygame font.")
        title_font = pygame.font.Font(None, 46)
        ui_font = pygame.font.Font(None, 30)
        ui_font_small = pygame.font.Font(None, 24)

    title_text_surface = title_font.render("Interactive Piano Teacher", True, TITLE_TEXT_COLOR)
    title_text_rect = title_text_surface.get_rect(center=(SCREEN_WIDTH // 2, HEADER_HEIGHT // 2))

    # Initialize Keyboard
    keyboard_render_height = int(MAIN_SECTION_HEIGHT * KEYBOARD_HEIGHT_RATIO)
    keyboard_render_width = int(SCREEN_WIDTH * KEYBOARD_WIDTH_RATIO)
    keyboard_x = (SCREEN_WIDTH - keyboard_render_width) // 2
    # Position keyboard: y is the top of the keyboard
    keyboard_y = MAIN_SECTION_Y_START + MAIN_SECTION_HEIGHT - keyboard_render_height - 10 # 10px padding from bottom

    piano_keyboard = Keyboard(
        x=keyboard_x,
        y=keyboard_y,
        width=keyboard_render_width,
        height=keyboard_render_height,
        start_midi_note=60, # C4
        num_octaves=2
    )
    keyboard_layout_info = piano_keyboard.get_key_layout_info()

    # Create dummy sound files for the notes on this keyboard
    if piano_keyboard.all_midi_notes: # Check if list is populated
         create_dummy_sound_files(piano_keyboard.all_midi_notes)
    else:
        print("Warning: piano_keyboard.all_midi_notes is empty. Cannot create dummy sound files.")

    # --- Computer Keyboard to MIDI Mapping ---
    COMPUTER_KEYS_FOR_NOTES = [
        pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_g, pygame.K_h, pygame.K_j, pygame.K_k, pygame.K_l, pygame.K_SEMICOLON,
        pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b, pygame.K_n, pygame.K_m, pygame.K_COMMA, pygame.K_PERIOD, pygame.K_SLASH, # Lower row
        pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_t, pygame.K_y, pygame.K_u, pygame.K_i, pygame.K_o, pygame.K_p, pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET, # Upper row
    ]
    KEY_TO_MIDI = {}
    key_idx = 0
    # Map white keys first
    for midi_note in piano_keyboard.white_key_midi_notes:
        if key_idx < len(COMPUTER_KEYS_FOR_NOTES):
            KEY_TO_MIDI[COMPUTER_KEYS_FOR_NOTES[key_idx]] = midi_note
            key_idx += 1
        else: break
    # Then map black keys to the next available computer keys
    # This simple sequential mapping for black keys might not be ideal for playability
    # A more ergonomic mapping would intersperse them (e.g. QWERTY for white, Numbers for black)
    # For now, this ensures all keys get a mapping if available.
    # The black keys are assigned from COMPUTER_KEYS_FOR_NOTES where white keys left off.
    # For a typical 2-octave (14 white, 10 black) keyboard, this needs ~24 computer keys.

    # Corrected logic for black keys:
    # Black keys are typically mapped to the row above the white keys (e.g. W, E, T, Y, U for C#, D#, F#, G#, A#)
    # This example just continues filling COMPUTER_KEYS_FOR_NOTES sequentially.
    # To make it more playable, one might have separate lists of computer keys for white and black notes.
    # For this iteration, we'll stick to simple sequential filling.

    # Actually, it's better to iterate through all notes on the keyboard in MIDI order
    # and assign them to computer keys. This makes the mapping more predictable.
    KEY_TO_MIDI.clear() # Reset for the new mapping strategy
    key_idx = 0
    # piano_keyboard.all_midi_notes should be sorted.
    sorted_keyboard_notes = sorted(list(set(piano_keyboard.white_key_midi_notes + piano_keyboard.black_key_midi_notes)))

    for midi_note in sorted_keyboard_notes: # Iterate through all unique notes on the keyboard, sorted
        if key_idx < len(COMPUTER_KEYS_FOR_NOTES):
            KEY_TO_MIDI[COMPUTER_KEYS_FOR_NOTES[key_idx]] = midi_note
            key_idx += 1
        else:
            # print(f"Ran out of computer keys to map. Mapped {key_idx} notes.")
            break
    print(f"KEY_TO_MIDI mapping created for {len(KEY_TO_MIDI)} keys from the piano keyboard.")


    # Create a dummy MIDI file for the piano roll and parse it
    dummy_midi_path = "assets/midi/dummy_pianoroll_test.mid"
    try:
        midi_ticks_per_beat, midi_tempo = create_test_midi(dummy_midi_path)
    except Exception as e:
        print(f"Could not create/load test MIDI '{dummy_midi_path}': {e}. Using defaults.")
        midi_ticks_per_beat, midi_tempo = 480, 500000

    parsed_notes = parse_midi_file(dummy_midi_path)
    if not parsed_notes:
        print(f"Warning: No notes parsed from '{dummy_midi_path}'. Piano roll will be empty.")

    # Initialize PianoRoll
    piano_roll_render_height = int(MAIN_SECTION_HEIGHT * PIANO_ROLL_HEIGHT_RATIO)
    piano_roll_width = int(SCREEN_WIDTH * PIANO_ROLL_WIDTH_RATIO)
    piano_roll_x = (SCREEN_WIDTH - piano_roll_width) // 2
    piano_roll_y = MAIN_SECTION_Y_START + PIANO_ROLL_Y_OFFSET_FROM_HEADER

    the_piano_roll = PianoRoll(
        x=piano_roll_x, y=piano_roll_y,
        width=piano_roll_width, height=piano_roll_render_height,
        keyboard_layout_info=keyboard_layout_info,
        notes=parsed_notes,
        ticks_per_beat=midi_ticks_per_beat,
        tempo=midi_tempo
    )

    # --- Control Panel GUI Elements ---
    control_panel_padding = 10
    # control_panel_gui_rect defines the usable area within the control panel for placing elements
    control_panel_gui_rect = pygame.Rect(
        control_panel_padding,
        CONTROL_PANEL_Y_START + control_panel_padding,
        SCREEN_WIDTH - (2 * control_panel_padding), # Width of the usable area
        CONTROL_PANEL_HEIGHT - (2 * control_panel_padding) # Height of the usable area
    )

    search_input_box_height = 35 # Or ui_font_small.get_height() + padding
    search_input_box_width = int(control_panel_gui_rect.width * 0.45) # Adjusted width
    search_input_box = TextInputBox(
        x=control_panel_gui_rect.x, # Position relative to control_panel_gui_rect's origin
        y=control_panel_gui_rect.y + (control_panel_gui_rect.height - search_input_box_height) // 2,
        w=search_input_box_width,
        h=search_input_box_height,
        font=ui_font_small,
        initial_text="Counting Stars",
        prompt_text="Search for MIDI online..."
    )

    def on_search_button_click():
        query = search_input_box.get_text()
        if not query:
            print("Search query is empty. Please enter a song title.")
            # Optionally, provide feedback in the UI, e.g., by temporarily changing input box border
            return

        print(f"Searching online for: '{query}'...")
        original_button_text = search_button.text
        search_button.set_text("Searching...")
        search_button.set_enabled(False)

        # This call will block the main thread (UI will freeze).
        # In a real app, this should be done in a separate thread.
        search_results = find_midi_links(query)

        search_button.set_text(original_button_text)
        search_button.set_enabled(True)

        if search_results:
            print(f"Found {len(search_results)} results for '{query}':")
            for i, result in enumerate(search_results):
                print(f"  {i+1}. {result['title']} - {result['url']}")
            # Future: Display these results in a list in the UI
            # For now, can update a status label or the input box itself as a simple feedback
            search_input_box.set_text(f"Found {len(search_results)} for: {query}")
        else:
            print(f"No MIDI files found for '{query}'.")
            search_input_box.set_text(f"No results for: {query}")


    search_button_width = 100
    search_button_height = search_input_box_height
    search_button = Button(
        x=search_input_box.rect.right + control_panel_padding,
        y=search_input_box.rect.y,
        w=search_button_width,
        h=search_button_height,
        text="Search",
        font=ui_font_small, # Use same font as input box for consistency
        callback=on_search_button_click
    )

    current_song_time_seconds = 0.0
    paused = False
    dt_ms = 0 # Delta time in milliseconds, for GUI updates like cursor blink

    running = True
    while running:
        dt_ms = clock.tick(FPS)
        dt_seconds = dt_ms / 1000.0

        if not paused:
            current_song_time_seconds += dt_seconds

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # --- GUI Element Event Handling ---
            # Pass event to input box first. If it's active, it might consume KEYDOWNs.
            input_box_action = search_input_box.handle_event(event)
            if input_box_action == 'enter_pressed':
                on_search_button_click()

            search_button.handle_event(event) # Then to the button
            # --- End GUI Element Event Handling ---

            # Only process game-related KEYDOWN if text input is NOT active
            if not search_input_box.active:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_p:
                        paused = not paused
                    if event.key == pygame.K_r:
                        current_song_time_seconds = 0.0
                        the_piano_roll.hit_effects.clear()
                        active_computer_keys_midi = [KEY_TO_MIDI[k] for k in KEY_TO_MIDI if piano_keyboard.pressed_keys.get(KEY_TO_MIDI[k])]
                        for note_to_release in active_computer_keys_midi:
                            piano_keyboard.set_key_pressed(note_to_release, False)

                    # Handle Computer Keyboard Input for Piano
                    if not paused and event.key in KEY_TO_MIDI:
                        midi_note = KEY_TO_MIDI[event.key]
                        piano_keyboard.set_key_pressed(midi_note, True)
                        the_piano_roll.trigger_hit_effect(midi_note)

            # KEYUP events for piano can be processed even if input box was active (e.g. user presses 'a' in box, then releases)
            # However, to prevent stopping a note if 'a' was typed into box, check active state here too.
            # A more robust way is for handle_event to return whether it consumed the event.
            if event.type == pygame.KEYUP:
                 if not search_input_box.active and event.key in KEY_TO_MIDI : # Only if input not active
                    midi_note = KEY_TO_MIDI[event.key]
                    piano_keyboard.set_key_pressed(midi_note, False)

            if event.type == pygame.MOUSEBUTTONDOWN:
                # If mouse click was not on an active GUI element that consumes clicks (like text input activation)
                # For simplicity, assume Button clicks are handled by its handle_event and don't need explicit check here to prevent piano interaction
                # But TextInputBox activation should prevent piano interaction if click is on it.
                if not search_input_box.rect.collidepoint(event.pos): # If click is NOT on input box
                    if not paused and event.button == 1:
                        if piano_keyboard.rect.collidepoint(event.pos): # And click IS on keyboard
                            clicked_midi_note = piano_keyboard.handle_mouse_click(event.pos)
                            if clicked_midi_note is not None:
                                the_piano_roll.trigger_hit_effect(clicked_midi_note)

        # Update game state
        for star in stars:
            star.update()

        search_input_box.update(dt_ms) # Update text input box (e.g., cursor blink)
        the_piano_roll.update(current_song_time_seconds)

        # --- Drawing ---
        # 1. Background (Stars)
        screen.fill(BLACK)
        for star in stars:
            star.draw(screen)

        # 2. Layout Sections
        pygame.draw.rect(screen, HEADER_COLOR, (0, 0, SCREEN_WIDTH, HEADER_HEIGHT))
        pygame.draw.line(screen, BORDER_COLOR, (0, HEADER_HEIGHT - BORDER_WIDTH // 2), (SCREEN_WIDTH, HEADER_HEIGHT - BORDER_WIDTH //2), BORDER_WIDTH)

        main_section_rect = pygame.Rect(0, MAIN_SECTION_Y_START, SCREEN_WIDTH, MAIN_SECTION_HEIGHT)
        pygame.draw.rect(screen, MAIN_SECTION_COLOR, main_section_rect)

        # 3. Application Components (Piano Roll, Keyboard)
        the_piano_roll.draw(screen)
        piano_keyboard.draw(screen)

        # Control Panel Background (drawn before GUI elements on it)
        pygame.draw.rect(screen, CONTROL_PANEL_COLOR, (0, CONTROL_PANEL_Y_START, SCREEN_WIDTH, CONTROL_PANEL_HEIGHT))
        # Border for control panel (optional, if not part of its background rect fill)
        # pygame.draw.rect(screen, BORDER_COLOR, (0, CONTROL_PANEL_Y_START, SCREEN_WIDTH, CONTROL_PANEL_HEIGHT), BORDER_WIDTH)
        pygame.draw.line(screen, BORDER_COLOR, (0, CONTROL_PANEL_Y_START), (SCREEN_WIDTH, CONTROL_PANEL_Y_START ), BORDER_WIDTH) # Ensure top border of control panel is clean


        # 4. GUI Elements in Control Panel
        search_input_box.draw(screen)
        search_button.draw(screen)

        # 5. Top-level UI Text Elements (Title, etc.)
        screen.blit(title_text_surface, title_text_rect)

        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main()
