# src/music_logic.py
import mido

class Note:
    """Represents a musical note with its properties."""
    def __init__(self, note: int, start_time: float, duration: float):
        """
        Initializes a Note object.

        Args:
            note: The MIDI number of the note.
            start_time: The time (in ticks) when the note starts.
            duration: The duration (in ticks) for which the note plays.
        """
        self.note = note
        self.start_time = start_time
        self.duration = duration

    def __repr__(self):
        return f"Note(note={self.note}, start_time={self.start_time}, duration={self.duration})"

def parse_midi_file(midi_file_path: str) -> dict | None:
    """
    Parses a MIDI file and extracts note information, ticks_per_beat, and tempo.

    Args:
        midi_file_path: The path to the MIDI file.

    Returns:
        A dictionary {'notes': list[Note], 'ticks_per_beat': int, 'tempo': int}
        or None if an error occurs or no notes are found.
    """
    notes_list = [] # Renamed to avoid conflict with the class name
    active_notes = {}  # To store start times of active notes
    current_time_ticks = 0

    # Default tempo (120 BPM = 500,000 microseconds per beat)
    tempo_micros_per_beat = 500000
    ticks_per_beat_from_file = None

    try:
        midi_file = mido.MidiFile(midi_file_path)
        ticks_per_beat_from_file = midi_file.ticks_per_beat

        # Attempt to find the first set_tempo message to get initial tempo
        # This can be in any track, typically a meta message track or the first track.
        # For simplicity, we'll check the first track, or all if needed.
        # A more robust solution might iterate all tracks for meta messages before note processing.
        tempo_found = False
        for i, track in enumerate(midi_file.tracks):
            for msg in track:
                if msg.is_meta and msg.type == 'set_tempo':
                    tempo_micros_per_beat = msg.tempo
                    tempo_found = True
                    # print(f"Found tempo: {tempo_micros_per_beat} us/beat (from track {i})")
                    break # Use the first tempo message found
            if tempo_found:
                break

        track_to_parse = None
        if not midi_file.tracks:
            print(f"Warning: MIDI file '{midi_file_path}' has no tracks.")
            return None # No tracks, so no notes

        # Heuristic: Choose the track with the most note_on events.
        # This is a common way to find a melody track if not explicitly known.
        best_track_index = -1
        max_note_on_events = -1

        for i, track in enumerate(midi_file.tracks):
            note_on_count = sum(1 for msg in track if msg.type == 'note_on' and msg.velocity > 0)
            # print(f"Track {i}: {note_on_count} note_on events")
            if note_on_count > max_note_on_events:
                max_note_on_events = note_on_count
                best_track_index = i

        if best_track_index != -1:
            # print(f"Selected track {best_track_index} as the primary note track (events: {max_note_on_events}).")
            track_to_parse = midi_file.tracks[best_track_index]
        else: # No track with note_on events found
            print(f"Warning: No track with note_on events found in '{midi_file_path}'.")
            return None # No notes to parse

        for msg in track_to_parse:
            current_time_ticks += msg.time  # Accumulate delta time

            if msg.type == 'note_on' and msg.velocity > 0:
                active_notes[msg.note] = current_time_ticks
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in active_notes:
                    start_time = active_notes.pop(msg.note)
                    duration = current_time_ticks - start_time
                    if duration > 0:
                        notes_list.append(Note(note=msg.note, start_time=start_time, duration=duration))

        if not notes_list:
            # print(f"Warning: No notes extracted from track {best_track_index} in '{midi_file_path}'.")
            # Depending on strictness, could return None here or an empty list with tempo/tpb.
            # For now, if no notes, consider it as "nothing to play".
            return None

        notes_list.sort(key=lambda x: x.start_time)

    except FileNotFoundError:
        print(f"Error: MIDI file not found at '{midi_file_path}'")
        return None
    except mido.midifiles.meta.KeySignatureError as e: # Specific mido error
        print(f"Error parsing MIDI file '{midi_file_path}' (KeySignatureError): {e}")
        return None
    except Exception as e: # Catch other potential mido or general errors
        print(f"Error parsing MIDI file '{midi_file_path}': {e}")
        return None

    return {
        'notes': notes_list,
        'ticks_per_beat': ticks_per_beat_from_file if ticks_per_beat_from_file is not None else 480, # Default if somehow not set
        'tempo': tempo_micros_per_beat
    }

if __name__ == '__main__':
    note1 = Note(note=60, start_time=0.0, duration=0.5)
    print(note1)

    print("\nTesting parse_midi_file with a potentially empty or minimal MIDI:")
    parsed_data_dummy = parse_midi_file("assets/midi/dummy.mid")
    if parsed_data_dummy:
       print(f"Parsed dummy.mid: {len(parsed_data_dummy['notes'])} notes. TPB: {parsed_data_dummy['ticks_per_beat']}, Tempo: {parsed_data_dummy['tempo']}")
       # for note_obj in parsed_data_dummy['notes']: print(note_obj)
    else:
       print("Could not parse dummy.mid or it contained no playable notes.")

    print("\nTo test parse_midi_file more thoroughly, create a valid MIDI file (e.g., using create_test_midi from piano_roll.py) and call parse_midi_file with its path.")
    # Example:
    # from piano_roll import create_test_midi # Assuming piano_roll.py is in the same directory for direct test
    # test_midi_path = "assets/midi/generated_test.mid"
    # create_test_midi(test_midi_path)
    # parsed_generated_data = parse_midi_file(test_midi_path)
    # if parsed_generated_data:
    #    print(f"Parsed {test_midi_path}: {len(parsed_generated_data['notes'])} notes. TPB: {parsed_generated_data['ticks_per_beat']}, Tempo: {parsed_generated_data['tempo']}")
    # Example:
    # real_test_notes = parse_midi_file("assets/midi/your_actual_midi_file.mid")
    # if real_test_notes:
    #    for note_obj in real_test_notes:
    #        print(note_obj)
    # else:
    #    print("Could not parse your_actual_midi_file.mid")
