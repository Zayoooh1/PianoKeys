import pygame
from music_logic import Note # Assuming music_logic.py is in the same src directory
import mido # For create_test_midi

# --- Constants ---
NOTE_COLOR = (0, 180, 220) # Slightly less bright
NOTE_OUTLINE_COLOR = (80, 200, 240)
HIT_EFFECT_COLOR = (255, 255, 100, 150) # RGBA
HIT_LINE_COLOR = (255, 50, 50, 200) # RGBA for hit line, slightly transparent
SCROLL_SPEED_PIXELS_PER_SECOND = 120.0 # Increased speed

class PianoRoll:
    def __init__(self, x, y, width, height, keyboard_layout_info, notes: list[Note], ticks_per_beat=480, tempo=500000):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.notes = notes if notes else []
        self.keyboard_layout_info = keyboard_layout_info # This contains screen coordinates for keys

        self.visible_note_representations = [] # Stores dicts of {'rect': pygame.Rect, 'note': Note, 'color': tuple}
        self.hit_effects = [] # Stores dicts for visual feedback on key press / note hit

        # Y-coordinate of the "hit line" where notes are considered "played"
        self.hit_line_y = self.y + self.height * 0.85 # Positioned towards the bottom of the piano roll area

        # Time conversion: MIDI ticks to seconds
        self.ticks_per_beat = ticks_per_beat if ticks_per_beat > 0 else 480
        self.tempo_micros_per_beat = tempo if tempo > 0 else 500000 # Default 120 BPM (500,000 microseconds per beat)
        self.seconds_per_tick = self.tempo_micros_per_beat / (1000000.0 * self.ticks_per_beat)

    def _get_key_rect_for_note(self, midi_note):
        """Helper to get key's screen rect info from the keyboard_layout_info."""
        if self.keyboard_layout_info and 'key_rects_map' in self.keyboard_layout_info:
            return self.keyboard_layout_info['key_rects_map'].get(midi_note)
        return None

    def update(self, current_time_seconds: float):
        self.visible_note_representations = []
        for note_obj in self.notes:
            # Calculate note's timing in seconds
            note_start_seconds = note_obj.start_time * self.seconds_per_tick
            note_duration_seconds = note_obj.duration * self.seconds_per_tick

            # Y position: notes scroll from top to bottom. Hit line is fixed.
            # y_offset_pixels is how far the START of the note is from the hit line in pixels
            y_offset_pixels = (note_start_seconds - current_time_seconds) * SCROLL_SPEED_PIXELS_PER_SECOND

            # note_screen_y is the TOP of the note rectangle on screen
            note_screen_y = self.hit_line_y - y_offset_pixels
            note_screen_height = note_duration_seconds * SCROLL_SPEED_PIXELS_PER_SECOND

            # Cull notes that are entirely off-screen (above or below piano roll area)
            if note_screen_y + note_screen_height < self.y or note_screen_y > self.y + self.height:
                continue

            key_info = self._get_key_rect_for_note(note_obj.note)
            if key_info:
                # x position and width are taken directly from the keyboard key's screen projection
                note_screen_x = key_info['x_on_keyboard']
                note_screen_width = key_info['w_on_keyboard']

                note_render_rect = pygame.Rect(
                    note_screen_x,
                    note_screen_y - note_screen_height, # Pygame rects are (x, y, w, h) where y is top
                    note_screen_width,
                    max(1, note_screen_height) # Ensure height is at least 1 pixel
                )
                self.visible_note_representations.append({'rect': note_render_rect, 'note_obj': note_obj, 'color': NOTE_COLOR})

        # Update hit effects (e.g., fade out, expand)
        new_effects = []
        for effect in self.hit_effects:
            effect['alpha'] -= 10 # Fade out speed
            effect['size'] += 3   # Expansion speed
            if effect['alpha'] > 0 and effect['size'] < effect['max_size']:
                new_effects.append(effect)
        self.hit_effects = new_effects

    def draw(self, surface):
        # Draw a background for the piano roll area (optional, good for clipping viz)
        # pygame.draw.rect(surface, (5, 15, 35, 100), (self.x, self.y, self.width, self.height)) # Slightly transparent dark blue

        # Draw the hit line
        # Create a surface for transparency if color has alpha
        hit_line_surf = pygame.Surface((self.width, 3), pygame.SRCALPHA)
        hit_line_surf.fill(HIT_LINE_COLOR)
        surface.blit(hit_line_surf, (self.x, self.hit_line_y - 1))


        # Draw visible notes (clipped to the piano roll area)
        for item in self.visible_note_representations:
            rect = item['rect']
            color = item['color']

            # Clip the note rectangle to the piano roll's bounds before drawing
            clipped_rect = rect.clip(pygame.Rect(self.x, self.y, self.width, self.height))

            if clipped_rect.width > 0 and clipped_rect.height > 0:
                pygame.draw.rect(surface, color, clipped_rect)
                pygame.draw.rect(surface, NOTE_OUTLINE_COLOR, clipped_rect, 1) # Outline

        # Draw hit effects
        for effect in self.hit_effects:
            key_info = self._get_key_rect_for_note(effect['note_midi'])
            if key_info:
                center_x = key_info['x_on_keyboard'] + key_info['w_on_keyboard'] / 2

                # Create a temporary surface for the circle with per-pixel alpha
                effect_surf = pygame.Surface((effect['size'], effect['size']), pygame.SRCALPHA)
                current_effect_color = HIT_EFFECT_COLOR[:3] + (max(0,min(255,int(effect['alpha']))),) # Ensure alpha is valid

                pygame.draw.circle(effect_surf, current_effect_color,
                                   (effect['size'] // 2, effect['size'] // 2), # Center of the temp surface
                                   effect['size'] // 2) # Radius

                # Blit centered on the key's x-position at the hit line's y-position
                surface.blit(effect_surf, (center_x - effect['size'] // 2, self.hit_line_y - effect['size'] // 2))

    def trigger_hit_effect(self, midi_note):
        """Adds a new hit effect for the given MIDI note."""
        key_info = self._get_key_rect_for_note(midi_note)
        if key_info:
            initial_size = int(key_info['w_on_keyboard'] * 0.8) # Start slightly smaller than key width
            self.hit_effects.append({
                'note_midi': midi_note,
                'alpha': 255,
                'size': initial_size,
                'max_size': initial_size * 3 # Expand to 3x initial size
            })

def create_test_midi(file_path="assets/midi/dummy_pianoroll_test.mid", ticks_per_beat=480):
    """Creates a simple MIDI file for testing the piano roll."""
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Define a simple melody: C4, D4, E4, F4, G4, A4, B4, C5
    notes_sequence = [60, 62, 64, 65, 67, 69, 71, 72]
    time_delta = ticks_per_beat // 2  # Duration of each note (e.g., eighth notes if ticks_per_beat is a quarter note)

    # Set tempo (e.g., 120 BPM)
    actual_tempo = mido.bpm2tempo(120) # Microseconds per beat
    track.append(mido.MetaMessage('set_tempo', tempo=actual_tempo, time=0))

    current_tick = 0
    for i, note_val in enumerate(notes_sequence):
        on_time = 0 if i == 0 else time_delta # Delta time from previous event
        track.append(mido.Message('note_on', note=note_val, velocity=80, time=on_time))
        track.append(mido.Message('note_off', note=note_val, velocity=64, time=time_delta))
        current_tick += time_delta * 2 # Account for note_on and note_off time

    try:
        mid.save(file_path)
        print(f"Test MIDI file saved to {file_path}. TicksPerBeat: {ticks_per_beat}, Tempo: {actual_tempo} ({mido.tempo2bpm(actual_tempo):.2f} BPM)")
    except Exception as e:
        print(f"Error saving test MIDI: {e}")
    return ticks_per_beat, actual_tempo


if __name__ == '__main__':
    # Create a dummy MIDI file first (if it doesn't exist or needs update)
    test_ticks_per_beat, test_tempo = create_test_midi("assets/midi/dummy_pianoroll_test.mid")

    pygame.init()
    screen_width_test, screen_height_test = 800, 600
    screen_test = pygame.display.set_mode((screen_width_test, screen_height_test))
    pygame.display.set_caption("Piano Roll Test")
    clock = pygame.time.Clock()

    # --- Mock Keyboard Layout Info for testing PianoRoll independently ---
    mock_key_rects_map = {}
    num_test_keys = 24 # roughly 2 octaves
    white_key_w_test = screen_width_test / (num_test_keys * 7/12) # Approximate white key width
    black_key_w_test = white_key_w_test * 0.6
    current_x_test = 30 # Starting x for the mock keyboard
    start_midi_test = 55 # Approx F3

    for i in range(num_test_keys):
        midi_note_val = start_midi_test + i
        is_white = (midi_note_val % 12) not in [1, 3, 6, 8, 10] # Standard black key MIDI offsets from C
        key_width = white_key_w_test if is_white else black_key_w_test

        # For black keys in mock, just place them sequentially with smaller width.
        # A real keyboard would interleave them. This is just for mapping X positions.
        mock_key_rects_map[midi_note_val] = {
            'x_on_keyboard': current_x_test + (white_key_w_test - key_width)/2 if not is_white else current_x_test, # Center black keys a bit
            'w_on_keyboard': key_width,
            'is_white': is_white,
            'key_rect_obj': pygame.Rect(current_x_test, screen_height_test - 150, key_width, 150) # Dummy rect
        }
        if is_white:
            current_x_test += white_key_w_test
        # Else, black keys don't advance current_x_test in this simple mock as they overlay.

    test_keyboard_layout_info = {'key_rects_map': mock_key_rects_map, 'keyboard_rect': pygame.Rect(30, screen_height_test-150, current_x_test-30, 150)}

    # --- Parse notes from the test MIDI file ---
    parsed_notes_for_test = []
    try:
        from music_logic import parse_midi_file # Ensure music_logic.py is accessible
        parsed_notes_for_test = parse_midi_file("assets/midi/dummy_pianoroll_test.mid")
        if not parsed_notes_for_test:
             print("No notes parsed from dummy_pianoroll_test.mid for the test run.")
    except ImportError:
        print("Could not import parse_midi_file from music_logic for the test.")
    except Exception as e:
        print(f"Error parsing MIDI for test: {e}")

    # --- Piano Roll Instance ---
    piano_roll_area_rect = pygame.Rect(50, 50, screen_width_test - 100, screen_height_test - 250) # Area for piano roll display
    piano_roll_instance = PianoRoll(
        piano_roll_area_rect.x, piano_roll_area_rect.y,
        piano_roll_area_rect.width, piano_roll_area_rect.height,
        test_keyboard_layout_info,
        parsed_notes_for_test,
        ticks_per_beat=test_ticks_per_beat,
        tempo=test_tempo
    )

    current_song_time_seconds_test = 0.0
    test_font = pygame.font.SysFont("Arial", 20)
    paused_test = False

    running_test_loop = True
    while running_test_loop:
        delta_time_seconds = clock.tick(60) / 1000.0
        if not paused_test:
            current_song_time_seconds_test += delta_time_seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running_test_loop = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running_test_loop = False
                if event.key == pygame.K_r: # Reset time
                    current_song_time_seconds_test = 0.0
                    piano_roll_instance.hit_effects.clear() # Clear effects on reset
                if event.key == pygame.K_p: # Pause
                    paused_test = not paused_test
                if event.key == pygame.K_SPACE: # Trigger a test hit effect for C4 (MIDI 60)
                    piano_roll_instance.trigger_hit_effect(60)
            if event.type == pygame.MOUSEBUTTONDOWN: # Test triggering effect on click
                 # Find a note to trigger based on click (very simplified)
                 if parsed_notes_for_test:
                    piano_roll_instance.trigger_hit_effect(parsed_notes_for_test[0].note)


        piano_roll_instance.update(current_song_time_seconds_test)

        screen_test.fill((20, 20, 30)) # Dark background
        pygame.draw.rect(screen_test, (30, 40, 50), piano_roll_area_rect) # Draw piano roll background area
        piano_roll_instance.draw(screen_test) # Draw the piano roll content

        # Display test info
        time_text_surf = test_font.render(f"Time: {current_song_time_seconds_test:.2f}s {'(Paused)' if paused_test else ''}", True, (220,220,220))
        screen_test.blit(time_text_surf, (10, 10))

        notes_info_surf = test_font.render(f"Parsed Notes: {len(parsed_notes_for_test)}, Visible Notes: {len(piano_roll_instance.visible_note_representations)}", True, (220,220,220))
        screen_test.blit(notes_info_surf, (10, screen_height_test - 30))

        pygame.display.flip()

    pygame.quit()
