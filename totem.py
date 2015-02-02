# coding=utf-8

execfile('config.py')

import ConfigParser
TOTEM_CONFIG = GLOBAL_PATH + '/config.ini'
config = ConfigParser.ConfigParser()
config.read(TOTEM_CONFIG)

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
PLAY_FOREVER = 0x00
SCRIPT_ID = 0x00
RAINBOW_SEQUENCE = 0x0A
CYAN_FLASH = 0x06
GREEN_FLASH = 0x04

# Led parameters
BOOT_FADE_SPEED = 0x0A # 1 = slow, 255 = instant
FADE_SPEED = 0x30 # 1 = slow, 255 = instant
BOOT_TIME_ADJUST = 0 # 0 = default
TIME_ADJUST = -12 # 0 = default

import multiprocessing, time

# FB
common = multiprocessing.Manager().dict()
common['ORIGINAL_FB_LIKES'] = 0
common['FB_LIKES'] = 0
common['ID'] = ID
common['FB_PAGE'] = config.get('TOTEM', 'FB_PAGE')
common['HASHTAG'] = config.get('TOTEM', 'HASHTAG')
common['HASHTAG_COMPLEMENTARY'] = config.get('TOTEM', 'HASHTAG_COMPLEMENTARY')
common['RELOAD_TWITTER'] = False
common['SAVE_DATA'] = False

# I2C ADDRESS
DEVICE_ADDRESS = 0x09
#DEVICE_ADDRESS = 0x00 # General Broadcast Call


#####################################
#       Just some display stuff     #
#####################################
import tty, sys, termios
import logging
logging.basicConfig(filename=GLOBAL_PATH + '/totem.log',level=logging.DEBUG)

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
    logging.info("(" + level + ") " + message)
    print "  # " + Debug.colors[level] + level + Debug.colors["ENDC"] + " : " + message

#####################################
#           Wifi procedure          #
#####################################
from wifi import Cell, Scheme
def connect_to_wifi():

    wifis = Cell.all('wlan0')

    # List comprehensions POOOOORN
    connectable_wifis = [(wifi,item[1]) for wifi in wifis for item in CONFIGURED_WIFIS if item[0] == wifi.ssid]

    if len(connectable_wifis) > 0:
      # Connect to the first one
      Debug.println("INFO", "Connecting to %s (%s)" % (connectable_wifis[0][0].ssid, connectable_wifis[0][1]))
      scheme = Scheme.for_cell('wlan0', 'totem_wifi', connectable_wifis[0][0], connectable_wifis[0][1])

      if Scheme.find('wlan0','totem_wifi') is None:
        Debug.println("INFO", "Saving interface")
        scheme.save()

      # Connect for real
      status = scheme.activate()

      if status:
          Debug.println("SUCCESS", "Connected to %s" % connectable_wifis[0][0].ssid)
          return True;
      else:
          return False
    else:
      return False

#####################################
#        Wrapper for WebServer      #
#####################################
from bottle import route, run, template, static_file, request, post

class BottleWrapper(multiprocessing.Process):

    @route('/static/<filepath:path>')
    def server_static(filepath):
        return static_file(filepath, root= GLOBAL_PATH + "/static")

    @post('/hashtag')
    def change_hashtag():
        new_hashtag = request.POST.get('hashtag')
        common['HASHTAG'] = new_hashtag
        common['RELOAD_TWITTER'] = True
        common['SAVE_DATA'] = True

    @post('/hashtag/complementary')
    def change_complementary_hashtag():
        new_complementary_hashtag = request.POST.get('complementary_hashtag')
        common['HASHTAG_COMPLEMENTARY'] = new_complementary_hashtag
        common['RELOAD_TWITTER'] = True
        common['SAVE_DATA'] = True

    @post('/facebook')
    def change_fb_page():
        new_page = request.POST.get('page')
        common['FB_PAGE'] = new_page
        common['ORIGINAL_FB_LIKES'] = FBWrapper.get_likes()
        common['SAVE_DATA'] = True

    @route('/')
    def index():

        percentage = round(float(common['FB_LIKES'] - common['ORIGINAL_FB_LIKES']) / common['ORIGINAL_FB_LIKES'] * 100, 2) # float

        tpl_vars = {
            "fb_likes" : common['FB_LIKES'],
            "instance_id": common['ID'],
            "fb_page" : common['FB_PAGE'],
            "hashtag" : common['HASHTAG'],
            "hashtag_complementary" : common['HASHTAG_COMPLEMENTARY'],
            "percentage" : percentage,
            "color": COLOR
        }

        return template('index', **tpl_vars)

    def run(self):
      Debug.println("NOTICE", "Process started for web server on port 8080")
      try:
        run(host='0.0.0.0', port=8080)
      finally:
        Debug.println("NOTICE", "Webserver process stopped.")


