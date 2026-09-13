# ESPUI

### Lightweight UI Framework for ESP32 + MicroPython

ESPUI is a lightweight UI framework designed for **ESP32 + MicroPython**.

It provides a simple way to build graphical interfaces for small displays such as OLED screens without manually implementing:

* Display drawing
* Widget positioning
* Layout management
* Scrolling
* Focus navigation
* Keyboard input
* Screen navigation
* Sidebar navigation
* Notifications
* Dialogs
* UI events

ESPUI is designed for small embedded devices where memory, processing power, and display space are limited.

> **Version:** 1.1
> **Platform:** ESP32
> **Language:** MicroPython
> **Status:** Experimental / In Development

---

# Features

* Lightweight and modular
* Designed for ESP32 + MicroPython
* SSD1306-compatible display abstraction
* 4×4 matrix keypad support
* Screen-based application structure
* Widget system
* Containers
* Vertical layouts
* Horizontal layouts
* Grid layouts
* Scrollable content
* Automatic scrollbar
* Focus management
* Automatic focus scrolling
* Nested containers
* Header
* Footer
* Sidebar
* Notifications
* Dialogs
* Event system
* Button controls
* Toggle controls
* Checkbox controls
* Slider controls
* Progress bars
* Labels
* Separators
* Long-text truncation
* Text wrapping
* Display clipping
* Screen navigation stack

---

# Requirements

ESPUI is designed for:

* ESP32
* MicroPython
* A compatible display driver
* Optional 4×4 matrix keypad

A typical setup can use:

* SSD1306 OLED 128×64
* `ssd1306.py`
* 4×4 matrix keypad

ESPUI itself does not require any external Python package beyond the MicroPython modules required by your hardware and display driver.

---

# Installation

Copy `espui.py` to your ESP32.

A simple project can look like:

```text
ESP32/
├── boot.py
├── main.py
├── espui.py
└── ssd1306.py
```

Then import ESPUI:

```python
from espui import *
```

---

# Quick Start

## Display

Example using an SSD1306 OLED:

```python
from machine import Pin, I2C
import ssd1306

from espui import *

i2c = I2C(
    0,
    scl=Pin(22),
    sda=Pin(21)
)

oled = ssd1306.SSD1306_I2C(
    128,
    64,
    i2c
)

display = Display(
    oled,
    128,
    64
)
```

`Display` acts as an abstraction layer between ESPUI and the actual display driver.

It also provides clipping, text fitting, wrapping, rectangles, lines and other drawing functions.

---

# Input

ESPUI includes a 4×4 matrix keypad controller.

```python
keypad = Keypad4x4(
    rows=[13, 12, 14, 27],
    cols=[26, 25, 33, 32]
)
```

Default keypad:

```text
┌───┬───┬───┬───┐
│ 1 │ 2 │ 3 │ A │
├───┼───┼───┼───┤
│ 4 │ 5 │ 6 │ B │
├───┼───┼───┼───┤
│ 7 │ 8 │ 9 │ C │
├───┼───┼───┼───┤
│ * │ 0 │ # │ D │
└───┴───┴───┴───┘
```

The keypad supports:

* Key press
* Key release
* Key hold
* Key repeat

The controller also provides configurable hold and repeat timing.

---

# Creating the UI

Create the UI core:

```python
ui = UI()

ui.begin(
    display=display,
    controller=keypad
)
```

---

# Screens

A `Screen` represents a complete UI page.

```python
home = Screen("Home")
```

Add a header:

```python
home.header("ESP32 Control")
```

Add a footer:

```python
home.footer("2/8 Move   A OK   B Back")
```

Display the screen:

```python
ui.show(home)
```

Start the UI:

```python
ui.run()
```

---

# Header

Enable or change the header:

```python
home.header("ESP32 Control")
```

Disable it:

```python
home.hide_header()
```

The header is separated from the content area so normal widgets are clipped below it.

---

# Footer

Create a footer:

```python
home.footer("2/8 Move   A OK   B Back")
```

