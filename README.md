# Light A Fire
an exhibit where a user creates fire by wiggling a stick on a sensor like in the good ol' days.
# Installation
clone the repo and run the setup script. 
```bash
git clone https://github.com/jerusalem-science-museum/energy-light-a-fire.git
cd energy-light-a-fire/graphics
chmod +x setup_gui_rpi.sh && ./setup_gui_rpi.sh
```
this installs required packages and pip installs + adds run.sh to autostart.
NOTE: opencv-python might take a long time to install... worst case just do 
```bash
sudo apt install -y python3-opencv
```
and pip install requirements manually... :(
# How It Works
an arduino is connected to a thermal sensor, that updates the temperature to the RaspberryPi.  
When the visitor wiggles the stick on the sensor the temperature rises, and at specific points an animation of smoke and fire appears via pygame.  
a watchdog is used to rerun the main.py because the usb camera connection might reset sometimes. The arduino is reconnected within the script itself.
