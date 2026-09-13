from machine import Pin
import time


# ============================================================
# ESPUI
# Lightweight UI Framework for ESP32 + MicroPython
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

    def __init__(
        self,
        driver,
        width=128,
        height=64
    ):

        self.driver = driver

        self.width = width
        self.height = height

    def clear(self):

        self.driver.fill(0)

    def show(self):

        self.driver.show()

    def pixel(self, x, y, color=1):

        self.driver.pixel(
            int(x),
            int(y),
            color
        )

    def line(
        self,
        x1,
        y1,
        x2,
        y2,
        color=1
    ):

        self.driver.line(
            int(x1),
            int(y1),
            int(x2),
            int(y2),
            color
        )

    def rect(
        self,
        x,
        y,
        width,
        height,
        color=1
    ):

        self.driver.rect(
            int(x),
            int(y),
            int(width),
            int(height),
            color
        )

    def fill_rect(
        self,
        x,
        y,
        width,
        height,
        color=1
    ):

        self.driver.fill_rect(
            int(x),
            int(y),
            int(width),
            int(height),
            color
        )

    def text(
        self,
        text,
        x,
        y,
        color=1
    ):

        self.driver.text(
            str(text),
            int(x),
            int(y),
            color
        )

    def hline(
        self,
        y,
        color=1
    ):

        self.line(
            0,
            y,
            self.width - 1,
            y,
            color
        )

    def vline(
        self,
        x,
        color=1
    ):

        self.line(
            x,
            0,
            x,
            self.height - 1,
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
            Pin(
                pin,
                Pin.IN,
                Pin.PULL_DOWN
            )
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

        # ------------------------------------
        # No key
        # ------------------------------------

        if detected is None:

            if self.last_key is not None:

                key = self.last_key

                self.last_key = None

                self.hold_sent = False

                return (
                    Event.KEY_RELEASE,
                    key
                )

            return None

        # ------------------------------------
        # New key
        # ------------------------------------

        if detected != self.last_key:

            self.last_key = detected

            self.press_time = now

            self.last_repeat = now

            self.hold_sent = False

            return (
                Event.KEY_PRESS,
                detected
            )

        # ------------------------------------
        # Hold
        # ------------------------------------

        elapsed = time.ticks_diff(
            now,
            self.press_time
        )

        if (
            elapsed >= self.hold_time
            and not self.hold_sent
        ):

            self.hold_sent = True

            return (
                Event.KEY_HOLD,
                detected
            )

        # ------------------------------------
        # Repeat
        # ------------------------------------

        if self.hold_sent:

            if time.ticks_diff(
                now,
                self.last_repeat
            ) >= self.repeat_time:

                self.last_repeat = now

                return (
                    Event.KEY_REPEAT,
                    detected
                )

        return None


# ============================================================
# BASE WIDGET
# ============================================================

class Widget(EventEmitter):

    def __init__(
        self,
        width=None,
        height=12
    ):

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


# ============================================================
# CONTAINER
# ============================================================

class Container(Widget):

    def __init__(
        self,
        width=None,
        height=None,
        layout="vertical",
        spacing=2
    ):

        super().__init__(
            width=width,
            height=height or 0
        )

        self.children = []

        self.layout_type = layout

        self.spacing = spacing

    def add(self, widget):

        widget.set_parent(self)

        self.children.append(widget)

        return widget

    def remove(self, widget):

        if widget in self.children:

            self.children.remove(widget)

            widget.parent = None

    def clear(self):

        self.children.clear()

    def layout(self):

        if not self.children:
            return

        if self.layout_type == "vertical":

            self._layout_vertical()

        elif self.layout_type == "horizontal":

            self._layout_horizontal()

        elif self.layout_type == "grid":

            self._layout_grid()

    def _layout_vertical(self):

        y = self.y + self.padding

        available_width = (
            self.width -
            self.padding * 2
        )

        for child in self.children:

            if not child.visible:
                continue

            child.x = self.x + self.padding

            child.y = y

            if child.width is None:
                child.width = available_width

            y += (
                child.height +
                self.spacing
            )

        self.content_height = (
            y -
            self.y +
            self.padding
        )

    def _layout_horizontal(self):

        x = self.x + self.padding

        for child in self.children:

            if not child.visible:
                continue

            child.x = x

            child.y = (
                self.y +
                self.padding
            )

            if child.height is None:
                child.height = self.height

            x += (
                child.width +
                self.spacing
            )

        self.content_width = (
            x -
            self.x +
            self.padding
        )

    def _layout_grid(self):

        columns = 2

        if self.width >= 100:
            columns = 2

        cell_width = (
            self.width -
            self.spacing * (columns - 1)
        ) // columns

        x = self.x
        y = self.y

        column = 0

        for child in self.children:

            child.x = x
            child.y = y

            child.width = cell_width

            column += 1

            if column >= columns:

                column = 0

                x = self.x

                y += (
                    child.height +
                    self.spacing
                )

            else:

                x += (
                    cell_width +
                    self.spacing
                )

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
        spacing=2
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

    def layout(self):

        # Layout in virtual coordinates

        virtual_y = self.y - self.scroll_y

        if self.layout_type == "vertical":

            for child in self.children:

                child.x = (
                    self.x +
                    self.padding
                )

                child.y = virtual_y

                if child.width is None:

                    child.width = (
                        self.width -
                        self.padding * 2
                    )

                virtual_y += (
                    child.height +
                    self.spacing
                )

            self.content_height = (
                virtual_y -
                self.y +
                self.scroll_y
            )

    def max_scroll(self):

        if self.content_height <= self.height:
            return 0

        return (
            self.content_height -
            self.height
        )

    def scroll_to(self, value):

        value = max(
            0,
            min(
                self.max_scroll(),
                value
            )
        )

        self.scroll_y = value

    def scroll_by(self, amount):

        self.scroll_to(
            self.scroll_y + amount
        )

    def scroll_up(self):

        self.scroll_by(
            -self.scroll_speed
        )

    def scroll_down(self):

        self.scroll_by(
            self.scroll_speed
        )

    def ensure_visible(self, widget):

        if widget not in self.children:
            return

        top = self.y
        bottom = (
            self.y +
            self.height
        )

        if widget.y < top:

            self.scroll_by(
                widget.y - top
            )

        elif (
            widget.y +
            widget.height
            >
            bottom
        ):

            self.scroll_by(
                widget.y +
                widget.height -
                bottom
            )

    def draw(self, display):

        if not self.visible:
            return

        self.layout()

        # Clip manually by checking children

        for child in self.children:

            if not child.visible:
                continue

            if (
                child.y +
                child.height <
                self.y
            ):
                continue

            if child.y > (
                self.y +
                self.height
            ):
                continue

            child.draw(display)

        self.draw_scrollbar(display)

    def draw_scrollbar(self, display):

        if self.max_scroll() <= 0:
            return

        x = (
            self.x +
            self.width -
            2
        )

        display.vline(x)

        track_height = self.height

        thumb_height = max(
            5,
            int(
                track_height *
                track_height /
                self.content_height
            )
        )

        available = (
            track_height -
            thumb_height
        )

        position = int(
            available *
            self.scroll_y /
            self.max_scroll()
        )

        display.fill_rect(
            x - 1,
            self.y + position,
            2,
            thumb_height,
            1
        )


# ============================================================
# LABEL
# ============================================================

class Label(Widget):

    def __init__(self, text):

        super().__init__(
            height=10
        )

        self.text = str(text)

    def draw(self, display):

        display.text(
            self.text,
            self.x,
            self.y
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

    def draw(self, display):

        if self.focused:

            display.fill_rect(
                self.x,
                self.y,
                self.width,
                self.height,
                1
            )

            display.text(
                self.text,
                self.x + 3,
                self.y + 3,
                0
            )

        else:

            display.rect(
                self.x,
                self.y,
                self.width,
                self.height,
                1
            )

            display.text(
                self.text,
                self.x + 3,
                self.y + 3
            )

    def handle_key(self, key):

        if key == "OK":

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

        self.value = value

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

        if key == "OK":

            self.toggle()

            return True

        return False

    def draw(self, display):

        display.text(
            self.text,
            self.x,
            self.y + 3
        )

        box_x = (
            self.x +
            self.width -
            16
        )

        display.rect(
            box_x,
            self.y + 1,
            14,
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

        display.text(
            self.text,
            self.x,
            self.y + 2
        )

        box_x = (
            self.x +
            self.width -
            11
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
            min(
                self.maximum,
                value
            )
        )

        if value != self.value:

            self.value = value

            self.emit(
                Event.CHANGE,
                self.value
            )

    def handle_key(self, key):

        if key == "LEFT":

            self.set_value(
                self.value - 1
            )

            return True

        if key == "RIGHT":

            self.set_value(
                self.value + 1
            )

            return True

        if key == "OK":

            return True

        return False

    def draw(self, display):

        display.text(
            "{}: {}".format(
                self.text,
                self.value
            ),
            self.x,
            self.y
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
            (
                self.width - 2
            )
        )

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

    def __init__(
        self,
        value=0
    ):

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
            (
                self.width - 2
            ) *
            self.value /
            100
        )

        display.fill_rect(
            self.x + 1,
            self.y + 1,
            inner,
            6
        )


# ============================================================
# DIALOG
# ============================================================

class Dialog(EventEmitter):

    def __init__(
        self,
        title,
        message
    ):

        super().__init__()

        self.title = title
        self.message = message

        self.visible = True

    def close(self):

        self.visible = False

    def draw(
        self,
        display
    ):

        if not self.visible:
            return

        width = min(
            display.width - 12,
            116
        )

        height = 36

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

        display.text(
            self.title,
            x + 4,
            y + 3
        )

        display.text(
            self.message,
            x + 4,
            y + 16
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

        self.title = title

        self.width = width
        self.height = height

        self.header_enabled = True
        self.footer_enabled = True
        self.sidebar_enabled = False

        self.header_height = 11
        self.footer_height = 10
        self.sidebar_width = 34

        self.header_text = title
        self.footer_text = "2/8 Move   A Select"

        self.content = None

        self.sidebar_items = []
        self.sidebar_index = 0

        self.focusables = []
        self.focus_index = -1

        self.dialog = None

        self.notification = None
        self.notification_until = 0

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    def header(
        self,
        title=None
    ):

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

    def footer(
        self,
        text
    ):

        self.footer_enabled = True

        self.footer_text = str(text)

        return self

    def hide_footer(self):

        self.footer_enabled = False

        return self

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    def sidebar(
        self,
        items
    ):

        self.sidebar_enabled = True

        self.sidebar_items = list(items)

        return self

    def hide_sidebar(self):

        self.sidebar_enabled = False

        return self

    # --------------------------------------------------------
    # CONTENT
    # --------------------------------------------------------

    def set_content(
        self,
        content
    ):

        self.content = content

        return content

    def add(
        self,
        widget
    ):

        if self.content is None:

            self.content = Container(
                layout="vertical"
            )

        return self.content.add(widget)

    # --------------------------------------------------------
    # FOCUS TREE
    # --------------------------------------------------------

    def collect_focusables(
        self
    ):

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

                    self.focusables.append(
                        child
                    )

                if hasattr(
                    child,
                    "children"
                ):

                    scan(child)

        if self.content:

            scan(self.content)

    def set_initial_focus(self):

        self.collect_focusables()

        if not self.focusables:

            self.focus_index = -1

            return

        self.focus_index = 0

        self.update_focus()

    def update_focus(self):

        for widget in self.focusables:

            widget.blur()

        if self.focus_index < 0:
            return

        if self.focus_index >= len(
            self.focusables
        ):
            return

        current = self.focusables[
            self.focus_index
        ]

        current.focus()

        # Scroll parent into view

        parent = current.parent

        while parent:

            if isinstance(
                parent,
                ScrollView
            ):

                parent.ensure_visible(
                    current
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

    def handle_key(
        self,
        key
    ):

        # Navigation

        if key == "UP":

            self.focus_previous()

            return True

        if key == "DOWN":

            self.focus_next()

            return True

        # Current widget

        if (
            self.focus_index >= 0
            and self.focus_index <
            len(self.focusables)
        ):

            widget = self.focusables[
                self.focus_index
            ]

            if widget.handle_key(
                key
            ):

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

        content_width = (
            self.width -
            left
        )

        content_height = (
            self.height -
            top -
            bottom
        )

        self.content.x = left
        self.content.y = top

        self.content.width = content_width
        self.content.height = content_height

        self.content.update()

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------

    def draw(
        self,
        display
    ):

        display.clear()

        self.layout()

        self.draw_header(display)

        self.draw_sidebar(display)

        if self.content:

            self.content.draw(
                display
            )

        self.draw_footer(display)

        self.draw_notification(
            display
        )

        if self.dialog:

            self.dialog.draw(
                display
            )

        display.show()

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    def draw_header(
        self,
        display
    ):

        if not self.header_enabled:
            return

        display.fill_rect(
            0,
            0,
            self.width,
            self.header_height,
            1
        )

        display.text(
            self.header_text,
            3,
            1,
            0
        )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    def draw_footer(
        self,
        display
    ):

        if not self.footer_enabled:
            return

        y = (
            self.height -
            self.footer_height
        )

        display.hline(y)

        display.text(
            self.footer_text,
            2,
            y + 1
        )

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    def draw_sidebar(
        self,
        display
    ):

        if not self.sidebar_enabled:
            return

        display.vline(
            self.sidebar_width
        )

        y = self.header_height + 2

        for index, item in enumerate(
            self.sidebar_items
        ):

            if y + 11 > self.height:
                break

            if index == self.sidebar_index:

                display.fill_rect(
                    1,
                    y,
                    self.sidebar_width - 3,
                    11,
                    1
                )

                display.text(
                    str(item),
                    3,
                    y + 1,
                    0
                )

            else:

                display.text(
                    str(item),
                    3,
                    y + 1
                )

            y += 12

    # --------------------------------------------------------
    # NOTIFICATION
    # --------------------------------------------------------

    def notify(
        self,
        text,
        duration=1500
    ):

        self.notification = str(text)

        self.notification_until = (
            time.ticks_ms() +
            duration
        )

    def draw_notification(
        self,
        display
    ):

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
            len(text) * 8 + 8
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

        display.text(
            text,
            x + 4,
            y + 3,
            0
        )

    # --------------------------------------------------------
    # DIALOG
    # --------------------------------------------------------

    def show_dialog(
        self,
        title,
        message
    ):

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

    def __init__(
        self,
        fps=20
    ):

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

    def begin(
        self,
        display,
        controller
    ):

        self.display = display

        self.controller = controller

        return self

    # --------------------------------------------------------
    # SCREEN
    # --------------------------------------------------------

    def show(
        self,
        screen
    ):

        self.current_screen = screen

        screen.set_initial_focus()

        self.render()

        return screen

    def push(
        self,
        screen
    ):

        if self.current_screen:

            self.screens.append(
                self.current_screen
            )

        return self.show(
            screen
        )

    def pop(self):

        if not self.screens:

            return

        screen = self.screens.pop()

        self.show(
            screen
        )

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

        # Only react to press/repeat
        if event_type not in (
            Event.KEY_PRESS,
            Event.KEY_REPEAT
        ):

            return

        self.handle_key(
            key
        )

    # --------------------------------------------------------
    # KEY MAPPING
    # --------------------------------------------------------

    def map_key(
        self,
        key
    ):

        # Default 4x4 keypad mapping

        mapping = {

            "2": "UP",
            "8": "DOWN",

            "4": "LEFT",
            "6": "RIGHT",

            "A": "OK",
            "#": "OK",

            "B": "BACK",
            "*": "BACK",

            "C": "MENU"

        }

        return mapping.get(
            key,
            key
        )

    # --------------------------------------------------------
    # HANDLE KEY
    # --------------------------------------------------------

    def handle_key(
        self,
        key
    ):

        key = self.map_key(key)

        self.events.emit(
            "ui_key",
            key
        )

        if not self.current_screen:
            return

        # BACK

        if key == "BACK":

            self.events.emit(
                Event.BACK
            )

            self.back()

            return

        # MENU

        if key == "MENU":

            self.events.emit(
                Event.MENU
            )

            return

        # LEFT / RIGHT

        if key == "LEFT":

            self.events.emit(
                Event.LEFT
            )

        elif key == "RIGHT":

            self.events.emit(
                Event.RIGHT
            )

        # SCREEN

        self.current_screen.handle_key(
            key
        )

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

        frame_ms = int(
            1000 / self.fps
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

                time.sleep_ms(
                    delay
                )

    def stop(self):

        self.running = False

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    def on(
        self,
        event,
        callback
    ):

        self.events.on(
            event,
            callback
        )

        return self