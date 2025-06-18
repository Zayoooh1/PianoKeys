import pygame
import os # Added for path joining and checking file existence

# --- Constants ---
WHITE_KEY_COLOR = (230, 230, 230)
BLACK_KEY_COLOR = (30, 30, 30)
WHITE_KEY_PRESSED_COLOR = (180, 180, 220)  # Light blue/purple accent
BLACK_KEY_PRESSED_COLOR = (100, 100, 150) # Darker accent for black keys
KEY_BORDER_COLOR = (100, 100, 100)
SHADOW_COLOR_LIGHT = (250, 250, 250) # Brighter highlight for top/left
SHADOW_COLOR_DARK = (180, 180, 180)  # Softer shadow for white keys bottom/right
BLACK_KEY_HIGHLIGHT_COLOR = (60, 60, 60) # Subtle highlight for black keys

# Notes in an octave for mapping. C=0, C#=1, D=2 ... B=11
WHITE_KEY_NOTES_IN_OCTAVE = [0, 2, 4, 5, 7, 9, 11] # C, D, E, F, G, A, B
BLACK_KEY_NOTES_IN_OCTAVE = [1, 3, 6, 8, 10] # C#, D#, F#, G#, A#
ALL_NOTES_IN_OCTAVE = sorted(WHITE_KEY_NOTES_IN_OCTAVE + BLACK_KEY_NOTES_IN_OCTAVE)

SOUND_FILES_PATH = "assets/sounds/"
PLACEHOLDER_SOUND_FILENAME = "placeholder_sound.wav"

