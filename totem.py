# coding=utf-8

execfile("config.py")

# BlinkM Codes
GOTO_RGB = 0x6e
FADE_RGB = 0x63
FADE_RANDOM = 0x43
PLAY_SCRIPT = 0x70
STOP_SCRIPT = 0x6f
SET_FADE_SPEED = 0x66
SET_TIME_ADJUST = 0x74
WRITE_SCRIPT_LINE = 0x57
READ_SCRIPT_LINE = 0x52
SET_SCRIPT_LENGTH = 0x4c
SET_BLINKM_ADDRESS = 0x41

PLAY_ONCE = 0x01
SCRIPT_ID = 0x00
RAINBOW_SEQUENCE = 0x0A

# Led parameters
FADE_SPEED = 60 # 1 = slow, 255 = instant
TIME_ADJUST = 0 # 0 = default

# FB
ORIGINAL_FB_LIKES = 0
PREVIOUS_FB_LIKES = 0
FB_LIKES = 0

# I2C ADDRESS
DEVICE_ADDRESS = 0x09
#DEVICE_ADDRESS = 0x00 # General Broadcast Call

import threading, time, smbus, urllib, json
from twython import Twython, TwythonStreamer
from pygame import mixer


#####################################
#       Just some display stuff     #
#####################################
import tty, sys, termios

class Debug():

  colors = {
    "NOTICE" : '\033[95m', # Pink
    "INFO" : '\033[94m', # Blue
    "SUCCESS" : '\033[92m', # Green
    "WARNING" : '\033[93m', # Yellowish
    "FAIL" : '\033[91m', # Red
    "ENDC" : '\033[0m',
  }

  @staticmethod
  def println(level, message):
    print "  # " + Debug.colors[level] + level + Debug.colors["ENDC"] + " : " + message

#####################################
#        Wrapper for FB likes       #
#####################################
class FBWrapper:

    def __init__(self,led):

        self.url = "http://graph.facebook.com/" + FB_PAGE + "/"
        self.led = led

        # Run the Pianette!
        self._timer = None
        self._timer_interval = 1 # 1 second
        self._timer_is_running = False

        # Start the timer thread that will cycle buffered states at each interval
        self.start_timer()
        Debug.println("INFO", "Thread started each %f sec" % self._timer_interval)

    def __del__(self):
        if hasattr(self, '_timer'):
            self.stop_timer()

    # Timer Methods
    def _run_timer(self):
        self._timer_is_running = False
        self.start_timer()
        self.check_fb()

    def start_timer(self):
        if not self._timer_is_running:
            self._timer = threading.Timer(self._timer_interval, self._run_timer)
            self._timer.start()
            self.is_running = True

    def stop_timer(self):
        self._timer.cancel()
        self._timer_is_running = False

    def check_fb(self):
        global FB_LIKES, ORIGINAL_FB_LIKES

        # For comparison
        PREVIOUS_FB_LIKES = FB_LIKES

        # Retrieve new like figure
        FB_LIKES = self.get_likes()
    
        if (FB_LIKES > PREVIOUS_FB_LIKES and PREVIOUS_FB_LIKES > 0):
        
            percentage = FB_LIKES_FACTOR * float(FB_LIKES - ORIGINAL_FB_LIKES) / ORIGINAL_FB_LIKES
            Debug.println("SUCCESS", "New Facebook like (Total: %s, up %d%%)" % (FB_LIKES, int(percentage*100)))
        
            # We have to recompute the color
            self.led.compute_color_for_percentage(percentage)
            # And play the light animation
            self.led.play_facebook()

    def get_likes(self):
        response = urllib.urlopen(self.url);
        data = json.loads(response.read())
        return data['likes']


