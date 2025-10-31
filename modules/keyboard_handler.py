import array
import os
import usb
import usb_hid
import adafruit_usb_host_descriptors
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from modules import layout_manager

class KeyboardHandler:
    def __init__(self):
        """Initialize the keyboard handler with USB host and HID devices."""
        self.debug_mode = os.getenv("debug_mode", "false").lower() == "true"
        if(self.debug_mode):
            print("Keyboard Handler:Debug mode is ON\n")

        # hardware configuration
        self.input_device = None
        self.input_endpoint = None
        self.output_device = Keyboard(usb_hid.devices)
        self.hid_buffer = array.array("b", [0] * 8)
        self.setup_input_device()

        # Key handling
        self.old_keys = []
        self.old_modifiers = 0
        self.previous_hid_buffer = array.array("b", [0] * 8)
        self.layout_manager = layout_manager.LayoutManager()

    def setup_input_device(self):
        """Initialize USB input keyboard"""
        for device in usb.core.find(find_all=True):
            kbd_interface_index, kbd_endpoint_address = (
                adafruit_usb_host_descriptors.find_boot_keyboard_endpoint(device)
            )
            if kbd_interface_index is not None:
                if device.is_kernel_driver_active(0):
                    device.detach_kernel_driver(0)
                device.set_configuration()
                self.input_device = device
                self.input_endpoint = kbd_endpoint_address
                return True
        return False

    def parse_hid_report(self, report_data):
        """Parse HID report to extract keycodes and modifiers"""
        modifiers = hex(report_data[0])
        keys = []
        for k in report_data[2:8]:
            if k != 0:
                keys.append(hex(k))
        if(modifiers != 0 and keys != []):
            return f"Modifiers: {modifiers} Keys: {keys}"

    def get_pressed_keys(self, report):
        """Return a list of currently pressed keys from the HID report"""
        pressed_keys = set()
        for i in range(2, 8):
            k = report[i]
            if k > 1:
                pressed_keys.add(hex(k))
        if self.debug_mode:
            print(f"Pressed keys:{list(pressed_keys)}")
        return pressed_keys

    def read_input_with_error_handling(self):
        """Read keyboard input with robust error recovery"""
        if not self.input_device:
            if not self.setup_input_device():
                return None # No device found
        try:
            self.input_device.read(self.input_endpoint, self.hid_buffer, timeout=10)
            if self.debug_mode:
                print("parse_hid_report:")
                self.parse_hid_report(self.hid_buffer)

            self.send_remapped_keys(self.hid_buffer)

            return self.hid_buffer
        except usb.core.USBTimeoutError:
            return None # No data available
        except (usb.core.USBError, OSError) as e:
            print(f"USB error: {e}. Attempting to reinitialize device.")
            self.input_device = None
            self.input_endpoint = None
            if not self.setup_input_device():
                print("Failed to reinitialize device.")
            return None

    def get_modifier_keys(self, modifiers):
        """Convert HID modifier byte to list of Keycode modifier keys"""
        modifier_keys = []
        if modifiers & 0x01:  # Left Ctrl
            modifier_keys.append(Keycode.LEFT_CONTROL)
        if modifiers & 0x02:  # Left Shift
            modifier_keys.append(Keycode.LEFT_SHIFT)
        if modifiers & 0x04:  # Left Alt
            modifier_keys.append(Keycode.LEFT_ALT)
        if modifiers & 0x08:  # Left GUI (Windows/Command key)
            modifier_keys.append(Keycode.LEFT_GUI)
        if modifiers & 0x10:  # Right Ctrl
            modifier_keys.append(Keycode.RIGHT_CONTROL)
        if modifiers & 0x20:  # Right Shift
            modifier_keys.append(Keycode.RIGHT_SHIFT)
        if modifiers & 0x40:  # Right Alt
            modifier_keys.append(Keycode.RIGHT_ALT)
        if modifiers & 0x80:  # Right GUI
            modifier_keys.append(Keycode.RIGHT_GUI)
        return modifier_keys

    def send_remapped_keys(self, hid_buffer):
        try:
            # Extract modifiers and keys from HID buffer
            modifiers = hid_buffer[0]
            keys = self.get_pressed_keys(hid_buffer)

            # Convert current keys to a set for easier comparison
            current_keys = set(keys)
            old_keys = set(self.old_keys)
            if self.debug_mode:
                print(f"current: {list(current_keys)}\n old:{list(old_keys)}")
                print(f"modifiers: {hex(modifiers)}")

            # Get current and old modifier keys
            current_modifiers = set(self.get_modifier_keys(modifiers))
            old_modifiers = set(self.get_modifier_keys(self.old_modifiers))

            # Release modifiers that are no longer pressed
            released_modifiers = old_modifiers - current_modifiers
            for mod in released_modifiers:
                self.output_device.release(mod)

            # Release keys that were pressed but are no longer pressed
            released_keys = old_keys - current_keys
            for key in released_keys:
                remapped_key = self.layout_manager.get_key_mapping(key)
                if remapped_key:
                    self.output_device.release(remapped_key)

            # Press new modifiers that weren't pressed before
            pressed_modifiers = current_modifiers - old_modifiers
            for mod in pressed_modifiers:
                self.output_device.press(mod)

            # Press new keys that weren't pressed before
            pressed_keys = current_keys - old_keys
            for key in pressed_keys:
                remapped_key = self.layout_manager.get_key_mapping(key)
                if remapped_key:
                    self.output_device.press(remapped_key)

            # Update old_keys and old_modifiers for next iteration
            self.old_keys = list(current_keys)
            self.old_modifiers = modifiers

        except Exception as e:
            print(f"Error sending remapped keys: {e}")
