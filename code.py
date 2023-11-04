import rotaryio
import board
import digitalio
import usb_hid
import time

from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Поворот энкодера
dt = board.GP12
clk = board.GP11
encoder = rotaryio.IncrementalEncoder(clk, dt)
last_position = 0

# Нажатие на энкодер
sw = board.GP14
button = digitalio.DigitalInOut(sw)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP
button_state = None

cc = ConsumerControl(usb_hid.devices)

# States
MUTE_UNMUTE = 0
PLAY_PAUSE = 1

# Global variables
button_mode = None

# Global constants
DOUBLE_TAP_TIME_LIMIT = 0.5

def change_volume():
    global last_position
    current_position = encoder.position
    position_change = current_position - last_position
    # Прокрутили по часовой
    if position_change > 0:
        for _ in range(position_change):
            cc.send(ConsumerControlCode.VOLUME_INCREMENT)
    # Прокрутили против часовой
    elif position_change < 0:
        for _ in range(-position_change):
            cc.send(ConsumerControlCode.VOLUME_DECREMENT)      
    last_position = current_position


def detect_second_tap(first_tap_time):
    global button_mode
    
    second_tap_handled = False
    inner_button_state = None
    while(not second_tap_handled):
            second_tap_time = time.monotonic()
            time_dif = second_tap_time - first_tap_time
            # Нажата (button.value = 0)
            if not button.value:
                inner_button_state = "pressed"
            # Отпущена (button.value = 1)
            if button.value and inner_button_state == "pressed":
                button_mode = MUTE_UNMUTE
                second_tap_handled = True
            # Время для двойного нажатия прошло
            if time_dif > DOUBLE_TAP_TIME_LIMIT:
                button_mode = PLAY_PAUSE
                second_tap_handled = True

def change_mute_playback_state():
    global button_mode
    global DOUBLE_TAP_TIME_LIMIT
    global button_state
    
    # Check if button pressed
    # Нажата (button.value = 0) 
    if not button.value and button_state is None:
        button_state = "pressed"

    # Check if released after being pressed (Выполняем логику нажатия только после того как кнопка отпущена)
    # Отпущена (button.value = 1)
    if button.value and button_state == "pressed":
        first_tap_time = time.monotonic()
        detect_second_tap(first_tap_time)
        if button_mode == PLAY_PAUSE:
            cc.send(ConsumerControlCode.PLAY_PAUSE)
        else:
            cc.send(ConsumerControlCode.MUTE)
        button_state = None
        
while True:
    change_volume()
    change_mute_playback_state()