Hide it:

```python
home.hide_footer()
```

---

# Widgets

ESPUI currently provides several basic widgets.

| Widget        | Focusable | Main purpose      |
| ------------- | --------: | ----------------- |
| `Label`       |        No | Display text      |
| `Button`      |       Yes | Trigger actions   |
| `Toggle`      |       Yes | On/off value      |
| `Checkbox`    |       Yes | Boolean checkbox  |
| `Slider`      |       Yes | Numeric value     |
| `ProgressBar` |        No | Display progress  |
| `Separator`   |        No | Visual separation |

Focusable widgets participate in the screen focus system. The current implementation marks Button, Toggle and Slider as focusable, while Checkbox inherits that behavior from Toggle.

---

# Label

A label displays text.

```python
label = Label("Hello ESP32")

home.add(label)
```

Alignment can be changed:

```python
Label(
    "Centered",
    align="center"
)
```

Available alignments:

```text
left
center
right
```

You can also change the text color:

```python
Label(
    "Status: OK",
    text_color=1
)
```

---

# Button

Create a button:

```python
button = Button("WiFi")

home.add(button)
```

Buttons are focusable and respond to `OK`.

The focused button uses a different visual style:

```text
> WiFi <
```

while an unfocused button is displayed with an outline. Long button text is automatically fitted to the available space.

---

# Button Events

Buttons emit `Event.CLICK`.

```python
button.on(
    Event.CLICK,
    lambda: print("Button clicked")
)
```

For larger functions:

```python
def on_wifi():
    print("WiFi selected")

button.on(
    Event.CLICK,
    on_wifi
)
```

---

# Toggle

Create a toggle:

```python
wifi = Toggle(
    "WiFi",
    True
)

home.add(wifi)
```

Change its value:

```python
wifi.set_value(True)
wifi.set_value(False)
```

Toggle it manually:

```python
wifi.toggle()
```

A Toggle emits `Event.CHANGE` when its value changes:

```python
wifi.on(
    Event.CHANGE,
    lambda value: print("WiFi:", value)
)
```

Pressing `OK` while the Toggle is focused changes its state.

---

# Checkbox

Checkbox is based on Toggle:

```python
debug = Checkbox(
    "Debug Mode"
)

home.add(debug)
```

It supports the same basic value operations and `CHANGE` event.

```python
debug.on(
    Event.CHANGE,
    lambda value: print("Debug:", value)
)
```

---

# Slider

Create a slider:

```python
volume = Slider(
    "Volume",
    50
)

home.add(volume)
```

With custom limits:

```python
brightness = Slider(
    "Brightness",
    80,
    0,
    100
)
```

Change the value:

```python
brightness.set_value(60)
```

The slider responds to:

```text
LEFT  → decrease
RIGHT → increase
```

It emits `Event.CHANGE` when the value changes.

---

# ProgressBar

Create a progress bar:

```python
progress = ProgressBar(75)

home.add(progress)
```

Change it:

```python
progress.set_value(90)
```

The value is automatically limited to:

```text
0 - 100
```

---

# Separator

A separator can visually divide sections:

```python
home.add(
    Separator()
)
```

Custom height:

```python
home.add(
    Separator(height=8)
)
```

---

# Containers

Containers allow multiple widgets to be grouped together.

```python
container = Container()

container.add(
    Label("Network")
)

container.add(
    Button("Scan")
)

container.add(
    Button("Saved Networks")
)

home.add(container)
```

Containers can contain other containers, allowing nested UI structures. The focus system recursively searches nested containers for focusable widgets.

---

# Layouts

ESPUI provides three basic layouts.

## Vertical

```python
container = Container(
    layout="vertical"
)
```

Result:

```text
Button
Button
Button
Button
```

---

## Horizontal

```python
container = Container(
    layout="horizontal"
)
```

Result:

```text
Button   Button   Button
```

---

## Grid

```python
container = Container(
    layout="grid"
)
```

On a sufficiently wide display:

