import unittest
import pygame
import sys
import os

# Adjusting import path for src.gui_elements
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.gui_elements import TextInputBox, Button

# It's good practice to initialize Pygame modules needed for tests, especially font.
# This can be done globally or in a setUpModule.
pygame.font.init() # Initialize font module specifically
# pygame.init() # Alternatively, initialize all of pygame

class TestTextInputBox(unittest.TestCase):

    def setUp(self):
        self.font = pygame.font.Font(None, 30) # Default Pygame font, size 30
        self.input_box = TextInputBox(
            x=50, y=50, w=200, h=40,
            font=self.font,
            initial_text="Hello",
            max_len=10,
            prompt_text="Enter..."
        )

    def test_initial_state(self):
        self.assertEqual(self.input_box.get_text(), "Hello", "Initial text mismatch.")
        self.assertFalse(self.input_box.active, "Input box should be inactive initially.")
        self.assertEqual(self.input_box.prompt_text, "Enter...", "Prompt text mismatch.")

    def test_activation_click(self):
        # Click inside to activate
        inside_pos = (self.input_box.rect.centerx, self.input_box.rect.centery)
        event_activate = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': inside_pos})
        self.input_box.handle_event(event_activate)
        self.assertTrue(self.input_box.active, "Input box did not activate on click inside.")

        # Click outside to deactivate
        outside_pos = (self.input_box.rect.x - 10, self.input_box.rect.y - 10)
        event_deactivate = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': outside_pos})
        self.input_box.handle_event(event_deactivate)
        self.assertFalse(self.input_box.active, "Input box did not deactivate on click outside.")

    def test_text_input_add_char(self):
        self.input_box.active = True # Activate for text input
        self.input_box.set_text("") # Clear initial text

        # Simulate typing 'abc'
        event_a = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_a, 'unicode': 'a'})
        self.input_box.handle_event(event_a)
        self.assertEqual(self.input_box.get_text(), "a", "Text after 'a' input incorrect.")

        event_b = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_b, 'unicode': 'b'})
        self.input_box.handle_event(event_b)
        self.assertEqual(self.input_box.get_text(), "ab", "Text after 'b' input incorrect.")

        event_c = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_c, 'unicode': 'c'})
        self.input_box.handle_event(event_c)
        self.assertEqual(self.input_box.get_text(), "abc", "Text after 'c' input incorrect.")

    def test_text_input_backspace(self):
        self.input_box.active = True
        self.input_box.set_text("test")

        event_backspace = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_BACKSPACE, 'unicode': ''}) # Unicode is empty for backspace
        self.input_box.handle_event(event_backspace)
        self.assertEqual(self.input_box.get_text(), "tes", "Text after backspace incorrect.")

        self.input_box.handle_event(event_backspace)
        self.assertEqual(self.input_box.get_text(), "te", "Text after second backspace incorrect.")

        self.input_box.handle_event(event_backspace)
        self.input_box.handle_event(event_backspace)
        self.assertEqual(self.input_box.get_text(), "", "Text not empty after clearing with backspace.")

        self.input_box.handle_event(event_backspace) # Backspace on empty string
        self.assertEqual(self.input_box.get_text(), "", "Backspace on empty string changed text.")


    def test_text_input_max_len(self):
        self.input_box.active = True
        self.input_box.set_text("")
        self.input_box.max_len = 3 # Override default for this test

        for char_code in range(ord('a'), ord('e')): # Try to type 'a', 'b', 'c', 'd'
            event = pygame.event.Event(pygame.KEYDOWN, {'key': char_code, 'unicode': chr(char_code)})
            self.input_box.handle_event(event)

        self.assertEqual(self.input_box.get_text(), "abc", "Text input exceeded max_len.")

    def test_enter_press_signal(self):
        self.input_box.active = True
        event_enter = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN, 'unicode': '\r'})
        action = self.input_box.handle_event(event_enter)
        self.assertEqual(action, 'enter_pressed', "Enter key did not return 'enter_pressed'.")

    def test_escape_deactivates(self):
        self.input_box.active = True
        event_escape = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE, 'unicode': '\x1b'}) # Escape unicode
        self.input_box.handle_event(event_escape)
        self.assertFalse(self.input_box.active, "Escape key did not deactivate the input box.")


class TestButton(unittest.TestCase):

    def setUp(self):
        self.font = pygame.font.Font(None, 30)
        self.callback_called = False

        def mock_callback():
            self.callback_called = True

        self.mock_callback = mock_callback
        self.button = Button(
            x=100, y=100, w=150, h=50,
            text="Click Me",
            font=self.font,
            callback=self.mock_callback
        )

    def test_initial_state(self):
        self.assertEqual(self.button.text, "Click Me", "Initial button text mismatch.")
        self.assertTrue(self.button.enabled, "Button should be enabled initially.")
        self.assertFalse(self.callback_called, "Callback should not be called initially.")

    def test_hover_state(self):
        # Mouse not over
        event_motion_outside = pygame.event.Event(pygame.MOUSEMOTION, {'pos': (0,0)})
        self.button.handle_event(event_motion_outside)
        self.assertFalse(self.button.is_hovered, "Button should not be hovered.")

        # Mouse over
        inside_pos = self.button.rect.center
        event_motion_inside = pygame.event.Event(pygame.MOUSEMOTION, {'pos': inside_pos})
        self.button.handle_event(event_motion_inside)
        self.assertTrue(self.button.is_hovered, "Button should be hovered when mouse is over.")

    def test_callback_on_click(self):
        # Simulate hover first
        self.button.is_hovered = True # Directly set for simplicity, or simulate MOUSEMOTION

        # Simulate click
        event_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': self.button.rect.center})
        self.button.handle_event(event_click)

        # Callback is usually on MOUSEBUTTONDOWN
        self.assertTrue(self.callback_called, "Callback was not called on button click.")
        self.assertTrue(self.button.is_pressed, "Button should be in pressed state after MOUSEBUTTONDOWN.")

        # Simulate mouse up
        event_mouseup = pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 1, 'pos': self.button.rect.center})
        self.button.handle_event(event_mouseup)
        self.assertFalse(self.button.is_pressed, "Button should not be in pressed state after MOUSEBUTTONUP.")


    def test_no_callback_if_disabled(self):
        self.button.set_enabled(False)
        self.button.is_hovered = True # Assume mouse is over

        event_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': self.button.rect.center})
        self.button.handle_event(event_click)

        self.assertFalse(self.callback_called, "Callback should not be called when button is disabled.")

    def test_set_text(self):
        new_text = "New Label"
        self.button.set_text(new_text)
        self.assertEqual(self.button.text, new_text, "Button text not updated by set_text.")
        # Could also check self.button.text_surface if it's public and important to test re-rendering.

    def test_set_enabled(self):
        self.button.set_enabled(False)
        self.assertFalse(self.button.enabled, "Button enabled state not updated by set_enabled(False).")

        self.button.set_enabled(True)
        self.assertTrue(self.button.enabled, "Button enabled state not updated by set_enabled(True).")


if __name__ == '__main__':
    # Pygame needs to be initialized for font rendering, even if no display is shown.
    # pygame.init() # Initializes all modules, including font.
    # Or, more specifically:
    # pygame.font.init() # Done at the top of the file

    unittest.main(verbosity=2)

    # pygame.quit() # Clean up Pygame after tests if pygame.init() was called.
    pygame.font.quit() # Clean up font module if only font was initialized.
