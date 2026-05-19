import time
import subprocess
import pyudev

context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by(subsystem='usb')

SCRIPT_PATH = "python main.py"

process = None

def run_script():
    global process
    if process is not None:
        process.terminate()
        process.wait()
    print("Running script...")
    process = subprocess.Popen(SCRIPT_PATH.split())

def is_target_device(device):
    attrs = [
        device.get('ID_MODEL', ''),
        device.get('ID_MODEL_ENC', ''),
        device.get('ID_USB_DRIVER', ''),
        device.get('ID_VENDOR', ''),
    ]
    combined = ' '.join(attrs).upper()
    return 'CH340' in combined or 'USB CAMERA' in combined or 'USB_CAMERA' in combined

run_script()

for device in iter(monitor.poll, None):
    if device.action == 'add' and is_target_device(device):
        print(f"Target device reconnected: {device.get('ID_MODEL', 'unknown')}")
        run_script()
        time.sleep(2)