```text
Button   Button
Button   Button
Button   Button
```

The grid automatically uses fewer columns on narrow displays.

---

# Spacing

Containers support spacing between widgets:

```python
container = Container(
    layout="vertical",
    spacing=4
)
```

Widgets also support:

```python
widget.gap_before = 2
widget.gap_after = 2
```

This can be useful when creating clearer groups of controls.

---

# ScrollView

`ScrollView` is designed for content that is larger than the available display area.

```python
scroll = ScrollView()

home.set_content(scroll)
```

Add widgets:

```python
scroll.add(
    Label("Network Settings")
)

scroll.add(
    Toggle("WiFi")
)

scroll.add(
    Toggle("Bluetooth")
)

scroll.add(
    Slider("Brightness", 80)
)

scroll.add(
    Button("Save")
)
```

The content can extend beyond the physical display.

ESPUI calculates virtual widget positions and clips the content to the ScrollView viewport. A scrollbar is displayed automatically when necessary.

---

# Manual Scrolling

Scroll down:

```python
scroll.scroll_down()
```

Scroll up:

```python
scroll.scroll_up()
```

Scroll by a custom amount:

```python
scroll.scroll_by(10)
```

Move to an exact position:

```python
scroll.scroll_to(20)
```

The scroll position is automatically limited to the valid content range.

---

# Focus System

ESPUI has a built-in focus system for interactive widgets.

Focusable widgets include:

```text
Button
Toggle
Checkbox
Slider
```

The screen automatically collects focusable widgets, maintains a focus index, and calls the widget's `focus()` / `blur()` methods.

Move focus:

```text
2 → Previous
8 → Next
```

The focused widget can also request automatic scrolling when it is outside the visible area.

---

# Keyboard Mapping

The default 4×4 keypad is mapped to UI actions as follows:

| Key | Action |
| --- | ------ |
| `2` | UP     |
| `8` | DOWN   |
| `4` | LEFT   |
| `6` | RIGHT  |
| `A` | OK     |
| `#` | OK     |
| `B` | BACK   |
| `*` | BACK   |
| `C` | MENU   |

The mapping is implemented by `UI.map_key()`.

---

# Screen Navigation

ESPUI includes a simple navigation stack.

Create screens:

```python
home = Screen("Home")
settings = Screen("Settings")
```

Navigate to Settings:

```python
button.on(
    Event.CLICK,
    lambda: ui.push(settings)
)
```

Go back:

```python
ui.back()
```

The previous screen is stored in the navigation stack.

---

# Replace Current Screen

You can directly switch screens without pushing the current screen onto the navigation stack:

```python
ui.show(settings)
```

Use:

```python
ui.push(settings)
```

when you want `BACK` to return to the previous screen.

Use:

```python
ui.show(settings)
```

when you want to replace the current screen.

---

# Sidebar

A screen can have a sidebar:

```python
home.sidebar([
    "Home",
    "Network",
    "Settings",
    "About"
])
```

Sidebar items can also contain targets:

```python
home.sidebar([
    ("Home", home),
    ("Settings", settings)
])
```

A dictionary can also be used:

```python
home.sidebar([
    {
        "label": "Home",
        "target": home
    },
    {
        "label": "Settings",
        "target": settings
    }
])
```

The sidebar has its own focus state and scrolling system. LEFT enters the sidebar and RIGHT returns to content navigation.

---

# Notifications

Display a temporary notification:

```python
home.notify(
    "WiFi selected"
)
```

Custom duration:

```python
home.notify(
    "Saved!",
    duration=3000
)
```

The duration is specified in milliseconds.

---

# Dialogs

Show a dialog:

```python
home.show_dialog(
    "Warning",
    "Are you sure?"
)
```

Close it:

```python
home.close_dialog()
```

When a dialog is visible, it receives priority over normal screen navigation. `OK` and `BACK` close the dialog.

---

# Events

ESPUI provides a simple event emitter.

Register an event:

```python
button.on(
    Event.CLICK,
    my_function
)
```

Available event constants include:

```text
KEY_PRESS
KEY_RELEASE
KEY_HOLD
KEY_REPEAT

CLICK
CHANGE

FOCUS
BLUR

UP
DOWN
LEFT
RIGHT

OK
BACK
MENU

SIDEBAR_FOCUS
SIDEBAR_BLUR
SIDEBAR_CHANGE
SIDEBAR_SELECT
```

The event system is shared by the UI core and widgets.

---

# Global UI Events

The `UI` object also has an event emitter:

```python
ui.on(
    "ui_key",
    lambda key: print("Key:", key)
)
```

This can be useful for application-level input handling.

---

# Complete Example

```python
from machine import Pin, I2C
import ssd1306

from espui import *


# ============================================================
# DISPLAY
# ============================================================

i2c = I2C(
    0,
    scl=Pin(22),
    sda=Pin(21)
)

oled = ssd1306.SSD1306_I2C(
    128,
    64,
    i2c
)

display = Display(
    oled,
    128,
    64
)


# ============================================================
# KEYPAD
# ============================================================

keypad = Keypad4x4(
    rows=[13, 12, 14, 27],
    cols=[26, 25, 33, 32]
)


# ============================================================
# UI
# ============================================================

ui = UI(fps=20)

ui.begin(
    display=display,
    controller=keypad
)


# ============================================================
# SCREENS
# ============================================================

home = Screen("Home")
settings = Screen("Settings")


home.header("ESP32 Control")
home.footer("2/8 Move   A OK   B Back")

settings.header("Settings")
settings.footer("B Back")


# ============================================================
# HOME CONTENT
# ============================================================

home_scroll = ScrollView()

home.set_content(
    home_scroll
)

wifi_button = Button("WiFi")
settings_button = Button("Settings")

debug = Checkbox("Debug Mode")
brightness = Slider(
    "Brightness",
    80
)

home_scroll.add(
    Label("System Control")
)

home_scroll.add(
    wifi_button
)

home_scroll.add(
    settings_button
)

home_scroll.add(
    debug
)

home_scroll.add(
    brightness
)


# ============================================================
# SETTINGS CONTENT
# ============================================================

settings_scroll = ScrollView()

settings.set_content(
    settings_scroll
)

wifi = Toggle(
    "WiFi",
    True
)

bluetooth = Toggle(
    "Bluetooth",
    False
)

volume = Slider(
    "Volume",
    50
)

settings_scroll.add(
    Label("Settings")
)

settings_scroll.add(
    wifi
)

settings_scroll.add(
    bluetooth
)

settings_scroll.add(
    volume
)


# ============================================================
# EVENTS
# ============================================================

wifi_button.on(
    Event.CLICK,
    lambda: home.notify(
        "WiFi selected"
    )
)

settings_button.on(
    Event.CLICK,
    lambda: ui.push(settings)
)

wifi.on(
    Event.CHANGE,
    lambda value: home.notify(
        "WiFi: {}".format(value)
    )
)

volume.on(
    Event.CHANGE,
    lambda value: print(
        "Volume:",
        value
    )
)


# ============================================================
# START
# ============================================================

ui.show(home)
ui.run()
```

---

# Architecture

ESPUI is organized into several layers:

```text
┌───────────────────────────┐
│       Application         │
├───────────────────────────┤
│          Screen           │
├───────────────────────────┤
│        Containers         │
├───────────────────────────┤
│          Widgets          │
├───────────────────────────┤
│        UI / Events        │
├───────────────────────────┤
│    Display / Controller   │
├───────────────────────────┤
│         Hardware          │
└───────────────────────────┘
```

### Core classes

```text
Event
EventEmitter
Display
Keypad4x4
Widget
Container
ScrollView
Label
Button
Toggle
Checkbox
Slider
ProgressBar
Separator
Dialog
Screen
UI
```

This structure keeps hardware handling, UI logic, layout, widgets and application code separated.

---

# Display Abstraction

