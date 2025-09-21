import json
import gc
import os
from time import sleep
import board
import neopixel
from adafruit_hid.keycode import Keycode

class LayoutManager:
    def __init__(self):
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
        self.debug_mode = os.getenv("debug_mode") == "true"
        if(self.debug_mode): 
            print("Layout Manager: Debug mode is ON\n")
            print (f"os env: {os.getenv('performance.debug_mode')}")
            print (f"current default: {os.getenv('default_mapping')}")
            gc.collect()
            print(f"Memory after gc: {gc.mem_free()}")
        self.pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
        self.default_brightness = os.getenv("brightness", 3)/10
        self.pixel.brightness = self.default_brightness
        self.pixel.fill((0, 255, 0))  # Indicate ready with green   
        
        self.current_layout = os.getenv("default_mapping", "passthrough")
        self.hid_to_keycode = {}
        self.load_layout(self.current_layout)
       

    def load_layout(self, layout_name):
        """Load a keyboard layout from a JSON file."""
        try:
            with open(f"{os.getenv('mapping_directory', 'keymaps/')}{layout_name}.json", "r") as f:
                self.current_layout = json.load(f)
                if(self.debug_mode):  
                    print(f"Loaded layout: {self.current_layout}\n")
                for mapping in self.current_layout['keymaps']:
                    for hex_str, keycode_str in mapping.items():
                      if(self.debug_mode):  
                          print(f"Loading mapping: {hex_str} -> {keycode_str}\n")
                      hex_key = hex(int(hex_str, 16))
                      keycode = getattr(Keycode, keycode_str, None)
                      if(self.debug_mode):  
                          print(f"Loaded mapping: {hex_key} -> {keycode}\n")
                      if keycode:
                        self.hid_to_keycode[hex_key] = keycode
                if(self.debug_mode):
                    self.current_layout['led_color'] = "FF00FF"
                self.set_neopixel_color()
                gc.collect()  # Free up memory after loading
                if(self.debug_mode):  
                    print(f"keymap: {self.hid_to_keycode}\n")
                    print(f"neopixel color: {self.current_layout['led_color']}")
        except Exception as e:
            print(f"Unexpected error loading layout: {e}")
            gc.collect()
            return None
        
    def get_key_mapping(self, hexcode):
        """Get the remapped keycode from the current layout."""
        if(self.debug_mode):
            print(f"Looking up key mapping for hexcode: {hexcode}")
            print(self.hid_to_keycode[hexcode])
        self.flicker_pixel()
        return self.hid_to_keycode.get(hexcode, hexcode)

    def flicker_pixel(self):
        """Briefly flicker the neopixel to indicate activity."""
        original_brightness = self.pixel.brightness
        temp_brightness = 0.0
        self.pixel.brightness = temp_brightness
        sleep(0.1)
        self.pixel.brightness = original_brightness  

    def set_neopixel_color(self):
        """ 
        Use the color from the layout to set the neopixel color.
        Accepts color names or hex strings (e.g., "red" or "FF0000").
        If there is no layout color setting, defaults to red.
        """
        color_string = self.current_layout.get('led_color', 'red')
        if(self.debug_mode):
            print(f"Setting neopixel color to: {color_string}")
        if color_string.lower() in self.color_constants:
            self.pixel.fill(self.color_constants[color_string.lower()])
        try:
            hex_color = int(color_string, 16)
            self.pixel.fill(((hex_color >> 16) & 0xFF, (hex_color >> 8) & 0xFF, hex_color & 0xFF))
        except ValueError:
            return None
