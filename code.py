import rotaryio
import board
import digitalio
import usb_hid
import time

from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Encoder rotation
dt = board.GP12
clk = board.GP11
encoder = rotaryio.IncrementalEncoder(clk, dt)

# Pressing the encoder
sw = board.GP14
encoder_button = digitalio.DigitalInOut(sw)
encoder_button.direction = digitalio.Direction.INPUT
encoder_button.pull = digitalio.Pull.UP

# HID
cc = ConsumerControl(usb_hid.devices)

# States
MUTE_UNMUTE = 0
PLAY_PAUSE = 1
WAS_PRESSED = 1

# Global variables
last_position = 0
encoder_button_state = None
encoder_button_mode = None

# Global constants
DOUBLE_TAP_TIME_LIMIT = 0.5 # in seconds

def change_volume():
    global last_position
    current_position = encoder.position
    position_change = current_position - last_position
    
    # Clockwise rotation
    if position_change > 0:
        for _ in range(position_change):
            cc.send(ConsumerControlCode.VOLUME_INCREMENT)
    # Counterclockwise rotation
    elif position_change < 0:
        for _ in range(-position_change):
            cc.send(ConsumerControlCode.VOLUME_DECREMENT)            
    last_position = current_position


def detect_second_tap(first_tap_time):
    global encoder_button_mode
    second_tap_handled = False
    inner_button_state = None
    
    while not second_tap_handled:
        second_tap_time = time.monotonic()
        time_dif = second_tap_time - first_tap_time
        
        is_pressed = not encoder_button.value
        if is_pressed and inner_button_state is None:
            inner_button_state = WAS_PRESSED
        is_released = encoder_button.value
        if is_released and inner_button_state == WAS_PRESSED:
            encoder_button_mode = MUTE_UNMUTE
            second_tap_handled = True
        if time_dif > DOUBLE_TAP_TIME_LIMIT:
            encoder_button_mode = PLAY_PAUSE
            second_tap_handled = True


def change_mute_or_playback_state():
    global DOUBLE_TAP_TIME_LIMIT
    global encoder_button_state
    global encoder_button_mode
    
    is_pressed = not encoder_button.value
    if is_pressed and encoder_button_state is None:
        encoder_button_state = WAS_PRESSED
    is_released = encoder_button.value
    if is_released and encoder_button_state == WAS_PRESSED:
        first_tap_time = time.monotonic()
        detect_second_tap(first_tap_time)
        if encoder_button_mode == PLAY_PAUSE:
            cc.send(ConsumerControlCode.PLAY_PAUSE)
        else:
            cc.send(ConsumerControlCode.MUTE)
        encoder_button_state = None


while True:
    change_volume()
    change_mute_or_playback_state()