#####################################
#        Wrapper for FB likes       #
#####################################
import urllib, json

class FBWrapper(multiprocessing.Process):

    def run(self):
        Debug.println("NOTICE", "Process started for Facebook likes")

        common['ORIGINAL_FB_LIKES'] = FBWrapper.get_likes()
        Debug.println("INFO", "Getting original Facebook likes : %s" % str(common['ORIGINAL_FB_LIKES']))

        try:
            while (True):
                time.sleep(1)
                FBWrapper.check_fb()

        except KeyboardInterrupt:
            Debug.println("NOTICE", "Facebook process stopped.")

    @staticmethod
    def reinit():

        common['ORIGINAL_FB_LIKES'] = FBWrapper.get_likes()
        Debug.println("INFO", "Getting original Facebook likes : %s" % str(common['ORIGINAL_FB_LIKES']))

    @staticmethod
    def check_fb():
        # For comparison
        PREVIOUS_FB_LIKES = common['FB_LIKES']

        # Retrieve new like figure
        common['FB_LIKES'] = FBWrapper.get_likes()
    
        if (common['FB_LIKES'] > PREVIOUS_FB_LIKES and PREVIOUS_FB_LIKES > 0):
        
            percentage = FB_LIKES_FACTOR * float(common['FB_LIKES'] - common['ORIGINAL_FB_LIKES']) / common['ORIGINAL_FB_LIKES']
            Debug.println("SUCCESS", "New Facebook like (Total: %s, up %d%%)" % (common['FB_LIKES'], int(percentage*100/FB_LIKES_FACTOR)))
        
            # We have to recompute the color
            totem.compute_color_for_percentage(percentage)
            # And play the light animation
            totem.play_facebook()

    @staticmethod
    def get_likes():
        try:
            response = urllib.urlopen("http://graph.facebook.com/" + common['FB_PAGE'] + "/")
            data = json.loads(response.read())
            return data['likes']
        except IOError:
            return common['FB_LIKES'] # no changes


#####################################
#   Wrapper for the Physical stuff  #
#####################################
import smbus
import glob, random, os

# Creating sounds
sounds = glob.glob(GLOBAL_PATH + "/sounds/*.wav")
notification_sounds = list()
for s in sounds:
    Debug.println("INFO", "Creating sound : %s" % s)
    notification_sounds.append('aplay ' + GLOBAL_PATH + s + ' &')

startup_sound = 'aplay ' + GLOBAL_PATH + "/sounds/LetsGo.wav" + ' &'
facebook_sound = 'aplay ' + GLOBAL_PATH + "/sounds/Coin.wav" + ' &'
twitter_sound = 'aplay ' + GLOBAL_PATH + "/sounds/CuiCui.wav" + ' &'
power_sound = 'aplay ' + GLOBAL_PATH + "/sounds/Oohoo.wav" + ' &'
instagram_sound = 'aplay ' + GLOBAL_PATH + "/sounds/Shutter.wav" + ' &'

def play_power_sound():
    os.system(twitter_sound)
    os.system(power_sound)

