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


class ScrollableList:
    def __init__(self, x, y, w, h, font,
                 item_height=30,
                 text_color=(220, 220, 220),
                 bg_color=(40, 40, 60),
                 hover_item_color=(60, 60, 80),
                 selected_item_color=(80, 80, 110),
                 scrollbar_color=(100, 100, 120),
                 scrollbar_thumb_color=(150, 150, 180),
                 border_color=(120,120,150)):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.item_height = item_height
        self.text_color = text_color
        self.bg_color = bg_color
        self.hover_item_color = hover_item_color
        self.selected_item_color = selected_item_color # For click feedback, not persistent selection
        self.scrollbar_color = scrollbar_color
        self.scrollbar_thumb_color = scrollbar_thumb_color
        self.border_color = border_color

        self.items_data = []  # List of dicts, e.g., [{'title': 'Song 1', 'url': '...'}, ...]
        self.rendered_items = [] # List of {'surface': Surface, 'rect': Rect, 'data_idx': int}

        self.scroll_y_offset = 0  # How many pixels the content is scrolled up
        self.max_visible_items = self.rect.height // self.item_height

        self.scrollbar_width = 15
        self.scrollbar_rect = None
        self.scrollbar_thumb_rect = None
        self.dragging_scrollbar = False
        self.drag_start_y = 0
        self.drag_start_scroll_y = 0

        self.hovered_item_idx_rel = None # Relative index of hovered item on screen
        self.selected_index_abs = None # Absolute index in self.items_data of last clicked item

    def set_items(self, items_data_list: list[dict]):
        self.items_data = items_data_list if items_data_list else []
        self.scroll_y_offset = 0
        self.hovered_item_idx_rel = None
        self.selected_index_abs = None
        self._render_visible_items()
        self._update_scrollbar()

    def _render_visible_items(self):
        self.rendered_items = []
        start_idx = self.scroll_y_offset // self.item_height

        for i in range(start_idx, min(len(self.items_data), start_idx + self.max_visible_items + 1)): # +1 for partial item
            if i < 0 : continue # Should not happen with proper scroll_y_offset limits

            item_data = self.items_data[i]
            text_to_render = item_data.get('title', "Untitled") # Expect 'title' key

            item_surface = self.font.render(text_to_render, True, self.text_color)

            # Position relative to the scrollable list's top-left
            item_y_pos = (i * self.item_height) - self.scroll_y_offset

            # Only add if it's at least partially visible within the main rect height
            if item_y_pos < self.rect.height and item_y_pos + self.item_height > 0:
                 self.rendered_items.append({
                    'surface': item_surface,
                    'abs_idx': i, # Absolute index in self.items_data
                    'screen_y': self.rect.y + item_y_pos # y-coord on the actual screen
                })

    def _update_scrollbar(self):
        if not self.items_data or len(self.items_data) <= self.max_visible_items:
            self.scrollbar_rect = None
            self.scrollbar_thumb_rect = None
            return

        self.scrollbar_rect = pygame.Rect(
            self.rect.right - self.scrollbar_width - 2, # -2 for padding
            self.rect.top + 2, # +2 for padding
            self.scrollbar_width,
            self.rect.height - 4 # -4 for padding
        )

        content_height = len(self.items_data) * self.item_height
        thumb_height = max(20, self.scrollbar_rect.height * (self.rect.height / content_height))

        # Scroll position (0.0 to 1.0)
        scroll_progress = self.scroll_y_offset / (content_height - self.rect.height) if content_height > self.rect.height else 0

        thumb_y = self.scrollbar_rect.top + scroll_progress * (self.scrollbar_rect.height - thumb_height)

        self.scrollbar_thumb_rect = pygame.Rect(
            self.scrollbar_rect.x,
            thumb_y,
            self.scrollbar_width,
            thumb_height
        )

    def handle_event(self, event: pygame.event.Event):
        clicked_item_abs_idx = None
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_item_idx_rel = None # Reset hover on each event cycle before check

        # Check for hover over list items
        if self.rect.collidepoint(mouse_pos):
            # Check if not over scrollbar (if it exists and mouse is over it)
            is_over_scrollbar = self.scrollbar_rect and self.scrollbar_rect.collidepoint(mouse_pos)

            if not is_over_scrollbar:
                relative_y = mouse_pos[1] - self.rect.top
                current_hover_abs_idx = (self.scroll_y_offset + relative_y) // self.item_height

                if 0 <= current_hover_abs_idx < len(self.items_data):
                     # Check if this item is actually rendered (visible)
                     for i, ren_item in enumerate(self.rendered_items):
                         if ren_item['abs_idx'] == current_hover_abs_idx:
                             # Check y-bounds for the specific item rect on screen
                             item_on_screen_rect = pygame.Rect(self.rect.x, ren_item['screen_y'], self.rect.width - self.scrollbar_width, self.item_height)
                             if item_on_screen_rect.collidepoint(mouse_pos):
                                 self.hovered_item_idx_rel = i # Store relative index of the *rendered* item
                             break


        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                if self.scrollbar_thumb_rect and self.scrollbar_thumb_rect.collidepoint(mouse_pos):
                    self.dragging_scrollbar = True
                    self.drag_start_y = mouse_pos[1]
                    self.drag_start_scroll_y = self.scroll_y_offset
                    return None # Consumed by scrollbar

                if self.hovered_item_idx_rel is not None and self.hovered_item_idx_rel < len(self.rendered_items):
                    self.selected_index_abs = self.rendered_items[self.hovered_item_idx_rel]['abs_idx']
                    # print(f"Selected item: {self.items_data[self.selected_index_abs]['title']}")
                    return self.selected_index_abs # Return absolute index of clicked item

            # Mouse wheel scrolling
            if self.rect.collidepoint(mouse_pos): # Only scroll if mouse is over the list
                if event.button == 4:  # Scroll up
                    self.scroll_y_offset -= self.item_height
                elif event.button == 5:  # Scroll down
                    self.scroll_y_offset += self.item_height

                # Clamp scroll_y_offset
                max_scroll = max(0, (len(self.items_data) * self.item_height) - self.rect.height)
                self.scroll_y_offset = max(0, min(self.scroll_y_offset, max_scroll))
                self._render_visible_items()
                self._update_scrollbar()

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging_scrollbar = False

        if event.type == pygame.MOUSEMOTION:
            if self.dragging_scrollbar and self.scrollbar_rect:
                dy = mouse_pos[1] - self.drag_start_y
                content_height = len(self.items_data) * self.item_height
                scrollable_track_height = self.scrollbar_rect.height - self.scrollbar_thumb_rect.height

                if scrollable_track_height > 0:
                    # How much one pixel of scrollbar drag moves the content
                    scroll_ratio = (content_height - self.rect.height) / scrollable_track_height
                    self.scroll_y_offset = self.drag_start_scroll_y + (dy * scroll_ratio)

                    max_scroll = max(0, content_height - self.rect.height)
                    self.scroll_y_offset = max(0, min(self.scroll_y_offset, max_scroll))
                    self._render_visible_items()
                    self._update_scrollbar()

        return clicked_item_abs_idx # Should be None if not clicked on an item

    def draw(self, surface: pygame.Surface):
        # Main background
        pygame.draw.rect(surface, self.bg_color, self.rect)

        # Clipping area for items
        original_clip = surface.get_clip()
        surface.set_clip(self.rect)

        for i, item_info in enumerate(self.rendered_items):
            item_rect_on_screen = pygame.Rect(
                self.rect.x + 2, # Padding from left
                item_info['screen_y'],
                self.rect.width - 4 - (self.scrollbar_width if self.scrollbar_rect else 0), # Adjust for scrollbar
                self.item_height
            )

            # Draw item background (hover/selection)
            if self.hovered_item_idx_rel is not None and self.rendered_items[self.hovered_item_idx_rel]['abs_idx'] == item_info['abs_idx']:
                pygame.draw.rect(surface, self.hover_item_color, item_rect_on_screen)
            # Optional: persistent selection color if self.selected_index_abs == item_info['abs_idx']

            # Blit text surface
            text_y_centered = item_rect_on_screen.y + (self.item_height - item_info['surface'].get_height()) // 2
            surface.blit(item_info['surface'], (item_rect_on_screen.x + 5, text_y_centered)) # 5px text padding

        surface.set_clip(original_clip) # Restore clipping region

        # Draw border for the whole list
        pygame.draw.rect(surface, self.border_color, self.rect, 1)

        # Draw scrollbar
        if self.scrollbar_rect and self.scrollbar_thumb_rect:
            pygame.draw.rect(surface, self.scrollbar_color, self.scrollbar_rect)
            pygame.draw.rect(surface, self.scrollbar_thumb_color, self.scrollbar_thumb_rect)
            # Add border to thumb for better visibility
            pygame.draw.rect(surface, self.border_color, self.scrollbar_thumb_rect, 1)


    def get_selected_item_data(self):
        if self.selected_index_abs is not None and 0 <= self.selected_index_abs < len(self.items_data):
            return self.items_data[self.selected_index_abs]
        return None

    def is_mouse_over(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


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

    # ScrollableList Test
    list_items_test = [{'title': f"Item {i+1}", 'id': i} for i in range(30)]
    scroll_list = ScrollableList(50, 150, 300, 200, small_font)
    scroll_list.set_items(list_items_test)

    selected_list_item_text = "Selected: None"
    list_font = pygame.font.SysFont("Consolas", 16)


    running = True
    while running:
        dt_ms = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            input_action = text_input.handle_event(event)
            if input_action == 'enter_pressed':
                print(f"Enter pressed in text box. Text: '{text_input.get_text()}'")

            test_button.handle_event(event)
            disabled_button.handle_event(event)

            clicked_idx_test = scroll_list.handle_event(event)
            if clicked_idx_test is not None:
                selected_data_test = scroll_list.get_selected_item_data()
                if selected_data_test:
                    selected_list_item_text = f"Selected: {selected_data_test['title']} (ID: {selected_data_test['id']})"
                    print(selected_list_item_text)


        text_input.update(dt_ms)
        # scroll_list.update() # Scroll list doesn't have an update method in this design, relies on events

        screen.fill((30, 30, 30))
        text_input.draw(screen)
        test_button.draw(screen)
        disabled_button.draw(screen)
        scroll_list.draw(screen)

        # Display selected item text
        sel_text_surf = list_font.render(selected_list_item_text, True, (200,200,255))
        screen.blit(sel_text_surf, (50, 360))

        pygame.display.flip()

    pygame.quit()

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
