# Keyhabilitator: Rescuing Good But Old Hardware

This is a little project to create useful mappings for a device that a friend of mine likes. The software to customize it has long since stopped working.

In this particular case the hardware in question is a "Fang" Gamepad, sometimes called a Z-pad, or called by its model number: [KU-0536](https://duckduckgo.com/?q=ku-0536).

On eBay they are still selling for roughly US$100, so it's worth (key)habilitating.

So I'm putting an [Adafruit Feather RP 2040 with Type A Host](https://learn.adafruit.com/adafruit-feather-rp2040-with-usb-type-a-host/overview) between the device and the computer. This project, written in CircuitPython, allows the user to capture the outputs of the keyboard and re-map them to the desired inputs for their computer.

## Building

This code is written for [CircuitPython 10.0.0-beta.3](https://circuitpython.org/board/adafruit_feather_rp2040_usb_host/)

The following libraries are required:

* `/adafruit_bus_device`
* `/adafruit_hid`
* `adafruit_pixelbuf.mpy`
* `adafruit_usb_host_descriptors.mpy`
* `neopixel.mpy`

## Configuration

Defaults are set using the `settings.toml` file in the root directory.

Creating new keymaps involves placing a `.json` file in the `/keymaps` directory. The format is:

```json
{
    "name": "passthrough",
    "led_color": "WHITE",
    "hid_key_maps": [
     {"0x29" : "ESC"},
     {"0x2B" : "F10"},
     ...
    ]
}

```

### `hid_key_maps` Values

The keys are the hex value of the key sent in from the USB device. The values are the constant names from `adafruit_hid.keycode.Keycode`. See the official docs for the [full list](https://docs.circuitpython.org/projects/hid/en/latest/index.html) (scroll down.)

### Colors

The `led_color` value can be any of the constants set in `layout_manager.py` (feel free to add your own) Or you can use hex color strings like `00FFBB` and it will convert those as well.

Right now the device will turn the neopixel green to show it's booted up, then change to the color in its default keymap. If it can't figure out what color that is, it will turn red. It flickers when you type. It's fun!
And yes, the file has white defined as half-white, because neopixels are bad at interpreting brightness and RGB codes at the same time.


The `name` is currently unused but could be used if you are working with a device that has a screen or something.

## TODO:

I need to implement a hotkey combo that will let the user switch keymaps on the fly.