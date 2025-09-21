import array
import os
import usb 
import usb_hid
import adafruit_usb_host_descriptors
from adafruit_hid.keyboard import Keyboard
from modules import layout_manager

class KeyboardHandler:
    def __init__(self):
        """Initialize the keyboard handler with USB host and HID devices."""  
        self.debug_mode = os.getenv("debug_mode", "false").lower() == "true"
        if(self.debug_mode):
            print("Keyboard Handler:Debug mode is ON\n")
        self.input_device = None
        self.input_endpoint = None
        self.output_device = Keyboard(usb_hid.devices)
        self.hid_buffer = array.array("b", [0] * 8)
        self.setup_input_device()
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
        modifiers = report_data[0]
        keys = []
        for k in report_data[2:8]:
            if k != 0:
                keys.append(hex(k))
        if(modifiers != 0 and keys != []):
            return f"{modifiers} + {keys}"

    def get_pressed_keys(self, report):
        """Return a list of currently pressed keys from the HID report"""
        pressed_keys = set()
        for i in range(2, 8):
            k = report[i]
            if k > 1:
                pressed_keys.add(hex(k))
        print(f"Pressed keys: {pressed_keys}\n")
        return pressed_keys
    
    def read_input_with_error_handling(self):
        """Read keyboard input with robust error recovery"""
        if not self.input_device:
            if not self.setup_input_device():
                return None # No device found
        try:
            self.input_device.read(self.input_endpoint, self.hid_buffer, timeout=10)

            self.send_remapped_keys(self.get_pressed_keys(self.hid_buffer))
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
        
    def send_remapped_keys(self, keys):
        try:
            for key in keys:
                remapped_key = self.layout_manager.get_key_mapping(key)
                self.output_device.press(remapped_key)
                self.output_device.release_all()
        except Exception as e:
            print(f"Error sending remapped keys: {e}")
