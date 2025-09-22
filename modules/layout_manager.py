# Copyright (c) 2025 Nate Dickson
# Licensed under the MIT License. See LICENSE.txt for details.

import json
import gc
import os
from time import sleep
import board
import neopixel
from adafruit_hid.keycode import Keycode

class LayoutManager:
    def __init__(self):
        """Initialize the layout manager, load default layout, and set up Neopixel."""
        self.debug_mode = os.getenv("debug_mode", "false").lower() == "true"
        
        # Define color constants for easy reference
        self.color_constants = {
                "red": (255, 0, 0),
                "blue": (0, 0, 255),
                "white": (128, 128, 128),
                "black": (0, 0, 0),
                "yellow": (255, 255, 0),
                "cyan": (0, 255, 255),
                "magenta": (255, 0, 255),
                "orange": (255, 165, 0),
                "purple": (128, 0, 128),
            }
            
        # Initialize Neopixel for visual feedback
        self.pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
        self.default_brightness = os.getenv("brightness", 3)/10
        self.pixel.brightness = self.default_brightness
        self.pixel_color = "00FF00"  # Default to green
        self.set_neopixel_color()

        # Load the default layout 
        self.current_layout_name = os.getenv("default_mapping", "passthrough")
        self.hid_to_keycode = {}
        self.load_layout(self.current_layout_name)

        # Initialize swap key and available layouts
        swap_key_string = os.getenv("layout_swap_key", "0x30")
        self.swap_key = hex(int(swap_key_string, 16)) 
        self.available_layouts = os.getenv("available", "passthrough,f_keys,WoW,other_game").split(",")
        self.layout_index = self.available_layouts.index(self.current_layout_name)
        self.max_layouts = len(self.available_layouts)

        # Debug statements
        
        if(self.debug_mode): 
            print("Layout Manager: Debug mode is ON")
            print (f"current default: {os.getenv('default_mapping')}")
            print (f"Current layout: {self.available_layouts[self.layout_index]}")
            print (f"Available layouts: {self.available_layouts}")
            print (f"Swap Key: {self.swap_key}")
            print(f"Memory before gc: {gc.mem_free()}")
            gc.collect()
            print(f"Memory after gc: {gc.mem_free()}")
        gc.collect()

    def load_layout(self, layout_name):
        """Load a keyboard layout from a JSON file."""
        try:
            with open(f"{os.getenv('mapping_directory', 'keymaps/')}{layout_name}.json", "r") as f:
                current_layout = json.load(f)
                if(self.debug_mode):  
                    print(f"Loaded layout: {layout_name}\n")
                for mapping in current_layout['keymaps']:
                    for hex_str, keycode_str in mapping.items():
                      hex_key = hex(int(hex_str, 16))
                      keycode = getattr(Keycode, keycode_str, None)
                      if(self.debug_mode):  
                          print(f"Loaded mapping: {hex_key} -> {keycode}")
                      if keycode:
                        self.hid_to_keycode[hex_key] = keycode
                self.pixel_color = current_layout.get('led_color', 'red')
                self.set_neopixel_color()
                del current_layout
                gc.collect()  # Free up memory after loading
                if(self.debug_mode):  
                    print(f"Loaded layout {layout_name} with {len(self.hid_to_keycode)} mappings")
                    print(f"neopixel color: {self.pixel_color}")
        except Exception as e:
            print(f"Unexpected error loading layout: {e}")
            gc.collect()
            return None
        
    def get_key_mapping(self, hexcode):
        """Get the remapped keycode from the current layout."""
        if hexcode == self.swap_key: 
            self.get_next_layout()
            return None
        self.flicker_pixel()
        return self.hid_to_keycode.get(hexcode, hexcode)

    def flicker_pixel(self):
        """Briefly flicker the neopixel to indicate activity."""
        original_brightness = self.pixel.brightness
        temp_brightness = 0.0
        self.pixel.brightness = temp_brightness
        sleep(0.1)
        self.pixel.brightness = original_brightness  

    def get_next_layout(self):
        """Cycle to the next available layout."""
        self.layout_index = (self.layout_index + 1) % self.max_layouts
        next_layout = self.available_layouts[self.layout_index]
        if(self.debug_mode):
            print(f"Switching to layout: {next_layout}")
        self.load_layout(next_layout)
        return next_layout

    def set_neopixel_color(self):
        """ 
        Use the color from the layout to set the neopixel color.
        Accepts color names or hex strings (e.g., "red" or "FF0000").
        If there is no layout color setting, defaults to red.
        """
        color_string = self.pixel_color
        if(self.debug_mode):
            print(f"Setting neopixel color to: {color_string}")
        if color_string.lower() in self.color_constants:
            self.pixel.fill(self.color_constants[color_string.lower()])
        try:
            hex_color = int(color_string, 16)
            self.pixel.fill(((hex_color >> 16) & 0xFF, (hex_color >> 8) & 0xFF, hex_color & 0xFF))
        except ValueError:
            return None