class Keyboard:
    def __init__(self, x, y, width, height, start_midi_note=60, num_octaves=2): # Default: C4, 2 octaves
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.start_midi_note = start_midi_note # MIDI note for the first key (leftmost C)
        self.num_octaves = num_octaves

        # Total number of white keys based on octaves. Each octave has 7 white keys.
        self.num_white_keys = 7 * self.num_octaves

        self.white_key_rects = []
        self.black_key_rects = []
        self.white_key_midi_notes = []
        self.black_key_midi_notes = []
        self.all_midi_notes = [] # For sound loading

        self.pressed_keys = {}  # {midi_note: True}
        self.key_sounds = {} # {midi_note: pygame.mixer.Sound}

        self._calculate_key_positions() # Populates midi_notes lists
        self._load_sounds() # Loads sounds based on populated midi_notes

    def _calculate_key_positions(self):
        """
        Calculates the positions and MIDI note numbers for all keys on the keyboard.
        This version aims for a more robust calculation of all key types and their MIDI notes.
        """
        self.white_key_rects.clear()
        self.white_key_midi_notes.clear()
        self.black_key_rects.clear()
        self.black_key_midi_notes.clear()
        self.all_midi_notes.clear()

        if self.num_white_keys == 0: return

        white_key_w = self.width / self.num_white_keys
        white_key_h = self.height
        black_key_w = white_key_w * 0.60 # Standard proportion
        black_key_h = white_key_h * 0.60 # Standard proportion

        # Determine the full range of MIDI notes this keyboard should cover
        # start_midi_note is the first C of the keyboard.
        # num_octaves determines how many octaves from that C are shown.
        # For example, if start_midi_note=60 (C4) and num_octaves=2, it covers C4-B5.

        # Iterate through each octave
        for octave_idx in range(self.num_octaves):
            octave_start_midi = self.start_midi_note + (octave_idx * 12)
            octave_start_x = self.x + (octave_idx * 7 * white_key_w) # X offset for the start of this octave's white keys

            # Place white keys for this octave
            for i, note_in_c_scale_offset in enumerate(WHITE_KEY_NOTES_IN_OCTAVE):
                current_midi_note = octave_start_midi + note_in_c_scale_offset
                # Calculate x position based on the white key index within this octave
                current_x = octave_start_x + (i * white_key_w)
                rect = pygame.Rect(current_x, self.y, white_key_w, white_key_h)

                self.white_key_rects.append(rect)
                self.white_key_midi_notes.append(current_midi_note)
                self.all_midi_notes.append(current_midi_note)

            # Place black keys for this octave
            # Black keys are C#, D#, F#, G#, A# (MIDI offsets 1, 3, 6, 8, 10 from C of the octave)
            # Their visual placement is relative to the white keys C, D, F, G, A
            # C (idx 0) -> C# (midi +1)
            # D (idx 1) -> D# (midi +3)
            # E (idx 2)
            # F (idx 3) -> F# (midi +6)
            # G (idx 4) -> G# (midi +8)
            # A (idx 5) -> A# (midi +10)
            # B (idx 6)

            # Positions of black keys relative to the start of the octave (octave_start_x)
            # These are based on which white key they are to the "right" of, visually.
            # C (0*white_key_w), D (1*white_key_w), F (3*white_key_w), G (4*white_key_w), A (5*white_key_w)
            black_key_relative_positions_factor = [0.75, 1.75, 3.75, 4.75, 5.75] # Factors of white_key_w

            for i, black_key_offset_in_octave in enumerate(BLACK_KEY_NOTES_IN_OCTAVE):
                current_midi_note = octave_start_midi + black_key_offset_in_octave
                # Calculate x position for black key
                # It's placed relative to the start of the octave, using the factor for its group.
                # The factor determines which white key boundary it's near.
                # Example: C# (midi offset 1) is associated with factor 0 (C). D# (midi offset 3) with factor 1 (D).
                # F# (midi offset 6) with factor 2 (F), etc.

                # The black_key_relative_positions_factor is indexed by the order of black keys (0 to 4)
                # C# is the 0th black key, D# is 1st, etc.

                # The x position is the start of the octave plus a factor of white_key_w, then centered.
                bk_x = octave_start_x + (black_key_relative_positions_factor[i] * white_key_w) - (black_key_w / 2)
                rect = pygame.Rect(bk_x, self.y, black_key_w, black_key_h)

                self.black_key_rects.append(rect)
                self.black_key_midi_notes.append(current_midi_note)
                self.all_midi_notes.append(current_midi_note)

        self.all_midi_notes.sort() # Ensure all_midi_notes is sorted for sound loading or other uses.

    def _load_sounds(self):
        """Loads sound files for each MIDI note represented by the keyboard."""
        if not pygame.mixer.get_init():
            print("Warning: Pygame mixer not initialized. Cannot load sounds.")
            return

        # Ensure the sound assets directory exists
        if not os.path.exists(SOUND_FILES_PATH):
            print(f"Warning: Sound assets path '{SOUND_FILES_PATH}' not found. Cannot load sounds.")
            # Optionally, create it here: os.makedirs(SOUND_FILES_PATH, exist_ok=True)
            return

        placeholder_path = os.path.join(SOUND_FILES_PATH, PLACEHOLDER_SOUND_FILENAME)
        placeholder_sound = None
        if os.path.exists(placeholder_path):
            try:
                placeholder_sound = pygame.mixer.Sound(placeholder_path)
            except pygame.error as e:
                print(f"Warning: Could not load placeholder sound '{placeholder_path}': {e}")
        else:
            print(f"Warning: Placeholder sound file '{placeholder_path}' not found.")

        for midi_note in self.all_midi_notes:
            sound_file = os.path.join(SOUND_FILES_PATH, f"{midi_note}.wav")
            if os.path.exists(sound_file):
                try:
                    self.key_sounds[midi_note] = pygame.mixer.Sound(sound_file)
                except pygame.error as e:
                    print(f"Warning: Could not load sound for MIDI note {midi_note} from '{sound_file}': {e}. Using placeholder.")
                    if placeholder_sound:
                        self.key_sounds[midi_note] = placeholder_sound
            else:
                if placeholder_sound:
                    self.key_sounds[midi_note] = placeholder_sound
                # else:
                #    print(f"Info: No sound file for MIDI note {midi_note} and no placeholder available.")
        # print(f"Loaded sounds for {len(self.key_sounds)} keys. All notes on keyboard: {len(self.all_midi_notes)}")


    def play_note_sound(self, midi_note):
        """Plays the sound associated with a given MIDI note if available."""
        if not pygame.mixer.get_init(): return # Mixer not initialized

        sound = self.key_sounds.get(midi_note)
        if sound:
            try:
                # Stop any previous instance of this sound on its channel to prevent overlap / cut-off issues
                # Find a free channel or a specific channel if managing them
                # For simplicity, just play. Pygame will find a channel.
                sound.stop() # Stop previous plays of this specific sound object
                sound.play()
            except pygame.error as e:
                print(f"Error playing sound for MIDI note {midi_note}: {e}")
        # else:
        #    print(f"No sound loaded for MIDI note {midi_note}")


    def draw(self, surface):
        # Draw white keys
        for i, rect in enumerate(self.white_key_rects):
            midi_note = self.white_key_midi_notes[i]
            color = WHITE_KEY_PRESSED_COLOR if self.pressed_keys.get(midi_note) else WHITE_KEY_COLOR
            pygame.draw.rect(surface, color, rect)

            # 3D effect for white keys using lines
            # Top and left edges lighter
            pygame.draw.line(surface, SHADOW_COLOR_LIGHT, rect.topleft, rect.topright, 1)
            pygame.draw.line(surface, SHADOW_COLOR_LIGHT, rect.topleft, (rect.left, rect.bottom -1), 1)
            # Bottom and right edges darker (creates a slight bevel)
            pygame.draw.line(surface, SHADOW_COLOR_DARK, (rect.left +1, rect.bottom -1), rect.bottomright, 1)
            pygame.draw.line(surface, SHADOW_COLOR_DARK, rect.topright, rect.bottomright, 1)

            pygame.draw.rect(surface, KEY_BORDER_COLOR, rect, 1) # Border

        # Draw black keys (drawn on top of white keys)
        for i, rect in enumerate(self.black_key_rects):
            midi_note = self.black_key_midi_notes[i]
            color = BLACK_KEY_PRESSED_COLOR if self.pressed_keys.get(midi_note) else BLACK_KEY_COLOR
            pygame.draw.rect(surface, color, rect)

            # Subtle highlight on black keys (e.g., top edge or a slight gradient)
            pygame.draw.line(surface, BLACK_KEY_HIGHLIGHT_COLOR, (rect.left + 1, rect.top + 1), (rect.right -1, rect.top + 1), 2)
            pygame.draw.rect(surface, KEY_BORDER_COLOR, rect, 1) # Border

    def handle_mouse_click(self, pos):
        # Check black keys first as they are drawn on top and thus have click priority
        for i, rect in enumerate(self.black_key_rects):
            if rect.collidepoint(pos):
                midi_note = self.black_key_midi_notes[i]
                midi_note = self.black_key_midi_notes[i]
                # self.pressed_keys[midi_note] = not self.pressed_keys.get(midi_note, False) # Old logic
                self.set_key_pressed(midi_note, not self.pressed_keys.get(midi_note, False)) # Use new method
                return midi_note

        # Then check white keys
        for i, rect in enumerate(self.white_key_rects):
            if rect.collidepoint(pos):
                midi_note = self.white_key_midi_notes[i]
                # self.pressed_keys[midi_note] = not self.pressed_keys.get(midi_note, False) # Old logic
                self.set_key_pressed(midi_note, not self.pressed_keys.get(midi_note, False)) # Use new method
                return midi_note
        return None

    def set_key_pressed(self, midi_note, is_pressed):
        """Sets the pressed state of a key by its MIDI note number and plays sound on initial press."""
        key_was_pressed = self.pressed_keys.get(midi_note, False)

        if is_pressed:
            self.pressed_keys[midi_note] = True
            if not key_was_pressed: # Play sound only if it wasn't already pressed
                self.play_note_sound(midi_note)
        else:
            if midi_note in self.pressed_keys:
                del self.pressed_keys[midi_note]
            # Optionally, could add logic here for "note off" sound or release envelope if sounds were more complex.

    def get_key_layout_info(self):
        """
        Returns a dictionary with information needed by PianoRoll to map notes to key X positions.
        Provides screen coordinates for keys.
        """
        key_rects_map = {}
        # Ensure self.white_key_rects and self.black_key_rects are populated with screen-coordinate rects
        for i, rect in enumerate(self.white_key_rects):
            midi_note = self.white_key_midi_notes[i]
            key_rects_map[midi_note] = {'x_on_keyboard': rect.x, 'w_on_keyboard': rect.width, 'is_white': True, 'key_rect_obj': rect}
        for i, rect in enumerate(self.black_key_rects):
            midi_note = self.black_key_midi_notes[i]
            key_rects_map[midi_note] = {'x_on_keyboard': rect.x, 'w_on_keyboard': rect.width, 'is_white': False, 'key_rect_obj': rect}

        return {
            'key_rects_map': key_rects_map, # Maps MIDI note to its screen x and width
            'keyboard_rect': pygame.Rect(self.x, self.y, self.width, self.height) # Overall keyboard area
        }