def play_startup_sound():
    os.system(startup_sound)

def play_facebook_sound():
    os.system(facebook_sound)

def play_twitter_sound():
    os.system(twitter_sound)

def play_instagram_sound():
    os.system(instagram_sound)


class TotemWrapper():

  def __init__(self):

    # Constants for script

    self.on_time = 24
    self.off_time = 16
    self.last_off_time = 10
    self.script_length = 0.03333 * (2*(self.on_time + TIME_ADJUST) + 2*(self.off_time + TIME_ADJUST) + (self.last_off_time + TIME_ADJUST))

    # Get I2C bus
    self.bus = smbus.SMBus(1)
    Debug.println("INFO", "I2C Bus created")

    # Reset state
    self.reset_state()
    Debug.println("INFO", "BlinkM state reset")

    # If we need to upload a new script (TODO : parameter of the app)
    if 1 < len(sys.argv) and sys.argv[1] == "--upload-script":
        self.upload_home_script()

  def reset_state(self):

    self.general_color = BASIC_COLOR
    self.animation_running = False

    # Stop current running script
    self.bus.write_byte(DEVICE_ADDRESS, STOP_SCRIPT) 

    # Color to Black
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, FADE_RGB, OFF_COLOR) 

    # Set fade speed to fast, time adjust and blank light
    self.bus.write_byte_data(DEVICE_ADDRESS, SET_FADE_SPEED, BOOT_FADE_SPEED)
    self.bus.write_byte_data(DEVICE_ADDRESS, SET_TIME_ADJUST, BOOT_TIME_ADJUST)

  def stop_animation(self):

    self.animation_running = False
    self.bus.write_byte(DEVICE_ADDRESS, STOP_SCRIPT) # Stop current running script
    self.change_color()

  ## Reset the writeable script on the ThingM BlinkM
  def upload_home_script(self):

    ## Twitter Script
    line_nb = 0x00
    # Line 0 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 0, self.off_time, FADE_RGB] + OFF_COLOR)
    time.sleep(0.05)
    # Line 1 : Fade to twitter color
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 1, self.on_time, FADE_RGB] + TWITTER_BLINK_COLOR)
    time.sleep(0.05)
    # Line 2 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 2, self.off_time, FADE_RGB] + OFF_COLOR)
    time.sleep(0.05)
    # Line 3 : Fade to twitter color
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 3, self.on_time, FADE_RGB] + TWITTER_BLINK_COLOR)
    time.sleep(0.05)
    # Line 4 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 4, self.last_off_time, FADE_RGB] + OFF_COLOR)
    time.sleep(0.05)


    ## Facebook Script
    line_nb = 0x05
    # Line 5 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 0, self.off_time, FADE_RGB] + OFF_COLOR)
    time.sleep(0.05)
    # Line 6 : Fade to facebook color
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 1, self.on_time, FADE_RGB] + FACEBOOK_BLINK_COLOR)
    time.sleep(0.05)
    # Line 7 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 2, self.off_time, FADE_RGB] + OFF_COLOR)
    time.sleep(0.05)
    # Line 8 : Fade to facebook color
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 3, self.on_time, FADE_RGB] + FACEBOOK_BLINK_COLOR)
    time.sleep(0.05)
    # Line 9 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 4, self.last_off_time, FADE_RGB] + OFF_COLOR)
    time.sleep(0.05)


    ## Instagram Script
    line_nb = 0x0A
    # Line 5 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 0, self.off_time, FADE_RGB] + OFF_COLOR)
    time.sleep(0.05)
    # Line 6 : Fade to facebook color
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 1, self.on_time, FADE_RGB] + INSTAGRAM_BLINK_COLOR)
    time.sleep(0.05)
    # Line 7 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 2, self.off_time, FADE_RGB] + OFF_COLOR)
    time.sleep(0.05)
    # Line 8 : Fade to facebook color
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 3, self.on_time, FADE_RGB] + INSTAGRAM_BLINK_COLOR)
    time.sleep(0.05)
    # Line 9 : Fade to nothing
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, WRITE_SCRIPT_LINE,[SCRIPT_ID, line_nb + 4, self.last_off_time, FADE_RGB] + OFF_COLOR)
    time.sleep(0.05)

    ## Set script length
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, SET_SCRIPT_LENGTH, [SCRIPT_ID, 6*self.on_time + 6*self.off_time + 3*self.last_off_time, 0x00])
    time.sleep(0.05)

    Debug.println("SUCCESS", "Script %s written to EEPROM" % hex(SCRIPT_ID))

  def play_twitter(self):

    self.animation_running = True
    play_twitter_sound()
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, PLAY_SCRIPT,[SCRIPT_ID, PLAY_ONCE, 0x00])
    time.sleep(self.script_length)
    self.stop_animation()

  def play_power_twitter(self):

    self.animation_running = True
    play_power_sound()
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, PLAY_SCRIPT,[SCRIPT_ID, PLAY_ONCE, 0x00])
    time.sleep(self.script_length)
    self.stop_animation()

  def play_facebook(self):

    self.animation_running = True
    play_facebook_sound()
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, PLAY_SCRIPT,[SCRIPT_ID, PLAY_ONCE, 0x05])
    time.sleep(self.script_length)
    self.stop_animation()

  def play_instagram(self):

    self.animation_running = True
    play_instagram_sound()
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, PLAY_SCRIPT,[SCRIPT_ID, PLAY_ONCE, 0x0A])
    time.sleep(self.script_length)
    self.stop_animation()

  def play_error(self):

    self.animation_running = True
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, PLAY_SCRIPT,[0x03, 0x00, 0x00])

  def looking_for_wifi(self):
    self.animation_running = True
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, PLAY_SCRIPT,[CYAN_FLASH, PLAY_FOREVER, 0x00])

  def wifi_found(self):
    self.animation_running = True
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, PLAY_SCRIPT,[GREEN_FLASH, PLAY_ONCE * 3, 0x00])
    time.sleep(1)

  def init_sequence(self):
    self.animation_running = True
    play_startup_sound()
    self.bus.write_i2c_block_data(DEVICE_ADDRESS, PLAY_SCRIPT,[RAINBOW_SEQUENCE, PLAY_ONCE, 0x00])
    time.sleep(4.5)
    self.stop_animation()

    # Real stuff now
    self.bus.write_byte_data(DEVICE_ADDRESS, SET_FADE_SPEED, FADE_SPEED)
    self.bus.write_byte_data(DEVICE_ADDRESS, SET_TIME_ADJUST, TIME_ADJUST)

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

