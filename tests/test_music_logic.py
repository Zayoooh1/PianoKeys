import unittest
import os
import shutil
import mido # For mido.bpm2tempo and creating test MIDI files

# Adjusting import path for src.music_logic
# This assumes 'python -m unittest tests.test_music_logic' is run from the project root,
# or that 'src' is in PYTHONPATH.
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.music_logic import Note, parse_midi_file

class TestParseMidi(unittest.TestCase):

    def setUp(self):
        """Set up test environment before each test."""
        self.test_midi_dir = "temp_test_midi_files"
        os.makedirs(self.test_midi_dir, exist_ok=True)

        self.valid_midi_path = os.path.join(self.test_midi_dir, "test_song.mid")
        self.expected_tpb = 480  # Ticks per beat
        self.expected_tempo = mido.bpm2tempo(120)  # Microseconds per beat (500000)

        # Define note properties for the test MIDI
        # Note 1: Starts at tick 0, duration is half a beat
        self.note1_midi = 60  # C4
        self.note1_start_tick = 0
        self.note1_duration_ticks = self.expected_tpb // 2 # e.g., an eighth note if TPB is a quarter

        # Note 2: Starts at tick `expected_tpb` (e.g. on the second beat), duration is one beat
        self.note2_midi = 62  # D4
        self.note2_start_tick = self.expected_tpb
        self.note2_duration_ticks = self.expected_tpb # e.g., a quarter note

        # Create a valid MIDI file programmatically
        mid = mido.MidiFile(ticks_per_beat=self.expected_tpb)
        track = mido.MidiTrack()
        mid.tracks.append(track)

        # Add tempo and notes
        track.append(mido.MetaMessage('set_tempo', tempo=self.expected_tempo, time=0))

        # Note 1
        track.append(mido.Message('note_on', note=self.note1_midi, velocity=64, time=self.note1_start_tick))
        track.append(mido.Message('note_off', note=self.note1_midi, velocity=64, time=self.note1_duration_ticks))

        # Note 2 - Delta time calculation is crucial
        # Time for note_on of note2 is relative to note_off of note1
        delta_time_for_note2_on = self.note2_start_tick - (self.note1_start_tick + self.note1_duration_ticks)
        track.append(mido.Message('note_on', note=self.note2_midi, velocity=64, time=delta_time_for_note2_on))
        track.append(mido.Message('note_off', note=self.note2_midi, velocity=64, time=self.note2_duration_ticks))

        mid.save(self.valid_midi_path)

        # Path for an empty MIDI file
        self.empty_midi_path = os.path.join(self.test_midi_dir, "empty.mid")
        with open(self.empty_midi_path, 'wb') as f:
            pass # Create an empty file

        # Path for a non-existent MIDI file
        self.non_existent_midi_path = os.path.join(self.test_midi_dir, "non_existent.mid")
        # Ensure it doesn't exist (it shouldn't, but good practice if tests could re-run)
        if os.path.exists(self.non_existent_midi_path):
            os.remove(self.non_existent_midi_path)


    def tearDown(self):
        """Clean up test environment after each test."""
        if os.path.exists(self.test_midi_dir):
            shutil.rmtree(self.test_midi_dir, ignore_errors=True)

    def test_parse_valid_midi(self):
        """Test parsing a correctly formatted MIDI file with notes and tempo."""
        result = parse_midi_file(self.valid_midi_path)

        self.assertIsNotNone(result, "parse_midi_file returned None for a valid MIDI.")
        self.assertIsInstance(result, dict, "Result should be a dictionary.")

        self.assertEqual(result.get('ticks_per_beat'), self.expected_tpb, "Ticks per beat mismatch.")
        self.assertEqual(result.get('tempo'), self.expected_tempo, "Tempo mismatch.")

        self.assertIn('notes', result, "Result dictionary missing 'notes' key.")
        self.assertIsInstance(result['notes'], list, "'notes' should be a list.")

        self.assertEqual(len(result['notes']), 2, "Incorrect number of notes parsed.")

        # Validate Note 1
        parsed_note1 = result['notes'][0]
        self.assertEqual(parsed_note1.note, self.note1_midi, "Note 1 MIDI value mismatch.")
        # Mido messages store absolute time from the beginning of the track for note_on/off events
        # Our parse_midi_file converts these to start_time and duration for Note objects
        self.assertEqual(parsed_note1.start_time, self.note1_start_tick, "Note 1 start time mismatch.")
        self.assertEqual(parsed_note1.duration, self.note1_duration_ticks, "Note 1 duration mismatch.")

        # Validate Note 2
        parsed_note2 = result['notes'][1]
        self.assertEqual(parsed_note2.note, self.note2_midi, "Note 2 MIDI value mismatch.")
        self.assertEqual(parsed_note2.start_time, self.note2_start_tick, "Note 2 start time mismatch.")
        self.assertEqual(parsed_note2.duration, self.note2_duration_ticks, "Note 2 duration mismatch.")

    def test_parse_non_existent_file(self):
        """Test parsing a non-existent MIDI file path."""
        result = parse_midi_file(self.non_existent_midi_path)
        self.assertIsNone(result, "parse_midi_file did not return None for a non-existent file.")

    def test_parse_empty_file(self):
        """Test parsing an empty file (which is not a valid MIDI)."""
        result = parse_midi_file(self.empty_midi_path)
        # mido.MidiFile on an empty file typically raises an EOFError or similar parsing error.
        # The parse_midi_file function should catch this and return None.
        self.assertIsNone(result, "parse_midi_file did not return None for an empty/invalid MIDI file.")

    def test_parse_midi_no_tempo_message(self):
        """Test parsing a MIDI with notes but no explicit tempo message."""
        no_tempo_midi_path = os.path.join(self.test_midi_dir, "no_tempo.mid")
        mid = mido.MidiFile(ticks_per_beat=self.expected_tpb)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        # Note 1 (same as valid_midi_path)
        track.append(mido.Message('note_on', note=self.note1_midi, velocity=64, time=self.note1_start_tick))
        track.append(mido.Message('note_off', note=self.note1_midi, velocity=64, time=self.note1_duration_ticks))
        mid.save(no_tempo_midi_path)

        result = parse_midi_file(no_tempo_midi_path)
        self.assertIsNotNone(result, "parse_midi_file returned None for MIDI with no tempo message.")
        # Should use default tempo
        self.assertEqual(result['tempo'], 500000, "Default tempo not used when no tempo message present.")
        self.assertEqual(result['ticks_per_beat'], self.expected_tpb)
        self.assertEqual(len(result['notes']), 1)

    def test_parse_midi_no_notes(self):
        """Test parsing a MIDI file that has a tempo message but no notes in the selected track."""
        no_notes_midi_path = os.path.join(self.test_midi_dir, "no_notes.mid")
        mid = mido.MidiFile(ticks_per_beat=self.expected_tpb)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage('set_tempo', tempo=self.expected_tempo, time=0))
        # Add another empty track or a track with only meta messages
        meta_track = mido.MidiTrack()
        mid.tracks.append(meta_track)
        meta_track.append(mido.MetaMessage('track_name', name='Empty Track', time=0))
        mid.save(no_notes_midi_path)

        result = parse_midi_file(no_notes_midi_path)
        # parse_midi_file is expected to return None if no notes are found in the chosen track.
        self.assertIsNone(result, "parse_midi_file did not return None for a MIDI with no notes.")


if __name__ == '__main__':
    unittest.main(verbosity=2)