#####################################
#      Wrapper for the Blink M      #
#####################################
class BlinkMWrapper():

  def __init__(self):

    # Get I2C bus
    self.bus = smbus.SMBus(1)
    Debug.println("INFO", "I2C Bus created")

    # Reset state
    self.reset_state()
    Debug.println("INFO", "BlinkM state reset")

    # If we need to upload a new script (TODO : parameter of the app)
    if False:
        self.upload_home_script()

  def reset_state(self):

    self.general_color = BASIC_COLOR
    self.animation_running = False

    # Stop current running script
    self.bus.write_byte(DEVICE_ADDRESS, STOP_SCRIPT) 

    # Stop current running script
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, FADE_RGB, OFF_COLOR) 

    # Set fade speed to fast, time adjust and blank light
    self.bus.write_byte_data(DEVICE_ADDRESS, SET_FADE_SPEED, FADE_SPEED)
    self.bus.write_byte_data(DEVICE_ADDRESS, SET_TIME_ADJUST, TIME_ADJUST)

  def stop_animation(self):

    self.animation_running = False
    self.bus.write_byte(DEVICE_ADDRESS, STOP_SCRIPT) # Stop current running script
    self.change_color()

  ## Reset the writeable script on the ThingM BlinkM
  def upload_home_script(self):

    ## Twitter Script
    line_nb = 0x00
    # Line 0 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 0, 4, FADE_RGB, 0x00, 0x00, 0x00])
    time.sleep(0.05)
    # Line 1 : Fade to twitter color
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 1, 5, FADE_RGB, 0x94, 0xE4, 0xE8])
    time.sleep(0.05)
    # Line 2 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 2, 4, FADE_RGB, 0x00, 0x00, 0x00])
    time.sleep(0.05)
    # Line 3 : Fade to twitter color
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 3, 5, FADE_RGB, 0x94, 0xE4, 0xE8])
    time.sleep(0.05)
    # Line 4 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 4, 10, FADE_RGB, 0x00, 0x00, 0x00])
    time.sleep(0.05)


    ## Facebook Script
    line_nb = 0x05
    # Line 5 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 0, 4, FADE_RGB, 0x00, 0x00, 0x00])
    time.sleep(0.05)
    # Line 6 : Fade to facebook color
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 1, 5, FADE_RGB, 0x6D, 0x8B, 0xC9])
    time.sleep(0.05)
    # Line 7 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 2, 4, FADE_RGB, 0x00, 0x00, 0x00])
    time.sleep(0.05)
    # Line 8 : Fade to facebook color
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 3, 5, FADE_RGB, 0x6D, 0x8B, 0xC9])
    time.sleep(0.05)
    # Line 9 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[0x00, line_nb + 4, 10, FADE_RGB, 0x00, 0x00, 0x00])
    time.sleep(0.05)

    ## Set script length
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, SET_SCRIPT_LENGTH, [SCRIPT_ID, 56, 0x00])
    time.sleep(0.05)

    Debug.println("SUCCESS", "Script %s written to EEPROM" % hex(SCRIPT_ID))

  def play_twitter(self):

    self.animation_running = True
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, PLAY_SCRIPT,[SCRIPT_ID, PLAY_ONCE, 0x00])
    time.sleep(0.75)
    self.stop_animation()

  def play_facebook(self):

    self.animation_running = True
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, PLAY_SCRIPT,[SCRIPT_ID, PLAY_ONCE, 0x05])
    time.sleep(0.75)
    self.stop_animation()

  def init_sequence(self):
    self.animation_running = True
    self.bus.write_byte_data(DEVICE_ADDRESS, SET_TIME_ADJUST, -10) # We play it quicker
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, PLAY_SCRIPT,[RAINBOW_SEQUENCE, PLAY_ONCE, 0x00])
    time.sleep(5)
    self.stop_animation()
    self.bus.write_byte_data(DEVICE_ADDRESS, SET_TIME_ADJUST, TIME_ADJUST) # And revert the timing adjustment back

    self.change_color()

  def compute_color_for_percentage(self, percentage):

    # Sanitizing
    if (percentage > 1):
        percentage = 1
    elif (percentage < 0):
        percentage = 0

    r_color = BASIC_COLOR[0]*(1 - percentage) + LIKED_COLOR[0]*percentage
    g_color = BASIC_COLOR[1]*(1 - percentage) + LIKED_COLOR[1]*percentage
    b_color = BASIC_COLOR[2]*(1 - percentage) + LIKED_COLOR[2]*percentage

    self.general_color = [int(r_color), int(g_color), int(b_color)]
    self.change_color()

  def change_color(self):
    if self.animation_running is False:
        self.bus.write_i2c_block_data(DEVICE_ADDRESS, FADE_RGB, self.general_color)


class MyStreamer(TwythonStreamer):
    def on_success(self, data):
        if 'text' in data:
            # Strip carriage / returns
            tweet = data['text'].encode('utf-8').replace(chr(10),' ').replace(chr(13),'')

            # Play the animation
            led.play_twitter()

            # And maybe the sound ...
            if HASHTAG_COMPLEMENTARY in data['text']:
                message = "New POWER tweet : " + tweet
                notification_sound.play() 
            else:
                message = "New tweet : " + tweet
            
            Debug.println("SUCCESS", message)
            

    def on_error(self, status_code, data):
        Debug.println("FAIL", "Error %d" % status_code)
        # self.disconnect()

Debug.println("NOTICE", "Starting application ...")

# Instantiate the LED via I2C
led = BlinkMWrapper()

# Creates an audio mixer for sound playing
Debug.println("INFO", "Creating audio mixer ...")
mixer.init()
Debug.println("INFO", "Creating sound : glass.wav")
notification_sound = mixer.Sound('sounds/glass.wav')

# Getting FB likes
fb = FBWrapper(led)
ORIGINAL_FB_LIKES = fb.get_likes()
Debug.println("INFO", "Getting original Facebook likes : %s" % str(ORIGINAL_FB_LIKES))

# Starting lights !
Debug.println("INFO", "Blinking lights !")
led.init_sequence()

# Get Twitter stream
stream = MyStreamer(APP_KEY, APP_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
Debug.println("NOTICE", "Starting Twitter stream for %s(%s)... " % (HASHTAG, HASHTAG_COMPLEMENTARY))
stream.statuses.filter(track=HASHTAG)
 