import pygame

class TextInputBox:
    def __init__(self, x, y, w, h, font,
                 text_color=(200, 200, 200),
                 box_color_inactive=(80, 80, 100),
                 box_color_active=(100, 100, 130),  # Slightly different active color
                 border_color=(180, 180, 200),
                 cursor_color=(230, 230, 230),
                 initial_text="",
                 max_len=50,
                 prompt_text=""): # Optional prompt text when empty and inactive
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.text_color = text_color
        self.box_color_inactive = box_color_inactive
        self.box_color_active = box_color_active
        self.border_color = border_color
        self.cursor_color = cursor_color
        self.text = initial_text
        self.max_len = max_len
        self.prompt_text = prompt_text

        self.active = False
        self.cursor_visible = True
        self.cursor_blink_timer = 0
        self.cursor_blink_interval = 500  # milliseconds

        self.text_surface = self.font.render(self.text, True, self.text_color)
        self.char_width_approx = self.font.size("A")[0] # Approximate for clipping

    def handle_event(self, event):
        action = None
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.cursor_visible = True # Show cursor immediately on click
                self.cursor_blink_timer = 0
            else:
                self.active = False
            return action # Consume click event if it's for activation

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                action = 'enter_pressed'
                # self.active = False # Optionally deactivate on enter
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.active = False # Deactivate on escape
            else:
                if len(self.text) < self.max_len:
                    self.text += event.unicode # Handles most characters, including shift states

            self.text_surface = self.font.render(self.text, True, self.text_color)
        return action

    def update(self, dt_ms): # dt_ms is delta time in milliseconds
        if self.active:
            self.cursor_blink_timer += dt_ms
            if self.cursor_blink_timer >= self.cursor_blink_interval:
                self.cursor_blink_timer = 0
                self.cursor_visible = not self.cursor_visible

    def draw(self, surface):
        current_box_color = self.box_color_active if self.active else self.box_color_inactive
        pygame.draw.rect(surface, current_box_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1) # Border

        # Display prompt text if applicable
        display_text = self.text
        text_color_to_use = self.text_color
        if not self.text and not self.active and self.prompt_text:
            display_text_surface = self.font.render(self.prompt_text, True, (150,150,150)) # Dimmer prompt
        else:
            display_text_surface = self.font.render(display_text, True, text_color_to_use)

        # Basic text clipping: only show what fits
        # For more advanced, render to a subsurface and blit that
        text_render_x = self.rect.x + 5
        text_render_y = self.rect.y + (self.rect.height - display_text_surface.get_height()) // 2

        # Clipping: calculate visible portion of text
        max_visible_chars = (self.rect.width - 10) // self.char_width_approx if self.char_width_approx > 0 else 0

        visible_text = display_text
        if display_text_surface.get_width() > self.rect.width - 10 : # 10 for padding
            # Show end of text that fits, or implement scrolling text
             start_char_index = max(0, len(display_text) - max_visible_chars +1) # +1 for cursor space if at end
             visible_text = display_text[start_char_index:]
             display_text_surface = self.font.render(visible_text, True, text_color_to_use)


        surface.blit(display_text_surface, (text_render_x, text_render_y))

        if self.active and self.cursor_visible:
            # Calculate cursor position based on the *rendered* visible text
            cursor_x_offset = display_text_surface.get_width()
            cursor_x = text_render_x + cursor_x_offset
            cursor_y_start = self.rect.y + 5
            cursor_y_end = self.rect.y + self.rect.height - 5
            pygame.draw.line(surface, self.cursor_color, (cursor_x, cursor_y_start), (cursor_x, cursor_y_end), 1)

    def get_text(self):
        return self.text

    def set_text(self, new_text):
        self.text = new_text
        self.text_surface = self.font.render(self.text, True, self.text_color)


class Button:
    def __init__(self, x, y, w, h, text, font,
                 text_color=(230, 230, 230),
                 button_color=(70, 70, 90),
                 hover_color=(100, 100, 120),
                 disabled_color=(50,50,50),
                 border_color=(150, 150, 150),
                 callback=None,
                 enabled=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.button_color = button_color
        self.hover_color = hover_color
        self.disabled_color = disabled_color
        self.border_color = border_color
        self.callback = callback
        self.enabled = enabled

        self.is_hovered = False
        self.is_pressed = False # For visual feedback on click (optional)

        self.text_surface = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def handle_event(self, event):
        if not self.enabled:
            return

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.is_pressed = True # Visual feedback
                if self.callback:
                    self.callback()

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_pressed:
                self.is_pressed = False # Reset visual feedback
                # Callback is usually on MOUSEBUTTONDOWN for responsiveness

    def draw(self, surface):
        current_button_color = self.button_color
        if not self.enabled:
            current_button_color = self.disabled_color
        elif self.is_pressed: # Optional: slightly different color when actively pressed
             current_button_color = pygame.Color(self.hover_color).lerp((0,0,0), 0.2) # Darken hover color
        elif self.is_hovered:
            current_button_color = self.hover_color

        pygame.draw.rect(surface, current_button_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1) # Border
        surface.blit(self.text_surface, self.text_rect)

    def set_text(self, new_text):
        self.text = new_text
        self.text_surface = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def set_enabled(self, enabled_status: bool):
        self.enabled = enabled_status
        self.is_hovered = False # Reset hover state if disabled
        self.is_pressed = False

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("GUI Elements Test")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 18)

    def my_button_action():
        print("Button clicked!")
        text_input.set_text("Button Action!")

    text_input = TextInputBox(50, 50, 300, 40, font, initial_text="Type here...", prompt_text="Enter search term")
    test_button = Button(400, 50, 150, 40, "Test Me", font, callback=my_button_action)

    disabled_button = Button(400, 100, 150, 40, "Disabled", font, enabled=False)


    running = True
    while running:
        dt_ms = clock.tick(60) # Delta time in milliseconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            input_action = text_input.handle_event(event)
            if input_action == 'enter_pressed':
                print(f"Enter pressed in text box. Text: '{text_input.get_text()}'")
                # my_button_action() # Example: trigger button action on enter

            test_button.handle_event(event)
            disabled_button.handle_event(event)


        text_input.update(dt_ms) # Update for cursor blink

        screen.fill((30, 30, 30))
        text_input.draw(screen)
        test_button.draw(screen)
        disabled_button.draw(screen)

        pygame.display.flip()

    pygame.quit()
