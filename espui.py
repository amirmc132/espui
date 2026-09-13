from machine import Pin
import time


# ============================================================
# ESPUI
# Lightweight UI Framework for ESP32 + MicroPython
# Version 2 - rebuilt from Version 1
#
# Main fixes:
# - Safe text wrapping / truncation
# - Buttons visually distinct from header
# - Long button text is handled safely
# - Consistent element spacing
# - Real sidebar focus/navigation
# - Scroll is independent from focusable widgets
# - Focused widgets are centered when possible
# - Non-focusable widgets scroll/render normally
# - Nested clip regions prevent content from escaping its area
# ============================================================


# ============================================================
# EVENTS
# ============================================================

class Event:
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    KEY_HOLD = "key_hold"
    KEY_REPEAT = "key_repeat"

    CLICK = "click"
    CHANGE = "change"

    FOCUS = "focus"
    BLUR = "blur"

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    OK = "ok"
    BACK = "back"
    MENU = "menu"

    SIDEBAR_FOCUS = "sidebar_focus"
    SIDEBAR_BLUR = "sidebar_blur"
    SIDEBAR_CHANGE = "sidebar_change"
    SIDEBAR_SELECT = "sidebar_select"


# ============================================================
# EVENT EMITTER
# ============================================================

class EventEmitter:

    def __init__(self):
        self._events = {}

    def on(self, event, callback):
        if event not in self._events:
            self._events[event] = []

        self._events[event].append(callback)
        return self

    def emit(self, event, *args):
        callbacks = self._events.get(event, [])

        for callback in callbacks:
            try:
                callback(*args)
            except Exception as e:
                print("ESPUI Event Error:", e)

        return self


# ============================================================
# DISPLAY
# ============================================================

