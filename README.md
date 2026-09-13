# ESPUI

A lightweight and modular UI framework for **ESP32 + MicroPython**.

ESPUI makes it easier to build applications for ESP32 without dealing directly with low-level display drawing, keypad scanning, focus management, layouts, scrolling, and screen navigation.

> 🚧 ESPUI is currently under development.

## Features

* 🖥️ Display abstraction
* ⌨️ 4×4 matrix keypad support
* 📱 Screen-based UI
* 🧩 Widget system
* 📦 Containers
* 📐 Vertical, horizontal, and grid layouts
* 📜 Scrollable views
* 🎯 Focus management
* 🔄 Screen navigation
* 🔔 Notifications
* 💬 Dialogs
* 🎛️ Buttons
* ☑️ Checkboxes
* 🔘 Toggles
* 🎚️ Sliders
* 📊 Progress bars
* 🏷️ Labels
* ⚡ Event system
* 🔌 Hardware abstraction

---

## Architecture

ESPUI is designed in layers:

```text
┌─────────────────────┐
│        App          │
├─────────────────────┤
│       Widgets       │
├─────────────────────┤
│      UI Core        │
├─────────────────────┤
│  Display / Input    │
├─────────────────────┤
│      Hardware       │
└─────────────────────┘
```

The UI layer does not need to know how the display or input hardware works internally.

This makes it possible to add support for different displays and controllers in the future.

---

## Installation

Copy `espui.py` to your MicroPython device.

Example:

```text
ESP32/
├── boot.py
├── main.py
├── espui.py
└── ssd1306.py
```

Then import it:

```python
from espui import *
```

---

# Quick Start

## 1. Create the Display

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

---

## 2. Create the Controller

Example using a 4×4 matrix keypad:

```python
keypad = Keypad4x4(
    rows=[13, 12, 14, 27],
    cols=[26, 25, 33, 32]
)
```

Default keypad layout:

```text
1  2  3  A
4  5  6  B
7  8  9  C
*  0  #  D
```

---

## 3. Initialize ESPUI

```python
ui = UI()

ui.begin(
    display=display,
    controller=keypad
)
```

---

# Creating a Screen

A screen is the main container for an application page.

```python
home = Screen("Home")

home.header("ESP32 Control")
home.footer("2/8 Move   A OK   B Back")
```

Show it:

```python
ui.show(home)
```

Run the UI:

```python
ui.run()
```

---

# Widgets

## Label

```python
label = Label("Hello ESP32")

home.content.add(label)
```

## Button

```python
button = Button("WiFi")

home.content.add(button)
```

## Toggle

```python
wifi = Toggle("WiFi", True)

home.content.add(wifi)
```

## Checkbox

```python
debug = Checkbox("Debug Mode")

home.content.add(debug)
```

## Slider

```python
volume = Slider("Volume", 50)

home.content.add(volume)
```

## Progress Bar

```python
progress = ProgressBar(
    "Download",
    75
)

home.content.add(progress)
```

---

# Events

Widgets can emit events.

Example:

```python
wifi_button = Button("WiFi")

wifi_button.on(
    Event.CLICK,
    lambda: print("WiFi clicked")
)

home.content.add(wifi_button)
```

Available events include:

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
```

---

# Screen Navigation

ESPUI includes a navigation stack.

## Push a new screen

```python
settings = Screen("Settings")

button.on(
    Event.CLICK,
    lambda: ui.push(settings)
)
```

The current screen is kept in the navigation stack.

```text
Home
  ↓
Settings
```

## Go back

```python
ui.back()
```

This returns to the previous screen.

```text
Settings
   ↓
Home
```

## Replace the current screen

```python
ui.show(home)
```

`show()` directly changes the current screen.

---

# Multiple Screens Example

```python
home = Screen("Home")
wifi = Screen("WiFi")
settings = Screen("Settings")

home.header("Home")
wifi.header("WiFi")
settings.header("Settings")

wifi_button = Button("WiFi")
settings_button = Button("Settings")

home.content.add(wifi_button)
home.content.add(settings_button)

wifi_button.on(
    Event.CLICK,
    lambda: ui.push(wifi)
)

settings_button.on(
    Event.CLICK,
    lambda: ui.push(settings)
)

ui.show(home)
ui.run()
```

Navigation:

```text
Home
├── WiFi
│   └── Back → Home
│
└── Settings
    └── Back → Home
```

---

# Containers

Containers allow widgets to be grouped together.

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

home.content.add(container)
```

---

# Layouts

ESPUI supports several basic layouts.

### Vertical

```python
container.layout_type = "vertical"
```

```text
Button
Button
Button
Button
```

### Horizontal

```python
container.layout_type = "horizontal"
```

```text
Button   Button   Button
```

### Grid

```python
container.layout_type = "grid"
```

```text
Button  Button
Button  Button
Button  Button
```

---

# ScrollView

For large interfaces, use `ScrollView`.

```python
scroll = ScrollView()

home.set_content(scroll)

scroll.add(
    Button("WiFi")
)

scroll.add(
    Button("Bluetooth")
)

scroll.add(
    Button("Settings")
)

scroll.add(
    Button("About")
)
```

