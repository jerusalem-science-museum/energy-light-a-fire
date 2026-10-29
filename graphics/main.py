"""
File: main.py
Purpose: Main file for the Light a Fire UI
"""
import math
import time

from display import *
from arduino import *
from logs import *


def Quit_pygame(cap):
    if cap:
        cap.release()
    pygame.quit()
    exit()


def main():
    """
    The main function for the Light a Fire UI
    """
    # camera setup
    cap = camera_init()

    # pygame setup
    pygame.display.set_caption("Light a Fire")
    screen = pygame.display.set_mode(VIEW_PORT, pygame.FULLSCREEN)
    # screen = pygame.display.set_mode(VIEW_PORT)
    pygame.mouse.set_visible(False)
    
    clock = pygame.time.Clock()  # for fps limit

    # initial values for th
    temperature = MIN_TEMPERATURE_DEFAULT

    # logging setup - log into a file called log.txt in the folder /logs with the format: [TIME] - [MESSAGE], if the file exists, append to it, if not, create it, if it exceeds 1MB, create a new file with a number suffix (before the .txt) and continue logging to it (e.g., log1.txt, log2.txt, etc.)
    logger = get_logger()
    logger.info("Starting Light a Fire UI")
    state = "idle"
    last_peak_temperature = None
    previous_window = None
    current_window = None

    # arduino setup
    arduino_port = find_arduino_port(logger=logger)  # find the serial port
    ser = open_serial_connection(arduino_port, logger=logger)  # Open the serial port
    time.sleep(1)  # wait for the arduino to reset
    last_time_tried_to_connect = time.time()  # for not trying to connect too often

    running = True
    sensor_off = False
    # stats collected while the sensor is off, for diagnosing the disconnects
    sensor_off_since = 0.0
    bad_lines_count = 0
    bad_analog_min = 0
    bad_analog_max = 0

    temperature_to_display = MIN_TEMPERATURE_DEFAULT

    while running:

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                Quit_pygame(cap)

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    Quit_pygame(cap)

                if event.key == pygame.K_UP:
                    temperature_to_display = min(temperature_to_display + 0.2, MAX_TEMPERATURE_DEFAULT)

                if event.key == pygame.K_DOWN:
                    temperature_to_display = max(temperature_to_display - 0.2, MIN_TEMPERATURE_DEFAULT)

        data_from_arduino = read_line(ser, logger=logger)  # try to read from arduino
        if data_from_arduino == SERIAL_ERROR:  # if arduino WAS connected at start, but now failed to read:
            print("Arduino disconnected. Trying to reconnect to Arduino...")
            logger.info("Arduino disconnected. Trying to reconnect to Arduino...")

            ser = None
            temperature_to_display = MIN_TEMPERATURE_DEFAULT

        # if arduino was connecetd at start, but now failed to read, try to reconnect
        if not ser and time.time() - last_time_tried_to_connect > RECONNECT_INTERVAL:
            arduino_port = find_arduino_port(logger=logger)  # find the serial port
            ser = open_serial_connection(arduino_port, logger=logger)  # Open the serial port
            last_time_tried_to_connect = time.time()  # update the last time tried to connect

        if data_from_arduino and data_from_arduino != SERIAL_ERROR:  # if data is vaild
            # print(data_from_arduino)
            temperature, sensor_analogread, error = parse_data(data_from_arduino, logger=logger)
            # print(f"parsed: pressure {temperature} sensor_analogread {sensor_analogread} error {error}")
            if not error and (sensor_analogread >= 1000 or not math.isfinite(temperature)):
                if not sensor_off:
                    msg = f"the sensor is disconected, raw line: {data_from_arduino!r}"
                    print(msg)
                    logger.info(msg)
                    sensor_off = True
                    sensor_off_since = time.time()
                    bad_lines_count = 0
                    bad_analog_min = bad_analog_max = sensor_analogread
                bad_lines_count += 1
                bad_analog_min = min(bad_analog_min, sensor_analogread)
                bad_analog_max = max(bad_analog_max, sensor_analogread)
                temperature_to_display = TEMPERATURE_SENSOR_OFF
                error = PARSE_ERROR
            elif not error and sensor_off:
                msg = (f"the sensor is reconnected after {time.time() - sensor_off_since:.2f}s, "
                       f"{bad_lines_count} bad lines, analog min {bad_analog_min} max {bad_analog_max}, "
                       f"raw line: {data_from_arduino!r}")
                print(msg)
                logger.info(msg)
                sensor_off = False
            if not error:
                temperature_to_display = temperature
                state, last_peak_temperature = log_temperature(logger, temperature_to_display, state,
                                                               last_peak_temperature)
        # state, last_peak_temperature = log_temperature(logger, temperature, state, last_peak_temperature=None)
        screen.fill(BLACK)  # reset screen
        cap = camera_setup(screen, cap)
        if cap is None:
            Quit_pygame(cap)
        display_measure(screen, Temperature=temperature_to_display)  # render the screen
        pygame.display.flip()
        clock.tick(FPS)

    Quit_pygame(cap)


if __name__ == "__main__":
    main()
