"""
Filename: image_processing.py
Purpose: Display functions for the Light a Fire UI
"""
from consts import *
import numpy as np
import cv2
import time

def robust_reconnect():
    # Try infinite reconnect w common indexes in case the OS shifted the camera path
    while True:
        for index in [0, 1, 2]:
            print(f"Trying to connect to camera index {index}...")
            cap = cv2.VideoCapture(index)
            
            if cap.isOpened():
                # FLUSH THE BUFFER: Grab a few frames immediately to clear out 
                # any initial initialization garbage/blank frames.
                for _ in range(5):
                    ret, frame = cap.read()
                    time.sleep(0.1) # tiny sleep between buffer reads
                    
                # Now check if it's genuinely feeding data
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"Success! Camera found and working on index {index}")
                    return cap
                
                # Opened, but feeding empty frames? Release and try next index.
                cap.release()

def camera_init():
    while True:
        try:
            cap = cv2.VideoCapture(CAMERA_INDEX)  # open the camera
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Réduit la taille du buffer de la caméra
            # cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0 if not auto_exposure else 1)  # disable automatic exposure - IMPORTANT
            # cap.set(cv2.CAP_PROP_AUTO_WB,0 if not auto_white_balance else 1)  # disable automatic white balance - IMPORTANT
            # cap.set(cv2.CAP_PROP_EXPOSURE, fixed_exposure)  # set the exposure to a fixed value - IMPORTANT
            if cap.isOpened():
                print("Camera is ready\n")
                time.sleep(2)  # wait for 2 seconds before trying to open the camera again
                return cap  # if the camera is connected and working, break the loop

        except Exception as e:
            print(
                "Error: Could not open camera. please check if the camera is connected properly.\nRetrying in 2 seconds...\n")
            time.sleep(2)
            pass


def camera_setup(screen, cap: cv2.VideoCapture):
    ret, frame = cap.read()
    if not ret:
        print("Erreur lors de la lecture de la caméra, trying tö réread")
        recovered = False
        for attempt in range(10):  # Try 10 times quickly
            time.sleep(0.1)        # Sleep for 100ms (Total max wait: 1 second)
            ret, frame = cap.read()
        
            if ret and frame is not None:
                print(f"Recovered stream after {attempt + 1} soft retries!")
                recovered = True
                break
        if not recovered:
            print("Camera is truly disconnected. Initiating full reset...")
            # Only NOW do you do cap.release() and run your full reconnection routine
            cap.release()
            time.sleep(2)
            print('start reset')
            cap = robust_reconnect() 
            if cap is None: # this won't actually ever happen, we'll just get stuck in the reconnect loop.
                return None
            else:
                ret, frame = cap.read()
        # cap.release()
        # cap = camera_init()

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convertir l'image BGR (OpenCV) en RGB (Pygame)
    # frame_rgb = np.rot90(frame_rgb)  # Corriger l'orientation si nécessaire
    # frame_surface = pygame.surfarray.make_surface(frame_rgb)# Convertir l'image en surface Pygame
    frame_surface = pygame.image.frombuffer(frame_rgb.tobytes(), frame_rgb.shape[1::-1], "RGB")
    frame_surface = pygame.transform.scale(frame_surface, VIEW_PORT)
    screen.blit(frame_surface, (0, 0))
    return cap


def display_measure(screen, Temperature=MIN_TEMPERATURE_DEFAULT):
    """
    Affiche l'écran de mesure avec une image adaptée à la température.
    Fait boucler certaines images de flammes si la température dépasse le max.
    """

    number_of_frame = len(SMOKE_FRAMES_PATHS) + len(FLAMES_FRAMES_PATHS)
    temperatures = np.linspace(MIN_TEMPERATURE_VALUE, MAX_TEMPERATURE_VALUE, number_of_frame)
    index = min(range(number_of_frame), key=lambda i: abs(temperatures[i] - Temperature))

    if Temperature < MAX_TEMPERATURE_VALUE:
        if index < len(SMOKE_FRAMES_PATHS):
            screen.blit(smoke_images[index], SMOKE_FRAME_POS)
        else:
            screen.blit(flames_images[index - len(SMOKE_FRAMES_PATHS)], FLAME_FRAME_POS)
    else:
        # Choisir l’image à afficher selon l'écart de température
        delta_temp = Temperature - MAX_TEMPERATURE_VALUE
        frame_index = int(delta_temp // DEGREES_PER_FRAME) % LOOP_FLAME_COUNT
        last_flame_images = flames_images[-LOOP_FLAME_COUNT:]
        image_to_display = last_flame_images[frame_index]
        screen.blit(image_to_display, FLAME_FRAME_POS)

    display_text_values(screen, Temperature)
    screen.blit(empty_thermometer, THERMOMETER_POS)
    display_bars(screen, Temperature)


def display_text_values(screen, temperature):
    """
    Display the text values on the screen
    :param screen: the screen to display the text values on
    :param temperature: the temperature to display
    """

    # sub function to reduce code duplication
    def display_text(screen, text, pos, size, color):
        """
        sub function to display the text on the screen
        """
        font = pygame.font.Font(None, size)
        text = font.render(f"{text:.1f}°C", True, color)
        text = pygame.transform.rotate(text, -90)
        text_rect = text.get_rect(center=pos)
        screen.blit(text, text_rect)

    display_text(screen, temperature, TEMPERATURE_TEXT_POS, TEXT_SIZE, TEXT_COLOR)


def avg_batch(temperature_list, new_temp, previous_avg):
    """
    Ajoute une nouvelle température à la liste.
    Quand on atteint ROLLING_WINDOW_SIZE, on calcule la moyenne, on vide la liste,
    et on retourne la nouvelle moyenne.
    Sinon, on retourne la moyenne précédente.
    """
    temperature_list.append(new_temp)

    if len(temperature_list) >= ROLLING_WINDOW_SIZE:
        new_avg = sum(temperature_list) / len(temperature_list)
        temperature_list.clear()  # Réinitialise la liste pour le prochain batch
        return temperature_list, new_avg
    else:
        return temperature_list, previous_avg


def display_bars(screen, temperature=MIN_TEMPERATURE_VALUE):
    """
    Display the bar on the screen according to the values
    :param screen: the screen to display the bar on
    :param temperature: the voltage to display
    """

    def display_bar_from_values(screen, value, max_v, min_v, bar_image):
        """
        Affiche une barre horizontale selon une valeur entre min et max.
        La barre est remplie de gauche à droite.
        """
        bar_height = SIZE_THERMOMETER[1]

        # Calcul du pourcentage de remplissage
        fill_ratio = (value - min_v) / (max_v - min_v)
        fill_ratio = max(0, min(1, fill_ratio))  # clamp entre 0 et 1

        fill_width = int(fill_ratio * THERMO_FULL_SIZE)

        # Créer le rectangle de crop horizontal
        crop_rect = pygame.Rect(0, 0, fill_width, bar_height)
        cropped_bar = bar_image.subsurface(crop_rect).copy()

        screen.blit(cropped_bar, THERMOMETER_POS)

    display_bar_from_values(screen, temperature, MAX_TEMPERATURE_VALUE, MIN_TEMPERATURE_DEFAULT, full_thermometer)

