# Copyright (c) 2025 Nate Dickson
# Licensed under the MIT License. See LICENSE.txt for details.

import os
from modules import keyboard_handler
keyboard_handler = keyboard_handler.KeyboardHandler()
debug_mode = os.getenv("debug_mode", "false").lower() == "true"

print("Keyhabilitator v0.5 by Nate Dickson. MMXXV")

if debug_mode:
    print(f"Debug mode is ON")
    print(os.getenv('debug_mode'))
    print(f"current default: {os.getenv('default_mapping')}")

while True:
    keyboard_handler.read_input_with_error_handling()
    # For Debugging: 
    report = keyboard_handler.parse_hid_report(keyboard_handler.hid_buffer)
    if report:
        print(f"Report: {report}\n")

# type: ignore