class Display:

    def __init__(self, driver, width=128, height=64):
        self.driver = driver
        self.width = width
        self.height = height

        # Clip stack: (x, y, width, height)
        self._clips = []

    def clear(self):
        self.driver.fill(0)

    def show(self):
        self.driver.show()

    def _current_clip(self):
        if not self._clips:
            return (0, 0, self.width, self.height)

        return self._clips[-1]

    def push_clip(self, x, y, width, height):
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)

        if width <= 0 or height <= 0:
            self._clips.append((0, 0, 0, 0))
            return

        if self._clips:
            cx, cy, cw, ch = self._clips[-1]

            nx = max(x, cx)
            ny = max(y, cy)

            nr = min(x + width, cx + cw)
            nb = min(y + height, cy + ch)

            if nr <= nx or nb <= ny:
                self._clips.append((0, 0, 0, 0))
            else:
                self._clips.append(
                    (nx, ny, nr - nx, nb - ny)
                )
        else:
            nx = max(0, x)
            ny = max(0, y)
            nr = min(self.width, x + width)
            nb = min(self.height, y + height)

            if nr <= nx or nb <= ny:
                self._clips.append((0, 0, 0, 0))
            else:
                self._clips.append(
                    (nx, ny, nr - nx, nb - ny)
                )

    def pop_clip(self):
        if self._clips:
            self._clips.pop()

    def _inside(self, x, y):
        cx, cy, cw, ch = self._current_clip()

        return (
            x >= cx and
            y >= cy and
            x < cx + cw and
            y < cy + ch
        )

    def _visible_rect(self, x, y, width, height):
        if width <= 0 or height <= 0:
            return None

        cx, cy, cw, ch = self._current_clip()

        left = max(int(x), cx)
        top = max(int(y), cy)
        right = min(int(x) + int(width), cx + cw)
        bottom = min(int(y) + int(height), cy + ch)

        if right <= left or bottom <= top:
            return None

        return (
            left,
            top,
            right - left,
            bottom - top
        )

    def pixel(self, x, y, color=1):
        x = int(x)
        y = int(y)

        if self._inside(x, y):
            self.driver.pixel(x, y, color)

    def line(self, x1, y1, x2, y2, color=1):
        # Cohen-Sutherland-style clipping is unnecessary for the
        # small OLED use case. We use a safe bounding test and the
        # driver's line primitive when the segment intersects.
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        rect = self._visible_rect(
            min(x1, x2),
            min(y1, y2),
            abs(x2 - x1) + 1,
            abs(y2 - y1) + 1
        )

        if rect is None:
            return

        # For ordinary OLED primitives this is enough because
        # widgets are laid out inside their clipping viewport.
        self.driver.line(x1, y1, x2, y2, color)

    def rect(self, x, y, width, height, color=1):
        rect = self._visible_rect(x, y, width, height)

        if rect is None:
            return

        # Driver rect cannot be partially clipped by all MicroPython
        # implementations, so draw the border with clipped lines.
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)

        self.line(x, y, x + width - 1, y, color)
        self.line(
            x,
            y + height - 1,
            x + width - 1,
            y + height - 1,
            color
        )
        self.line(x, y, x, y + height - 1, color)
        self.line(
            x + width - 1,
            y,
            x + width - 1,
            y + height - 1,
            color
        )

    def fill_rect(self, x, y, width, height, color=1):
        rect = self._visible_rect(x, y, width, height)

        if rect is None:
            return

        rx, ry, rw, rh = rect
        self.driver.fill_rect(rx, ry, rw, rh, color)

    def text_width(self, text):
        # SSD1306 default font is 8 px per character.
        return len(str(text)) * 8

    def max_chars(self, width):
        if width <= 0:
            return 0

        return max(0, int(width) // 8)

    def fit_text(self, text, width, ellipsis=True):
        text = str(text)
        count = self.max_chars(width)

        if count <= 0:
            return ""

        if len(text) <= count:
            return text

        if not ellipsis:
            return text[:count]

        if count <= 3:
            return "." * count

        return text[:count - 3] + "..."

    def wrap_text(self, text, width, max_lines=None):
        text = str(text)
        count = self.max_chars(width)

        if count <= 0:
            return []

        words = text.split(" ")
        lines = []
        current = ""

        for word in words:
            # Very long single word
            while len(word) > count:
                if current:
                    lines.append(current)
                    current = ""

                lines.append(word[:count])
                word = word[count:]

                if max_lines and len(lines) >= max_lines:
                    return lines[:max_lines]

            if not word:
                continue

            if not current:
                current = word
            elif len(current) + 1 + len(word) <= count:
                current += " " + word
            else:
                lines.append(current)
                current = word

                if max_lines and len(lines) >= max_lines:
                    return lines[:max_lines]

        if current:
            lines.append(current)

        return lines[:max_lines] if max_lines else lines

    def text_clipped(
        self,
        text,
        x,
        y,
        width=None,
        height=8,
        align="left",
        ellipsis=True,
        color=1
    ):
        if width is None:
            width = self.width - int(x)

        width = max(0, int(width))
        height = max(8, int(height))

        lines = max(1, height // 8)

        if lines == 1:
            value = self.fit_text(
                text,
                width,
                ellipsis=ellipsis
            )

            tw = self.text_width(value)

            if align == "center":
                tx = int(x + (width - tw) // 2)
            elif align == "right":
                tx = int(x + width - tw)
            else:
                tx = int(x)

            if self._visible_rect(
                tx,
                y,
                max(1, tw),
                8
            ):
                # Text is already fitted to the area.
                self.driver.text(
                    value,
                    tx,
                    int(y),
                    color
                )
            return 1

        wrapped = self.wrap_text(
            text,
            width,
            max_lines=lines
        )

        for i, line in enumerate(wrapped):
            self.text_clipped(
                line,
                x,
                y + i * 8,
                width=width,
                height=8,
                align=align,
                ellipsis=False,
                color=color
            )

        return len(wrapped)

    def text(self, text, x, y, color=1):
        # Backward-compatible text(), but now safely clipped.
        value = str(text)
        x = int(x)
        y = int(y)

        clip = self._current_clip()
        cx, cy, cw, ch = clip

        if y + 8 <= cy or y >= cy + ch:
            return

        available_right = cx + cw

        if x >= available_right:
            return

        if x < cx:
            # Default SSD1306 font has fixed-width glyphs.
            skip = (cx - x + 7) // 8
            value = value[skip:]
            x += skip * 8

        available = available_right - x
        value = self.fit_text(
            value,
            available,
            ellipsis=False
        )

        if not value:
            return

        self.driver.text(value, x, y, color)

    def hline(self, y, color=1, x=0, width=None):
        if width is None:
            width = self.width

        self.line(
            x,
            y,
            x + width - 1,
            y,
            color
        )

    def vline(self, x, color=1, y=0, height=None):
        if height is None:
            height = self.height

        self.line(
            x,
            y,
            x,
            y + height - 1,
            color
        )


# ============================================================
# KEYPAD 4x4
# ============================================================

class Keypad4x4:

    DEFAULT_KEYS = [
        ["1", "2", "3", "A"],
        ["4", "5", "6", "B"],
        ["7", "8", "9", "C"],
        ["*", "0", "#", "D"]
    ]

    def __init__(
        self,
        rows,
        cols,
        keys=None,
        hold_time=700,
        repeat_time=150
    ):
        self.rows = [
            Pin(pin, Pin.OUT)
            for pin in rows
        ]

        self.cols = [
            Pin(pin, Pin.IN, Pin.PULL_DOWN)
            for pin in cols
        ]

        self.keys = keys or self.DEFAULT_KEYS

        self.hold_time = hold_time
        self.repeat_time = repeat_time

        self.last_key = None
        self.press_time = 0
        self.last_repeat = 0
        self.hold_sent = False

    def scan(self):
        detected = None

        for r, row in enumerate(self.rows):
            for rr in self.rows:
                rr.value(0)

            row.value(1)

            for c, col in enumerate(self.cols):
                if col.value():
                    detected = self.keys[r][c]
                    break

            if detected:
                break

        now = time.ticks_ms()

        if detected is None:
            if self.last_key is not None:
                key = self.last_key
                self.last_key = None
                self.hold_sent = False

                return (Event.KEY_RELEASE, key)

            return None

        if detected != self.last_key:
            self.last_key = detected
            self.press_time = now
            self.last_repeat = now
            self.hold_sent = False

            return (Event.KEY_PRESS, detected)

        elapsed = time.ticks_diff(
            now,
            self.press_time
        )

        if elapsed >= self.hold_time and not self.hold_sent:
            self.hold_sent = True

            return (Event.KEY_HOLD, detected)

        if self.hold_sent:
            if time.ticks_diff(
                now,
                self.last_repeat
            ) >= self.repeat_time:
                self.last_repeat = now

                return (Event.KEY_REPEAT, detected)

        return None


# ============================================================
# BASE WIDGET
# ============================================================

class Widget(EventEmitter):

    def __init__(self, width=None, height=12):
        super().__init__()

        self.parent = None

        self.x = 0
        self.y = 0

        self.width = width
        self.height = height

        self.visible = True
        self.enabled = True
        self.focusable = False
        self.focused = False

        self.margin = 0
        self.padding = 0

        # Extra vertical gap requested by the UI design.
        self.gap_before = 0
        self.gap_after = 0

    def set_parent(self, parent):
        self.parent = parent

    def focus(self):
        if not self.focusable:
            return

        if self.focused:
            return

        self.focused = True
        self.emit(Event.FOCUS)

    def blur(self):
        if not self.focused:
            return

        self.focused = False
        self.emit(Event.BLUR)

    def update(self):
        pass

    def handle_key(self, key):
        return False

    def draw(self, display):
        pass

    def global_y(self):
        return self.y

    def global_x(self):
        return self.x

    def is_inside(self, x, y):
        return (
            x >= self.x and
            y >= self.y and
            x < self.x + self.width and
            y < self.y + self.height
        )


# ============================================================
# CONTAINER
# ============================================================

class Container(Widget):

    def __init__(
        self,
        width=None,
        height=None,
        layout="vertical",
        spacing=3
    ):
        super().__init__(
            width=width,
            height=height or 0
        )

        self.children = []
        self.layout_type = layout
        self.spacing = spacing

        self.content_width = 0
        self.content_height = 0

    def add(self, widget):
        widget.set_parent(self)
        self.children.append(widget)
        return widget

    def remove(self, widget):
        if widget in self.children:
            self.children.remove(widget)
            widget.parent = None

    def clear(self):
        for child in self.children:
            child.parent = None

        self.children.clear()

    def layout(self):
        if not self.children:
            self.content_width = 0
            self.content_height = 0
            return

        if self.layout_type == "vertical":
            self._layout_vertical()

        elif self.layout_type == "horizontal":
            self._layout_horizontal()

        elif self.layout_type == "grid":
            self._layout_grid()

    def _layout_vertical(self):
        y = self.y + self.padding

        available_width = max(
            1,
            self.width - self.padding * 2
        )

        for child in self.children:
            if not child.visible:
                continue

            y += getattr(child, "gap_before", 0)

            child.x = self.x + self.padding
            child.y = y

            if child.width is None:
                child.width = available_width

            y += child.height
            y += getattr(child, "gap_after", 0)
            y += self.spacing

        self.content_height = max(
            0,
            y - self.y - self.spacing + self.padding
        )

        self.content_width = available_width

    def _layout_horizontal(self):
        x = self.x + self.padding

        available_height = max(
            1,
            self.height - self.padding * 2
        )

        for child in self.children:
            if not child.visible:
                continue

            x += getattr(child, "gap_before", 0)

            child.x = x
            child.y = self.y + self.padding

            if child.height is None:
                child.height = available_height

            x += child.width
            x += getattr(child, "gap_after", 0)
            x += self.spacing

        self.content_width = max(
            0,
            x - self.x - self.spacing + self.padding
        )

        self.content_height = available_height

    def _layout_grid(self):
        columns = 2

        if self.width < 80:
            columns = 1

        cell_width = max(
            1,
            (
                self.width -
                self.spacing * (columns - 1) -
                self.padding * 2
            ) // columns
        )

        x = self.x + self.padding
        y = self.y + self.padding
        column = 0
        row_height = 0

        for child in self.children:
            if not child.visible:
                continue

            child.x = x
            child.y = y
            child.width = cell_width

            row_height = max(
                row_height,
                child.height
            )

            column += 1

            if column >= columns:
                column = 0
                x = self.x + self.padding
                y += row_height + self.spacing
                row_height = 0
            else:
                x += cell_width + self.spacing

        self.content_height = (
            y -
            self.y +
            row_height +
            self.padding
        )

        self.content_width = self.width

    def update(self):
        self.layout()

        for child in self.children:
            child.update()

    def draw(self, display):
        if not self.visible:
            return

        self.layout()

        for child in self.children:
            if child.visible:
                child.draw(display)


# ============================================================
# SCROLL VIEW
# ============================================================

class ScrollView(Container):

    def __init__(
        self,
        width=None,
        height=None,
        layout="vertical",
        spacing=3
    ):
        super().__init__(
            width=width,
            height=height,
            layout=layout,
            spacing=spacing
        )

        self.scroll_y = 0
        self.scroll_x = 0

        self.content_height = 0
        self.content_width = 0

        self.scroll_speed = 12
        self.center_focus = True
        self.show_scrollbar = True

    def _layout_virtual(self):
        if self.layout_type != "vertical":
            return

        virtual_y = self.y + self.padding

        available_width = max(
            1,
            self.width - self.padding * 2
        )

        for child in self.children:

            if not child.visible:
                continue

            # Gap before
            virtual_y += getattr(
                child,
                "gap_before",
                0
            )

            # -----------------------------
            # Virtual position
            # -----------------------------

            child.virtual_x = (
                self.x + self.padding
            )

            child.virtual_y = virtual_y

            # -----------------------------
            # Real screen position
            # -----------------------------

            child.x = child.virtual_x

            child.y = (
                child.virtual_y -
                self.scroll_y
            )

            # -----------------------------
            # Width
            # -----------------------------

            if child.width is None:
                child.width = available_width

            # -----------------------------
            # Height
            # -----------------------------

            child_height = getattr(
                child,
                "height",
                None
            )

            if child_height is None:
                child_height = 8
                child.height = child_height

            child_height = max(
                1,
                int(child_height)
            )

            # -----------------------------
            # Advance virtual cursor
            # -----------------------------

            virtual_y += child_height

            virtual_y += getattr(
                child,
                "gap_after",
                0
            )

            virtual_y += self.spacing

        # -----------------------------
        # Total content size
        # -----------------------------

        self.content_height = max(
            0,
            virtual_y -
            self.y -
            self.spacing +
            self.padding
        )

        self.content_width = available_width

    def layout(self):
        if self.layout_type == "vertical":
            self._layout_virtual()
        else:
            super().layout()

    def max_scroll(self):
        return max(
            0,
            self.content_height - self.height
        )

    def scroll_to(self, value):
        value = int(value)

        value = max(
            0,
            min(self.max_scroll(), value)
        )

        self.scroll_y = value
        self._layout_virtual()

    def scroll_by(self, amount):
        self.scroll_to(
            self.scroll_y + int(amount)
        )

    def scroll_up(self):
        self.scroll_by(-self.scroll_speed)

    def scroll_down(self):
        self.scroll_by(self.scroll_speed)

    def ensure_visible(self, widget, center=None):
        """
        Scroll based on the widget's virtual position.
        This is only called by focus management; ordinary
        non-focusable widgets are never required for scrolling.
        """
        if widget not in self.children:
            return

        if center is None:
            center = self.center_focus

        virtual_top = getattr(
            widget,
            "virtual_y",
            widget.y + self.scroll_y
        )

        widget_height = widget.height

        if center:
            viewport_center = (
                self.y +
                self.height // 2
            )

            widget_center = (
                virtual_top +
                widget_height // 2
            )

            target = (
                widget_center -
                self.height // 2
            )

            # If content is smaller, do nothing.
            target = max(
                0,
                min(self.max_scroll(), target)
            )

            self.scroll_to(target)
            return

        top = self.y
        bottom = self.y + self.height

        current_top = virtual_top - self.scroll_y
        current_bottom = (
            current_top + widget_height
        )

        if current_top < top:
            self.scroll_to(
                self.scroll_y +
                current_top -
                top
            )

        elif current_bottom > bottom:
            self.scroll_to(
                self.scroll_y +
                current_bottom -
                bottom
            )

    def update(self):
        # Layout entire virtual content regardless of focus.
        self._layout_virtual()

        for child in self.children:
            child.update()

    def draw(self, display):
        if not self.visible:
            return

        self._layout_virtual()

        # The viewport itself is the only clipping region.
        display.push_clip(
            self.x,
            self.y,
            self.width,
            self.height
        )

        for child in self.children:
            if not child.visible:
                continue

            # Child screen coordinates are derived from virtual
            # coordinates, so every widget scrolls identically.
            child_height = getattr(
                child,
                "height",
                8
            )

            if (
                child.y + child_height <= self.y or
                child.y >= self.y + self.height
            ):
                continue

            child.draw(display)

        display.pop_clip()

        if self.show_scrollbar:
            self.draw_scrollbar(display)

    def draw_scrollbar(self, display):
        if self.max_scroll() <= 0:
            return

        x = self.x + self.width - 2

        # Scrollbar is clipped to the ScrollView.
        display.push_clip(
            self.x,
            self.y,
            self.width,
            self.height
        )

        display.vline(
            x,
            1,
            self.y,
            self.height
        )

        track_height = self.height

        thumb_height = max(
            5,
            int(
                track_height *
                track_height /
                max(1, self.content_height)
            )
        )

        available = max(
            0,
            track_height - thumb_height
        )

        position = int(
            available *
            self.scroll_y /
            max(1, self.max_scroll())
        )

        display.fill_rect(
            x - 1,
            self.y + position,
            2,
            thumb_height,
            1
        )

        display.pop_clip()


# ============================================================
# LABEL
# ============================================================

class Label(Widget):

    def __init__(
        self,
        text,
        height=10,
        align="left",
        text_color=1,
        
    ):
        super().__init__(
            height=height
        )

        self.text = str(text)
        self.align = align
        self.text_color = text_color

    def draw(self, display):
        display.text_clipped(
            self.text,
            self.x,
            self.y + max(0, (self.height - 8) // 2),
            width=self.width,
            height=self.height,
            align=self.align,
            ellipsis=True,
            color=self.text_color
        )


# ============================================================
# BUTTON
# ============================================================

class Button(Widget):

    def __init__(
        self,
        text,
        height=14
    ):
        super().__init__(
            height=height
        )

        self.text = str(text)
        self.focusable = True

        # Small visual separation.
        self.gap_after = 1

    def draw(self, display):
        if not self.width:
            return

        text_y = self.y + max(
            0,
            (self.height - 8) // 2
        )

        if self.focused:
            # >button<
            # White background / black text

            display.fill_rect(
                self.x,
                self.y,
                self.width,
                self.height,
                1
            )

            display.text(
                ">",
                self.x + 1,
                text_y,
                0
            )

            display.text(
                "<",
                self.x + self.width - 9,
                text_y,
                0
            )

            display.text_clipped(
                self.text,
                self.x + 10,
                self.y + 2,
                width=max(
                    1,
                    self.width - 20
                ),
                height=max(
                    8,
                    self.height - 4
                ),
                align="center",
                ellipsis=True,
                color=0
            )

        else:
            # <button>
            # Black background / white text

            display.rect(
                self.x,
                self.y,
                self.width,
                self.height,
                1
            )

            display.text(
                "<",
                self.x + 1,
                text_y,
                1
            )

            display.text_clipped(
                self.text,
                self.x + 10,
                self.y + 2,
                width=max(
                    1,
                    self.width - 12
                ),
                height=max(
                    8,
                    self.height - 4
                ),
                align="center",
                ellipsis=True,
                color=1
            )
    def handle_key(self, key):
        if key == Event.OK:
            self.emit(Event.CLICK)
            return True

        return False


# ============================================================
# TOGGLE
# ============================================================

class Toggle(Widget):

    def __init__(
        self,
        text,
        value=False
    ):
        super().__init__(
            height=14
        )

        self.text = str(text)
        self.value = bool(value)
        self.focusable = True

    def set_value(self, value):
        value = bool(value)

        if value != self.value:
            self.value = value
            self.emit(
                Event.CHANGE,
                self.value
            )

    def toggle(self):
        self.set_value(
            not self.value
        )

    def handle_key(self, key):
        if key == Event.OK:
            self.toggle()
            return True

        return False

    def draw(self, display):
        box_width = 14
        text_width = max(
            1,
            self.width - box_width - 4
        )

        display.text_clipped(
            self.text,
            self.x,
            self.y + 3,
            width=text_width,
            height=8,
            ellipsis=True
        )

        box_x = (
            self.x +
            self.width -
            box_width
        )

        if self.focused:
            display.rect(
                box_x - 1,
                self.y,
                box_width + 2,
                13
            )

        display.rect(
            box_x,
            self.y + 1,
            box_width,
            11
        )

        if self.value:
            display.fill_rect(
                box_x + 3,
                self.y + 4,
                8,
                5
            )


# ============================================================
# CHECKBOX
# ============================================================

class Checkbox(Toggle):

    def draw(self, display):
        box_width = 11

        text_width = max(
            1,
            self.width - box_width - 4
        )

        display.text_clipped(
            self.text,
            self.x,
            self.y + 2,
            width=text_width,
            height=10,
            ellipsis=True
        )

        box_x = (
            self.x +
            self.width -
            box_width
        )

        if self.focused:
            display.rect(
                box_x - 1,
                self.y,
                box_width + 2,
                12
            )

        display.rect(
            box_x,
            self.y + 1,
            10,
            10
        )

        if self.value:
            display.line(
                box_x + 2,
                self.y + 5,
                box_x + 4,
                self.y + 8
            )

            display.line(
                box_x + 4,
                self.y + 8,
                box_x + 8,
                self.y + 3
            )


# ============================================================
# SLIDER
# ============================================================

class Slider(Widget):

    def __init__(
        self,
        text,
        value=50,
        minimum=0,
        maximum=100
    ):
        super().__init__(
            height=20
        )

        self.text = str(text)
        self.value = value
        self.minimum = minimum
        self.maximum = maximum

        self.focusable = True

    def set_value(self, value):
        value = max(
            self.minimum,
            min(self.maximum, value)
        )

        if value != self.value:
            self.value = value
            self.emit(
                Event.CHANGE,
                self.value
            )

    def handle_key(self, key):
        if key == Event.LEFT:
            self.set_value(
                self.value - 1
            )
            return True

        if key == Event.RIGHT:
            self.set_value(
                self.value + 1
            )
            return True

        if key == Event.OK:
            return True

        return False

    def draw(self, display):
        display.text_clipped(
            "{}: {}".format(
                self.text,
                self.value
            ),
            self.x,
            self.y,
            width=self.width,
            height=8,
            ellipsis=True
        )

        bar_y = self.y + 11

        display.rect(
            self.x,
            bar_y,
            self.width,
            5
        )

        if self.maximum == self.minimum:
            return

        value_width = int(
            (
                self.value -
                self.minimum
            ) /
            (
                self.maximum -
                self.minimum
            ) *
            max(0, self.width - 2)
        )

        if value_width > 0:
            display.fill_rect(
                self.x + 1,
                bar_y + 1,
                value_width,
                3
            )


# ============================================================
# PROGRESS BAR
# ============================================================

class ProgressBar(Widget):

    def __init__(self, value=0):
        super().__init__(
            height=9
        )

        self.value = value

    def set_value(self, value):
        self.value = max(
            0,
            min(100, value)
        )

    def draw(self, display):
        display.rect(
            self.x,
            self.y,
            self.width,
            8
        )

        inner = int(
            max(0, self.width - 2) *
            self.value /
            100
        )

        if inner > 0:
            display.fill_rect(
                self.x + 1,
                self.y + 1,
                inner,
                6
            )


# ============================================================
# SEPARATOR
# ============================================================

class Separator(Widget):

    def __init__(self, height=5):
        super().__init__(
            height=height
        )

    def draw(self, display):
        y = self.y + self.height // 2

        display.hline(
            y,
            1,
            self.x,
            self.width
        )


# ============================================================
# DIALOG
# ============================================================

class Dialog(EventEmitter):

    def __init__(self, title, message):
        super().__init__()

        self.title = str(title)
        self.message = str(message)

        self.visible = True

    def close(self):
        self.visible = False

    def draw(self, display):
        if not self.visible:
            return

        width = min(
            display.width - 12,
            116
        )

        height = 40

        x = (
            display.width -
            width
        ) // 2

        y = (
            display.height -
            height
        ) // 2

        display.fill_rect(
            x,
            y,
            width,
            height,
            0
        )

        display.rect(
            x,
            y,
            width,
            height,
            1
        )

        display.text_clipped(
            self.title,
            x + 4,
            y + 3,
            width - 8,
            8
        )

        display.text_clipped(
            self.message,
            x + 4,
            y + 14,
            width - 8,
            height - 18
        )


# ============================================================
# SCREEN
# ============================================================

class Screen(EventEmitter):

    def __init__(
        self,
        title="",
        width=128,
        height=64
    ):
        super().__init__()

        self.title = str(title)

        self.width = width
        self.height = height

        self.header_enabled = True
        self.footer_enabled = True
        self.sidebar_enabled = False

        self.header_height = 11
        self.footer_height = 10
        self.sidebar_width = 38

        self.header_text = self.title
        self.footer_text = "2/8 Move   A OK"

        self.content = None

        self.sidebar_items = []
        self.sidebar_index = 0
        self.sidebar_focus = False
        self.sidebar_scroll = 0

        self.focusables = []
        self.focus_index = -1

        self.dialog = None

        self.notification = None
        self.notification_until = 0

        self._ui = None

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    def header(self, title=None):
        self.header_enabled = True

        if title is not None:
            self.header_text = str(title)

        return self

    def hide_header(self):
        self.header_enabled = False
        return self

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    def footer(self, text):
        self.footer_enabled = True
        self.footer_text = str(text)
        return self

    def hide_footer(self):
        self.footer_enabled = False
        return self

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    def sidebar(self, items):
        """
        Items can be:
            "Home"
            ("Home", callback)
            ("Settings", another_screen)
            {"label": "Home", "target": screen}

        A plain string is selectable and emits SIDEBAR_SELECT.
        """
        self.sidebar_enabled = True
        self.sidebar_items = []

        for item in items:
            normalized = {
                "label": "",
                "target": None
            }

            if isinstance(item, str):
                normalized["label"] = item

            elif isinstance(item, (tuple, list)):
                if len(item) >= 1:
                    normalized["label"] = str(item[0])

                if len(item) >= 2:
                    normalized["target"] = item[1]

            elif isinstance(item, dict):
                normalized["label"] = str(
                    item.get(
                        "label",
                        item.get("title", "")
                    )
                )

                normalized["target"] = item.get(
                    "target",
                    item.get("callback")
                )

            else:
                normalized["label"] = str(item)

            self.sidebar_items.append(normalized)

        self.sidebar_index = max(
            0,
            min(
                self.sidebar_index,
                max(0, len(self.sidebar_items) - 1)
            )
        )

        self._update_sidebar_scroll()

        return self

    def hide_sidebar(self):
        self.sidebar_enabled = False
        self.sidebar_focus = False
        return self

    def focus_sidebar(self):
        if not self.sidebar_enabled:
            return False

        if not self.sidebar_items:
            return False

        if not self.sidebar_focus:
            self.sidebar_focus = True
            self._blur_content()
            self.emit(Event.SIDEBAR_FOCUS)

        self._update_sidebar_scroll()

        return True

    def blur_sidebar(self):
        if not self.sidebar_focus:
            return

        self.sidebar_focus = False
        self.emit(Event.SIDEBAR_BLUR)

    def _update_sidebar_scroll(self):
        if not self.sidebar_items:
            self.sidebar_scroll = 0
            return

        top = (
            self.header_height
            if self.header_enabled
            else 0
        )

        bottom = (
            self.height -
            self.footer_height
            if self.footer_enabled
            else self.height
        )

        item_height = 12
        visible = max(
            1,
            (bottom - top - 2) // item_height
        )

        if self.sidebar_index < self.sidebar_scroll:
            self.sidebar_scroll = self.sidebar_index

        if self.sidebar_index >= (
            self.sidebar_scroll + visible
        ):
            self.sidebar_scroll = (
                self.sidebar_index -
                visible +
                1
            )

        max_start = max(
            0,
            len(self.sidebar_items) - visible
        )

        self.sidebar_scroll = max(
            0,
            min(
                self.sidebar_scroll,
                max_start
            )
        )

    def sidebar_up(self):
        if not self.sidebar_items:
            return

        if self.sidebar_index > 0:
            self.sidebar_index -= 1

        self._update_sidebar_scroll()

        self.emit(
            Event.SIDEBAR_CHANGE,
            self.sidebar_index,
            self.sidebar_items[
                self.sidebar_index
            ]
        )

    def sidebar_down(self):
        if not self.sidebar_items:
            return

        if self.sidebar_index < (
            len(self.sidebar_items) - 1
        ):
            self.sidebar_index += 1

        self._update_sidebar_scroll()

        self.emit(
            Event.SIDEBAR_CHANGE,
            self.sidebar_index,
            self.sidebar_items[
                self.sidebar_index
            ]
        )

    def sidebar_select(self):
        if not self.sidebar_items:
            return False

        item = self.sidebar_items[
            self.sidebar_index
        ]

        self.emit(
            Event.SIDEBAR_SELECT,
            self.sidebar_index,
            item
        )

        target = item.get("target")

        if target is not None and self._ui:
            if isinstance(target, Screen):
                self._ui.show(target)
            elif callable(target):
                target(
                    self,
                    self.sidebar_index
                )

        return True

    # --------------------------------------------------------
    # CONTENT
    # --------------------------------------------------------

    def set_content(self, content):
        self.content = content
        return content

    def add(self, widget):
        if self.content is None:
            self.content = ScrollView(
                layout="vertical",
                spacing=3
            )

        return self.content.add(widget)

    # --------------------------------------------------------
    # FOCUS TREE
    # --------------------------------------------------------

    def collect_focusables(self):
        self.focusables = []

        def scan(container):
            if not hasattr(
                container,
                "children"
            ):
                return

            for child in container.children:
                if (
                    child.focusable and
                    child.enabled and
                    child.visible
                ):
                    self.focusables.append(child)

                if hasattr(
                    child,
                    "children"
                ):
                    scan(child)

        if self.content:
            scan(self.content)

    def _blur_content(self):
        for widget in self.focusables:
            widget.blur()

    def set_initial_focus(self):
        self.collect_focusables()

        if not self.focusables:
            self.focus_index = -1
            return

        self.focus_index = 0
        self.update_focus()

    def update_focus(self):
        self.collect_focusables()

        self._blur_content()

        if not self.focusables:
            self.focus_index = -1
            return

        self.focus_index = max(
            0,
            min(
                self.focus_index,
                len(self.focusables) - 1
            )
        )

        current = self.focusables[
            self.focus_index
        ]

        current.focus()

        # Focus changes are allowed to request scrolling,
        # but ScrollView itself does NOT depend on focus.
        parent = current.parent

        while parent:
            if isinstance(parent, ScrollView):
                parent.ensure_visible(
                    current,
                    center=True
                )

            parent = parent.parent

    def focus_next(self):
        if not self.focusables:
            return

        self.focus_index += 1

        if self.focus_index >= len(
            self.focusables
        ):
            self.focus_index = 0

        self.update_focus()

    def focus_previous(self):
        if not self.focusables:
            return

        self.focus_index -= 1

        if self.focus_index < 0:
            self.focus_index = (
                len(self.focusables) - 1
            )

        self.update_focus()

    # --------------------------------------------------------
    # KEY
    # --------------------------------------------------------

    def handle_key(self, key):
        # Sidebar mode
        if self.sidebar_focus and self.sidebar_enabled:
            if key == Event.UP:
                self.sidebar_up()
                return True

            if key == Event.DOWN:
                self.sidebar_down()
                return True

            if key == Event.RIGHT:
                self.blur_sidebar()
                self.set_initial_focus()
                return True

            if key == Event.OK:
                return self.sidebar_select()

            if key == Event.LEFT:
                return True

            return False

        # Content mode
        if key == Event.LEFT and self.sidebar_enabled:
            return self.focus_sidebar()

        if key == Event.UP:
            self.focus_previous()
            return True

        if key == Event.DOWN:
            self.focus_next()
            return True

        if (
            self.focus_index >= 0 and
            self.focus_index < len(self.focusables)
        ):
            widget = self.focusables[
                self.focus_index
            ]

            if widget.handle_key(key):
                return True

        return False

    # --------------------------------------------------------
    # LAYOUT
    # --------------------------------------------------------

    def layout(self):
        if not self.content:
            return

        top = (
            self.header_height
            if self.header_enabled
            else 0
        )

        bottom = (
            self.footer_height
            if self.footer_enabled
            else 0
        )

        left = (
            self.sidebar_width
            if self.sidebar_enabled
            else 0
        )

        content_width = max(
            1,
            self.width - left
        )

        content_height = max(
            1,
            self.height - top - bottom
        )

        self.content.x = left
        self.content.y = top
        self.content.width = content_width
        self.content.height = content_height

        self.content.update()

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------

    def draw(self, display):
        display.clear()

        self.layout()

        self.draw_header(display)
        self.draw_sidebar(display)

        if self.content:
            # Content can NEVER draw into header/footer.
            content_top = (
                self.header_height
                if self.header_enabled
                else 0
            )

            content_bottom = (
                self.height -
                self.footer_height
                if self.footer_enabled
                else self.height
            )

            content_left = (
                self.sidebar_width
                if self.sidebar_enabled
                else 0
            )

            display.push_clip(
                content_left,
                content_top,
                self.width - content_left,
                content_bottom - content_top
            )

            self.content.draw(display)

            display.pop_clip()

        self.draw_footer(display)
        self.draw_notification(display)

        if self.dialog:
            self.dialog.draw(display)

        display.show()

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    def draw_header(self, display):
        if not self.header_enabled:
            return

        # Header is deliberately different from buttons:
        # solid bar + title only.
        display.fill_rect(
            0,
            0,
            self.width,
            self.header_height,
            1
        )

        display.text_clipped(
            self.header_text,
            3,
            1,
            self.width - 6,
            8,
            align="left",
            color=0
        )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    def draw_footer(self, display):
        if not self.footer_enabled:
            return

        y = (
            self.height -
            self.footer_height
        )

        display.fill_rect(
            0,
            y,
            self.width,
            self.footer_height,
            0
        )

        display.hline(
            y,
            1,
            0,
            self.width
        )

        display.text_clipped(
            self.footer_text,
            2,
            y + 1,
            self.width - 4,
            8
        )

    # --------------------------------------------------------
    # SIDEBAR DRAW
    # --------------------------------------------------------

    def draw_sidebar(self, display):
        if not self.sidebar_enabled:
            return

        display.fill_rect(
            0,
            0,
            self.sidebar_width,
            self.height,
            0
        )

        display.vline(
            self.sidebar_width - 1,
            1,
            0,
            self.height
        )

        top = (
            self.header_height
            if self.header_enabled
            else 0
        )

        bottom = (
            self.height -
            self.footer_height
            if self.footer_enabled
            else self.height
        )

        item_height = 12
        y = top + 1

        visible = max(
            1,
            (bottom - top - 2) // item_height
        )

        start = self.sidebar_scroll
        end = min(
            len(self.sidebar_items),
            start + visible
        )

        for index in range(start, end):
            item = self.sidebar_items[index]
            label = item.get("label", "")

            selected = (
                index == self.sidebar_index
            )

            if selected:
                if self.sidebar_focus:
                    display.fill_rect(
                        1,
                        y,
                        self.sidebar_width - 3,
                        11,
                        1
                    )

                    display.text_clipped(
                        "< " + label,
                        3,
                        y + 1,
                        self.sidebar_width - 7,
                        8
                    )
                else:
                    display.rect(
                        1,
                        y,
                        self.sidebar_width - 3,
                        11,
                        1
                    )

                    display.text_clipped(
                        label,
                        3,
                        y + 1,
                        self.sidebar_width - 7,
                        8
                    )
            else:
                display.text_clipped(
                    label,
                    3,
                    y + 1,
                    self.sidebar_width - 7,
                    8
                )

            y += item_height

    # --------------------------------------------------------
    # NOTIFICATION
    # --------------------------------------------------------

    def notify(self, text, duration=1500):
        self.notification = str(text)

        self.notification_until = (
            time.ticks_ms() +
            duration
        )

    def draw_notification(self, display):
        if not self.notification:
            return

        if time.ticks_diff(
            self.notification_until,
            time.ticks_ms()
        ) <= 0:
            self.notification = None
            return

        text = self.notification

        width = min(
            display.width - 8,
            max(16, len(text) * 8 + 8)
        )

        x = (
            display.width -
            width
        ) // 2

        y = (
            display.height -
            16
        ) // 2

        display.fill_rect(
            x,
            y,
            width,
            15,
            1
        )

        display.text_clipped(
            text,
            x + 4,
            y + 3,
            width - 8,
            8
        )

    # --------------------------------------------------------
    # DIALOG
    # --------------------------------------------------------

    def show_dialog(self, title, message):
        self.dialog = Dialog(
            title,
            message
        )

    def close_dialog(self):
        self.dialog = None


# ============================================================
# UI CORE
# ============================================================

class UI:

    def __init__(self, fps=20):
        self.display = None
        self.controller = None

        self.screens = []
        self.current_screen = None

        self.running = False
        self.fps = fps

        self.events = EventEmitter()

    # --------------------------------------------------------
    # HARDWARE
    # --------------------------------------------------------

    def begin(self, display, controller):
        self.display = display
        self.controller = controller
        return self

    # --------------------------------------------------------
    # SCREEN
    # --------------------------------------------------------

    def show(self, screen):
        self.current_screen = screen
        screen._ui = self

        screen.layout()
        screen.set_initial_focus()

        self.render()

        return screen

    def push(self, screen):
        if self.current_screen:
            self.screens.append(
                self.current_screen
            )

        return self.show(screen)

    def pop(self):
        if not self.screens:
            return

        screen = self.screens.pop()

        self.show(screen)

    def back(self):
        self.pop()

    # --------------------------------------------------------
    # INPUT
    # --------------------------------------------------------

    def read_input(self):
        if not self.controller:
            return

        result = self.controller.scan()

        if not result:
            return

        event_type, key = result

        self.events.emit(
            event_type,
            key
        )

        if event_type not in (
            Event.KEY_PRESS,
            Event.KEY_REPEAT
        ):
            return

        self.handle_key(key)

    # --------------------------------------------------------
    # KEY MAPPING
    # --------------------------------------------------------

    def map_key(self, key):
        mapping = {
            "2": Event.UP,
            "8": Event.DOWN,

            "4": Event.LEFT,
            "6": Event.RIGHT,

            "A": Event.OK,
            "#": Event.OK,

            "B": Event.BACK,
            "*": Event.BACK,

            "C": Event.MENU
        }

        return mapping.get(
            key,
            key
        )

    # --------------------------------------------------------
    # HANDLE KEY
    # --------------------------------------------------------

    def handle_key(self, key):
        key = self.map_key(key)

        self.events.emit(
            "ui_key",
            key
        )

        if not self.current_screen:
            return

        # Dialog has priority.
        if (
            self.current_screen.dialog and
            self.current_screen.dialog.visible
        ):
            if key == Event.BACK:
                self.current_screen.close_dialog()
                self.render()
                return

            if key == Event.OK:
                self.current_screen.close_dialog()
                self.render()
                return

            return

        if key == Event.BACK:
            self.events.emit(Event.BACK)
            self.back()
            return

        if key == Event.MENU:
            self.events.emit(Event.MENU)
            return

        # All navigation keys go through Screen.
        # This is essential for Sidebar focus.
        self.current_screen.handle_key(key)

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    def update(self):
        self.read_input()

        if not self.current_screen:
            return

        self.current_screen.layout()

    # --------------------------------------------------------
    # RENDER
    # --------------------------------------------------------

    def render(self):
        if (
            self.display and
            self.current_screen
        ):
            self.current_screen.draw(
                self.display
            )

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    def run(self):
        self.running = True

        frame_ms = max(
            1,
            int(1000 / self.fps)
        )

        while self.running:
            start = time.ticks_ms()

            self.update()
            self.render()

            elapsed = time.ticks_diff(
                time.ticks_ms(),
                start
            )

            delay = (
                frame_ms -
                elapsed
            )

            if delay > 0:
                time.sleep_ms(delay)

    def stop(self):
        self.running = False

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    def on(self, event, callback):
        self.events.on(
            event,
            callback
        )

        return self


# ============================================================
# OPTIONAL HELPERS
# ============================================================

def vertical(
    width=None,
    height=None,
    spacing=3
):
    return Container(
        width=width,
        height=height,
        layout="vertical",
        spacing=spacing
    )


def horizontal(
    width=None,
    height=None,
    spacing=3
):
    return Container(
        width=width,
        height=height,
        layout="horizontal",
        spacing=spacing
    )


def scroll(
    width=None,
    height=None,
    spacing=3
):
    return ScrollView(
        width=width,
        height=height,
        layout="vertical",
        spacing=spacing
    )
