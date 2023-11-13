import rotaryio
import board
import digitalio
import usb_hid
import time

from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Encoder rotation
encoder_dt = board.GP12
encoder_clk = board.GP11
encoder = rotaryio.IncrementalEncoder(encoder_clk, encoder_dt)

# Pressing the encoder
sw = board.GP14
encoder_button = digitalio.DigitalInOut(sw)
encoder_button.direction = digitalio.Direction.INPUT
encoder_button.pull = digitalio.Pull.UP

# Pressing the button for next track
next_scan_button = digitalio.DigitalInOut(board.GP1)
next_scan_button.direction = digitalio.Direction.INPUT
next_scan_button.pull = digitalio.Pull.UP

# Pressing the button for previous track
previous_scan_button = digitalio.DigitalInOut(board.GP6)
previous_scan_button.direction = digitalio.Direction.INPUT
previous_scan_button.pull = digitalio.Pull.UP

# HID
cc = ConsumerControl(usb_hid.devices)

# Global variables
encoder_last_position = 0
encoder_button_state = None
previous_button_state = None
next_button_state = None

# Global constants, States
DOUBLE_TAP_TIME_LIMIT = 0.5 # in seconds
ENCODER_WAS_PRESSED = True
NEXT_BUTTON_WAS_PRESSED = True
PREV_BUTTON_WAS_PRESSED = True


def encoder_change_volume():
    global encoder_last_position
    current_position = encoder.position
    position_change = current_position - encoder_last_position
    # Clockwise rotation
    if position_change > 0:
        for _ in range(position_change):
            cc.send(ConsumerControlCode.VOLUME_INCREMENT)
    # Counterclockwise rotation
    elif position_change < 0:
        for _ in range(-position_change):
            cc.send(ConsumerControlCode.VOLUME_DECREMENT)            
    encoder_last_position = current_position


def encoder_is_double_tapped(first_tap_time) -> bool:
    inner_button_state = None
    while True:
        time_dif = time.monotonic() - first_tap_time
        is_pressed = not encoder_button.value
        if is_pressed and inner_button_state is None:
            inner_button_state = ENCODER_WAS_PRESSED
        is_released = encoder_button.value
        if inner_button_state == ENCODER_WAS_PRESSED and is_released:
            return True
        if time_dif > DOUBLE_TAP_TIME_LIMIT:
            return False


def encoder_change_mute_or_playback_state():
    global encoder_button_state
    is_pressed = not encoder_button.value
    if is_pressed and encoder_button_state is None:
        encoder_button_state = ENCODER_WAS_PRESSED
    is_released = encoder_button.value
    if encoder_button_state == ENCODER_WAS_PRESSED and is_released:
        first_tap_time = time.monotonic()
        if encoder_is_double_tapped(first_tap_time):
            cc.send(ConsumerControlCode.MUTE)
        else:
            cc.send(ConsumerControlCode.PLAY_PAUSE)
        encoder_button_state = None
        

def buttons_previous_next_track():
    global next_button_state
    global previous_button_state
    is_next_pressed = not next_scan_button.value
    is_previous_pressed = not previous_scan_button.value

    if is_next_pressed and next_button_state is None:
        next_button_state = NEXT_BUTTON_WAS_PRESSED
    elif is_previous_pressed and previous_button_state is None:
        previous_button_state = PREV_BUTTON_WAS_PRESSED

    is_next_released = next_scan_button.value
    is_previous_released = previous_scan_button.value

    if (next_button_state is not None and is_next_released) or (previous_button_state is not None and is_previous_released):  # Fix the variable name here
        if next_button_state == NEXT_BUTTON_WAS_PRESSED:
            cc.send(ConsumerControlCode.SCAN_NEXT_TRACK)
        elif previous_button_state == PREV_BUTTON_WAS_PRESSED:
            cc.send(ConsumerControlCode.SCAN_PREVIOUS_TRACK)

        next_button_state = None
        previous_button_state = None

while True:
    encoder_change_volume()
    encoder_change_mute_or_playback_state()
    buttons_previous_next_track()