The `Display` class provides a common interface around the MicroPython display driver.

Main operations include:

```python
display.clear()
display.show()

display.pixel(...)
display.line(...)
display.rect(...)
display.fill_rect(...)

display.text(...)
display.text_clipped(...)

display.hline(...)
display.vline(...)
```

It also supports nested clipping regions:

```python
display.push_clip(
    x,
    y,
    width,
    height
)

# Draw content

display.pop_clip()
```

This is especially important for ScrollView and screen content.

---

# Text Handling

ESPUI includes several text utilities.

Fit text:

```python
display.fit_text(
    "Very long text",
    80
)
```

Wrap text:

```python
display.wrap_text(
    "This is a long sentence",
    80
)
```

Clipped text:

```python
display.text_clipped(
    "Hello ESP32",
    0,
    20,
    width=100
)
```

Text can be aligned:

```python
align="left"
align="center"
align="right"
```

Long text can automatically use an ellipsis:

```text
This is a very...
```

---

# Custom Widgets

ESPUI is designed to be extendable.

A custom widget can inherit from `Widget`:

```python
class MyWidget(Widget):

    def __init__(self):
        super().__init__(
            height=14
        )

    def draw(self, display):
        display.rect(
            self.x,
            self.y,
            self.width,
            self.height
        )
```

Then add it to a screen:

```python
home.add(
    MyWidget()
)
```

For an interactive widget, enable focus:

```python
self.focusable = True
```

and implement:

```python
def handle_key(self, key):
    ...
```

---

# Performance

ESPUI is designed for small embedded displays.

The default UI loop runs at:

```python
UI(fps=20)
```

You can change it:

```python
ui = UI(fps=30)
```

Lower FPS can reduce CPU usage while higher FPS can make animations and input feel more responsive.

For small OLED interfaces, keeping the UI simple and avoiding unnecessarily expensive operations is recommended.

---

# Project Structure

A minimal ESPUI project:

```text
ESP32/
│
├── boot.py
├── main.py
├── espui.py
└── ssd1306.py
```

A larger application can be organized as:

```text
ESP32/
│
├── boot.py
├── main.py
├── espui.py
├── ssd1306.py
│
├── screens/
│   ├── home.py
│   ├── settings.py
│   └── network.py
│
└── app/
    ├── config.py
    └── events.py
```

For early development, keeping everything in `main.py` is perfectly fine.

---

# Version 1.1

## Main capabilities

ESPUI 1.1 provides:

* Display abstraction
* Text clipping
* Text fitting
* Text wrapping
* 4×4 keypad input
* Key press / release / hold / repeat
* Screens
* Screen navigation
* Navigation stack
* Focus management
* Nested containers
* Vertical layout
* Horizontal layout
* Grid layout
* ScrollView
* Automatic scrollbar
* Header
* Footer
* Sidebar
* Notifications
* Dialogs
* Buttons
* Toggles
* Checkboxes
* Sliders
* Progress bars
* Labels
* Separators
* Event callbacks

---

# Roadmap

Planned improvements include:

* More widgets
* Better focus visualization
* Improved nested scrolling
* More layout options
* More display-driver compatibility
* Touchscreen input
* Additional input controllers
* Theme system
* Better animations
* More advanced dialogs
* More powerful navigation
* Improved documentation
* Examples for common ESP32 projects
* Modular package structure

---

# Contributing

ESPUI is an experimental project and is still evolving.

Ideas, bug reports, improvements and new widgets are welcome.

When contributing, try to keep the framework:

* Lightweight
* Simple
* MicroPython-friendly
* Memory efficient
* Easy to understand
* Suitable for small displays

---

# License

See the repository for the current license information.

---

# Repository

**ESPUI**

GitHub:

https://github.com/amirmc132/espui

Main source:

`espui.py`

---

## Author

Created by **amirmc132**.

ESPUI is intended to make building embedded graphical interfaces with ESP32 + MicroPython easier while keeping the framework small and customizable.
