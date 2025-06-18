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

def parse_midi_file(midi_file_path: str) -> list[Note]:
    """
    Parses a MIDI file and extracts note information into a list of Note objects.

    Args:
        midi_file_path: The path to the MIDI file.

    Returns:
        A list of Note objects, or an empty list if an error occurs.
    """
    notes = []
    active_notes = {}  # To store start times of active notes
    current_time_ticks = 0

    try:
        midi_file = mido.MidiFile(midi_file_path)

        track_to_parse = None
        if not midi_file.tracks:
            print("MIDI file has no tracks.")
            return []

        best_track_index = 0
        if len(midi_file.tracks) > 1:
            print(f"MIDI file has {len(midi_file.tracks)} tracks. Analyzing tracks to find the melody...")
            max_note_on_events = -1
            for i, track in enumerate(midi_file.tracks):
                note_on_count = sum(1 for msg in track if msg.type == 'note_on' and msg.velocity > 0)
                print(f"Track {i}: {note_on_count} note_on events")
                if note_on_count > max_note_on_events:
                    max_note_on_events = note_on_count
                    best_track_index = i
            print(f"Selected track {best_track_index} as the melody track.")
            track_to_parse = midi_file.tracks[best_track_index]
        else:
            track_to_parse = midi_file.tracks[0]


        for msg in track_to_parse:
            current_time_ticks += msg.time  # Accumulate delta time to get absolute time

            if msg.type == 'note_on' and msg.velocity > 0:
                active_notes[msg.note] = current_time_ticks
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in active_notes:
                    start_time = active_notes.pop(msg.note)
                    duration = current_time_ticks - start_time
                    if duration > 0: # Add note only if duration is positive
                        notes.append(Note(note=msg.note, start_time=start_time, duration=duration))

        notes.sort(key=lambda x: x.start_time)

    except FileNotFoundError:
        print(f"Error: MIDI file not found at {midi_file_path}")
        return []
    except mido.midifiles.meta.KeySignatureError as e:
        # This is a specific error that can occur with some MIDI files
        # For now, we'll treat it like any other parsing error.
        print(f"Error parsing MIDI file {midi_file_path} (KeySignatureError): {e}")
        return []
    except Exception as e:
        print(f"Error parsing MIDI file {midi_file_path}: {e}")
        return []

    return notes

if __name__ == '__main__':
    note1 = Note(note=60, start_time=0.0, duration=0.5)
    print(note1)

    print("\nTesting parse_midi_file (requires a MIDI file):")
    # Attempt to parse the dummy MIDI file.
    # Since it's empty, it might lead to specific mido errors or return an empty list.
    test_notes = parse_midi_file("assets/midi/dummy.mid")
    if test_notes:
       for note_obj in test_notes: # Renamed to avoid conflict with class name
           print(note_obj)
    else:
       print("No notes parsed from dummy.mid (it might be empty or malformed).")

    print("\nTo test parse_midi_file more thoroughly, place a valid MIDI file (e.g., in assets/midi/) and call parse_midi_file with its path.")
    # Example:
    # real_test_notes = parse_midi_file("assets/midi/your_actual_midi_file.mid")
    # if real_test_notes:
    #    for note_obj in real_test_notes:
    #        print(note_obj)
    # else:
    #    print("Could not parse your_actual_midi_file.mid")