if __name__ == '__main__':
    # Basic test setup for the Keyboard class
    pygame.init()
    screen_width_test = 740  # Approx 14 white keys * 50px + padding
    screen_height_test = 300
    screen_test = pygame.display.set_mode((screen_width_test, screen_height_test))
    pygame.display.set_caption("Keyboard Test")

    # Keyboard: x=20, y=50, width=700, height=180. Start C4 (MIDI 60), 2 octaves.
    # 2 octaves = 14 white keys.
    keyboard_instance = Keyboard(x=20, y=60, width=700, height=180, start_midi_note=60, num_octaves=2)

    running_test_loop = True
    test_clock = pygame.time.Clock()

    while running_test_loop:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running_test_loop = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    clicked_note_value = keyboard_instance.handle_mouse_click(event.pos)
                    if clicked_note_value is not None:
                        print(f"Clicked MIDI note: {clicked_note_value}, Pressed state: {keyboard_instance.pressed_keys.get(clicked_note_value)}")
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running_test_loop = False
                if event.key == pygame.K_SPACE: # Example to test set_key_pressed
                    c4_midi = 60
                    is_c4_pressed = keyboard_instance.pressed_keys.get(c4_midi, False)
                    keyboard_instance.set_key_pressed(c4_midi, not is_c4_pressed)
                    print(f"Spacebar: Toggled C4 (MIDI {c4_midi}). New pressed state: {keyboard_instance.pressed_keys.get(c4_midi)}")


        screen_test.fill((40, 40, 70))  # Background for testing
        keyboard_instance.draw(screen_test) # Draw the keyboard
        pygame.display.flip()
        test_clock.tick(60) # Limit FPS

    pygame.quit()
