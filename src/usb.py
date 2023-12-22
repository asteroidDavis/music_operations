from typing import List

from watchdog.observers import Observer
import wmi


# Function to detect USB device connections using WMI
def detect_usb_insertion(directory_observers: List[Observer]):
    c = wmi.WMI()
    watcher = c.Win32_DeviceChangeEvent.watch_for("creation")
    while True:
        usb_event = watcher()
        # Check if the newly created device is a USB device
        if "USB" in usb_event.Description:
            for observer in directory_observers:
                observer.start()
