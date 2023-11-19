import rotaryio
import board
import digitalio
import usb_hid
import time
import busio
import lcd
import i2c_pcf8574_interface
import random

from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

from lcd import LCD, CursorMode
from i2c_pcf8574_interface import I2CPCF8574Interface

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
WAS_PRESSED = True



i2c = busio.I2C(scl=board.GP17, sda=board.GP0)
address = 0x27


i2c = i2c_pcf8574_interface.I2CPCF8574Interface(i2c, address)
lcd = lcd.LCD(i2c, num_rows=2, num_cols=16)

lcd.set_display_enabled(True)


last_blink_time = -1  
lcd_has_value = False
lcd_value = 'fdffd'

is_answer = False
is_waiting = True
is_thinking = False
wait_lcd_duration = 2

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


def is_double_tapped(button, first_tap_time) -> bool:
    inner_button_state = None
    while True:
        time_dif = time.monotonic() - first_tap_time
        is_pressed = not button.value
        if is_pressed and inner_button_state is None:
            inner_button_state = WAS_PRESSED
        is_released = button.value
        if inner_button_state == WAS_PRESSED and is_released:
            return True
        if time_dif > DOUBLE_TAP_TIME_LIMIT:
            return False


def encoder_change_mute_or_playback_state():
    global encoder_button_state
    is_pressed = not encoder_button.value
    if is_pressed and encoder_button_state is None:
        encoder_button_state = WAS_PRESSED
    is_released = encoder_button.value
    if encoder_button_state == WAS_PRESSED and is_released:
        first_tap_time = time.monotonic()
        if is_double_tapped(encoder_button, first_tap_time):
            cc.send(ConsumerControlCode.MUTE)
        else:
            cc.send(ConsumerControlCode.PLAY_PAUSE)
        encoder_button_state = None



def next_track_button():
    global next_button_state
    is_next_pressed = not next_scan_button.value
    if is_next_pressed and next_button_state is None:
        next_button_state = WAS_PRESSED
    is_next_released = next_scan_button.value
    if next_button_state == WAS_PRESSED and is_next_released:
        first_tap_time = time.monotonic()
        if is_double_tapped(next_scan_button, first_tap_time):
            magic_8_ball()
        else:
            cc.send(ConsumerControlCode.SCAN_NEXT_TRACK)
        next_button_state = None


def previous_track_button():
    global previous_button_state
    is_previous_pressed = not previous_scan_button.value
    if is_previous_pressed and previous_button_state is None:
        previous_button_state = WAS_PRESSED
    is_previous_released = previous_scan_button.value
    if previous_button_state == WAS_PRESSED and is_previous_released:
        cc.send(ConsumerControlCode.SCAN_PREVIOUS_TRACK)
        previous_button_state = None

def magic_8_ball():
    lcd.clear()
    answers = [
        "It is certain.",
               "It is decidedly so.",
               "Without a doubt.",
               "Yes definitely.",
               "You may rely on it.",
               "As I see it, yes.",
               "Most likely.", "Outlook good.",
               "Yes.", "Signs point to yes.",
               "Reply hazy",
                "try again.",
               "Ask again later.",
               "Better not tell you now.",
               "Cannot predict now.",
               "Concentrate and ask again.",
               "Don't count on it.",
               "My reply is no.",
               "My sources say no.",
               "Outlook not so good.",
               "Very doubtful."
        ]
    answer_number = random.randint(0, len(answers) - 1)
    lcd_print_animate(answers[answer_number])

def lcd_print_animate(value):
    global lcd_value
    global lcd_has_value
    global last_blink_time
    global wait_lcd_duration
    global is_answer
    global is_waiting
    global is_thinking
    
    is_answer = False
    is_waiting = False
    is_thinking = False
    
    lcd_value = value
    last_blink_time = time.monotonic()
    lcd_has_value = True
    wait_lcd_duration = random.randint(1, 5)
  
  
  
def lcd_animate_work():
    global is_answer
    global is_waiting
    global is_thinking
    global lcd_has_value
    global lcd_value
    global last_blink_time
    
    BLINK_ON_DURATION = 7
    
    if lcd_has_value:
        if time.monotonic() - last_blink_time >= BLINK_ON_DURATION + wait_lcd_duration:          
            lcd.clear()
            lcd_has_value = False
            is_answer = False
        elif time.monotonic() - last_blink_time >= wait_lcd_duration:         
            if not is_answer:
                lcd.clear()
                lcd.print(lcd_value)
                is_answer = True
                is_thinking = False
        else:
            if not is_thinking:
                lcd.clear()
                lcd.print("I'm thinking..\nWait...")
                is_thinking = True
                is_waiting = False
    else:
        if not is_waiting:
            lcd.clear()
            lcd.print("=====Ask me=====")
            is_waiting = True
                
                
try:
    lcd.print("====Welcome=========Ask me!=====")
       
    while True:
        encoder_change_volume()
        encoder_change_mute_or_playback_state()
        next_track_button()
        previous_track_button()
        lcd_animate_work()      
        
        
finally:
    lcd.set_backlight(False)
    lcd.set_display_enabled(False)
    lcd.close()