The content can extend beyond the display.

ESPUI automatically handles scrolling and the scrollbar.

You can also control scrolling manually:

```python
scroll.scroll_down()
```

```python
scroll.scroll_up()
```

Or:

```python
scroll.scroll_by(10)
```

---

# Header, Footer and Sidebar

## Header

```python
home.header("Network")
```

## Footer

```python
home.footer(
    "2/8 Navigate   A Select   B Back"
)
```

## Sidebar

```python
home.sidebar([
    "Home",
    "Network",
    "Settings",
    "About"
])
```

---

# Complete Example

```python
from machine import Pin, I2C
import ssd1306

from espui import *


# -------------------------
# Display
# -------------------------

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


# -------------------------
# Keypad
# -------------------------

keypad = Keypad4x4(
    rows=[13, 12, 14, 27],
    cols=[26, 25, 33, 32]
)


# -------------------------
# UI
# -------------------------

ui = UI()

ui.begin(
    display=display,
    controller=keypad
)


# -------------------------
# Home
# -------------------------

home = Screen("Home")

home.header("ESP32 Control")
home.footer("2/8 Move   A OK   B Back")

scroll = ScrollView()

home.set_content(scroll)


# -------------------------
# Settings
# -------------------------

settings = Screen("Settings")

settings.header("Settings")
settings.footer("B Back")

settings_scroll = ScrollView()

settings.set_content(settings_scroll)

settings_scroll.add(
    Toggle("WiFi", True)
)

settings_scroll.add(
    Toggle("Bluetooth", False)
)

settings_scroll.add(
    Slider("Volume", 50)
)


# -------------------------
# Home Widgets
# -------------------------

wifi_button = Button("WiFi")
settings_button = Button("Settings")

scroll.add(wifi_button)
scroll.add(settings_button)
scroll.add(Checkbox("Debug Mode"))
scroll.add(Slider("Brightness", 80))


# -------------------------
# Navigation
# -------------------------

settings_button.on(
    Event.CLICK,
    lambda: ui.push(settings)
)

wifi_button.on(
    Event.CLICK,
    lambda: home.notify("WiFi selected")
)


# -------------------------
# Start
# -------------------------

ui.show(home)
ui.run()
```

---

# Key Mapping

The default keypad mapping is:

| Key       | Action |
| --------- | ------ |
| `2`       | Up     |
| `8`       | Down   |
| `4`       | Left   |
| `6`       | Right  |
| `A` / `#` | OK     |
| `B` / `*` | Back   |
| `C`       | Menu   |

This mapping can be extended or changed as the framework evolves.

---

# Project Structure

The current project can remain very simple:

```text
ESPUI/
├── espui.py
├── ssd1306.py
├── main.py
└── README.md
```

The goal is to eventually separate the framework into modules as it grows.

---

# Design Goals

ESPUI is being designed with the following goals:

### Simple

An application developer should be able to create a UI without manually handling:

* OLED coordinates
* Drawing operations
* Keypad scanning
* Focus movement
* Scrolling
* Screen management

### Lightweight

ESP32 devices have limited RAM and processing power.

ESPUI is designed to stay lightweight and suitable for MicroPython.

### Modular

Hardware and UI logic should remain separated.

### Extensible

The framework is intended to grow beyond OLED + keypad.

Possible future controllers:

```text
Matrix Keypad
Rotary Encoder
Buttons
Touchscreen
Joystick
Gamepad
```

Possible future displays:

```text
SSD1306
SH1106
LCD
TFT
Color Displays
```

---

# Roadmap

## UI

* [x] Screens
* [x] Widgets
* [x] Containers
* [x] Basic layouts
* [x] ScrollView
* [x] Focus system
* [x] Navigation stack
* [x] Header
* [x] Footer
* [x] Basic sidebar
* [ ] Interactive sidebar
* [ ] ListView
* [ ] Dropdown / Select
* [ ] TextInput
* [ ] Virtual keyboard
* [ ] Icons
* [ ] Custom fonts
* [ ] Themes
* [ ] Animations

## Hardware

* [x] SSD1306 support through display abstraction
* [x] Matrix keypad
* [ ] Rotary encoder
* [ ] Touch input
* [ ] More OLED drivers
* [ ] TFT displays

## Application System

* [ ] App manager
* [ ] Application launcher
* [ ] Window system
* [ ] Settings system
* [ ] Plugin/API system
* [ ] Multi-app management

## ESP32 OS

The long-term goal is to use ESPUI as the foundation for a lightweight ESP32 operating environment.

```text
ESP32
 │
 ├── Hardware Drivers
 │
 ├── ESPUI
 │
 ├── System Services
 │
 ├── App Manager
 │
 └── Applications
```

---

# Contributing

Contributions, ideas, bug reports, and feature suggestions are welcome.

If you find a problem, please open an issue with:

1. ESP32 board model
2. MicroPython version
3. Display/controller used
4. Minimal example
5. Error message or unexpected behavior

---

# License

License information will be added as the project develops.

---

## Status

**Early Development / Experimental**

The API may change significantly before the first stable release.