#####################################
#     Twitter Stream API wrapper    #
#####################################
from twython import Twython, TwythonStreamer

class MyStreamer(TwythonStreamer):
    def on_success(self, data):
        if 'text' in data:
            # Strip carriage / returns
            tweet = data['text'].encode('utf-8').replace(chr(10),' ').replace(chr(13),'')

            # And maybe the sound ...
            if common['HASHTAG_COMPLEMENTARY'] in data['text']:
                message = "New POWER tweet : " + tweet
                totem.play_power_twitter()
            else:
                message = "New tweet : " + tweet
                totem.play_twitter()
            
            Debug.println("SUCCESS", message)
            

    def on_error(self, status_code, data):
        Debug.println("FAIL", "Error %d" % status_code)
        totem.play_error()
        #self.disconnect()


class TwitterWrapper(multiprocessing.Process):

    def run(self):
      Debug.println("NOTICE", "Process started for Twitter stream %s(%s)... " % (common['HASHTAG'], common['HASHTAG_COMPLEMENTARY']))
      stream = MyStreamer(APP_KEY, APP_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
      try:
        stream.statuses.filter(track=common['HASHTAG'])
      except KeyboardInterrupt:
        Debug.println("NOTICE", "Twitter process stopped.")
      except ConnectionError:
        common['RELOAD_TWITTER'] = True # Will it work ? - Restart the polling process


#####################################
#    Instagram Stream API wrapper   #
#####################################
class InstagramWrapper(multiprocessing.Process):

    def run(self):

        # Get latest min_id
        response = urllib.urlopen("https://api.instagram.com/v1/tags/" + common['HASHTAG'][1:] + "/media/recent?client_id=" + CLIENT_ID)
        data = json.loads(response.read())
        InstagramWrapper.min_id = int(data['pagination']['min_tag_id'])
        Debug.println("INFO", "Getting original Instagram min_id : %d" % InstagramWrapper.min_id)

        try:
            while (True):
                time.sleep(1.1)
                InstagramWrapper.check_tags()

        except KeyboardInterrupt:
            Debug.println("NOTICE", "Instagram process stopped.")

    @staticmethod
    def check_tags():
        global CLIENT_ID
        # get recent
        try:
            response = urllib.urlopen("https://api.instagram.com/v1/tags/" + common['HASHTAG'][1:] + "/media/recent?count=1&client_id=" + CLIENT_ID + ("&min_id=%d" % InstagramWrapper.min_id))
            data = json.loads(response.read())
        except IOError:
            data = None
        
        if data is not None and len(data['data']) > 0:
            # Play the animation
            totem.play_instagram()
            Debug.println("SUCCESS", "New Instagram (%s) : %s " % (data['data'][0]['id'], data['data'][0]['images']['standard_resolution']['url']))
            InstagramWrapper.min_id = int(data['pagination']['min_tag_id'])

Debug.println("SUCCESS", "Starting application ...")

# Instantiate the LED via I2C
totem = TotemWrapper()
totem.looking_for_wifi()

# Try to connect to a configured wifi
good_to_go = connect_to_wifi()
if good_to_go == False:
    Debug.println("FAIL", "Could not connect to any configured wifi, exiting ...")
    sys.exit(0)

totem.wifi_found()

# Getting FB likes
fb_process = FBWrapper();
fb_process.start()

# Start web server
webserver_process = BottleWrapper()
webserver_process.start()

# Get Twitter stream
twitter_process = TwitterWrapper()
twitter_process.start()

# Get Instagram stream
instagram_process = InstagramWrapper()
instagram_process.start()

# Wait for processes to start 
time.sleep(2)

# Starting lights and sound !
Debug.println("SUCCESS", "Blinking lights ! Ready to start !")
totem.init_sequence()

time.sleep(30)

try:
    while(True):

        if common['RELOAD_TWITTER'] == True:
            common['RELOAD_TWITTER'] = False
            twitter_process.terminate()
            twitter_process.join()
            Debug.println("NOTICE", "Twitter process stopped.")
            Debug.println("NOTICE", "Waiting 2 seconds before restarting ...")
            time.sleep(2)
            twitter_process = TwitterWrapper()
            twitter_process.start()

        if common['SAVE_DATA'] == True:
            Debug.println("NOTICE", "Saving data back to config.ini file.")
            common['SAVE_DATA'] = False
            config.set('TOTEM', 'HASHTAG', common['HASHTAG'])
            config.set('TOTEM', 'HASHTAG_COMPLEMENTARY', common['HASHTAG_COMPLEMENTARY'])
            config.set('TOTEM', 'FB_PAGE', common['FB_PAGE'])
            with open(TOTEM_CONFIG, 'w') as configfile:
                config.write(configfile)

except KeyboardInterrupt:
    # Stop current running script
    totem.reset_state()

    Debug.println("NOTICE", "Finishing threads ...")

    try:
        webserver_process.join(1)
    except AssertionError:
        pass
    try:
        twitter_process.join(1)
    except AssertionError:
        pass
    try:
        fb_process.join(1)
    except AssertionError:
        pass

    time.sleep(2)
    Debug.println("SUCCESS", "All Threads terminated, exiting ...")
    sys.exit(0)

