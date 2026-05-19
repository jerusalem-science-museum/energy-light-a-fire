import time
import subprocess
import wmi

SCRIPT_PATH = "python main.py"

process = None

def run_script():
    global process
    if process is not None:
        process.terminate()
        process.wait()
    print("Running script...")
    process = subprocess.Popen(SCRIPT_PATH.split())

def is_target_device(name):
    name_upper = (name or '').upper()
    return 'CH340' in name_upper or 'USB CAMERA' in name_upper

run_script()

c = wmi.WMI()
watcher = c.Win32_PnPEntity.watch_for(notification_type="Creation", delay_secs=1)

while True:
    device = watcher()
    if is_target_device(device.Name):
        print(f"Target device reconnected: {device.Name}")
        run_script()
        time.sleep(2)
