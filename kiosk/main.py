# Big Button: 2024 Colin Luoma
#
# License: GPL
"""Big Button"""
import sys
import _thread
import time
import machine
import network
import sdcard
import uos
import lib.urtc as urtc
import urequests as ur
import ujson
from machine import I2C, Pin, Timer
from lib.webserver import WebServer

"""
Button
handles debouncing and button led status
"""
class Button:
    DOWN = 0
    UP = 1

    def __init__(self, pin, led_pin, timeout=50):
        self.pin = pin
        self.led_pin = led_pin
        self.timeout = timeout
        self.debounce_timer = Timer(-1)
        self.is_timeout = False
        self.cur_value = pin.value()
        self.last_value = self.cur_value

    def _start_debounce_timer(self):
        self.debounce_timer.init(period=self.timeout, mode=Timer.ONE_SHOT,
                                 callback=self._cancel_timeout)

    def _cancel_timeout(self, _):
        self.is_timeout = not self.is_timeout

    def value(self):
        self.cur_value = self.pin.value()

        if self.cur_value == 0:
            self.led_pin.value(1)
        else:
            self.led_pin.value(0)

        if self.cur_value == 0 and self.last_value != 0 and not self.is_timeout:
            self.is_timeout = True
            self._start_debounce_timer()
            self.last_value = self.cur_value
            return self.DOWN
        elif self.cur_value == 1 and self.last_value != 1 and not self.is_timeout:
            self.is_timeout = True
            self._start_debounce_timer()
            self.last_value = self.cur_value
            return self.UP
        else:
            self.last_value = self.cur_value
            return self.UP
    
    def raw_value(self):
        return self.pin.value()


"""
Wifi
manages the wifi connection
"""
class Wifi:
    def __init__(self, ssid, password):
        self.wlan = None
        self.ssid = ssid
        self.password = password
        self.led_flash_timer = Timer(-1)
        self.connect_progress = 0
        self.connect_progress_dir = 1

    def inc_connect_button_lights(self):
        button_leds = [button_led_1, button_led_2, button_led_3, button_led_4]
        for i in range(4):
            if i <= self.connect_progress:
                button_leds[i].value(1)
            else:
                button_leds[i].value(0)
        self.connect_progress += self.connect_progress_dir
        if self.connect_progress == 3:
            self.connect_progress_dir = -1
        elif self.connect_progress == 0:
            self.connect_progress_dir = 1

    def flash_buttons_success(self):
        button_leds = [button_led_1, button_led_2, button_led_3, button_led_4]
        for bled in button_leds:
            bled.value(0)
        time.sleep(0.5)
        for i in range(3):
            button_led_1.value(1)
            time.sleep(0.5)
            button_led_1.value(0)
            time.sleep(0.5)
    
    def flash_buttons_failure(self):
        button_leds = [button_led_1, button_led_2, button_led_3, button_led_4]
        for bled in button_leds:
            bled.value(0)
        time.sleep(0.5)
        for i in range(3):
            button_led_4.value(1)
            time.sleep(0.5)
            button_led_4.value(0)
            time.sleep(0.5)

    def connect(self):
        tries = 3
        max_wait_per_try = 20
        self.wlan = network.WLAN(network.STA_IF)

        # Try to connect
        for i in range(tries):
            self.wlan.active(True)
            self.wlan.connect(self.ssid, self.password)

            # Wait for connect or fail
            max_wait = max_wait_per_try
            while max_wait > 0:
                if self.wlan.status() < 0 or self.wlan.status() == 3:
                    break
                max_wait -= 1
                print('waiting for connection...')
                self.inc_connect_button_lights()
                time.sleep(1)
            
            if self.wlan.status() != 3:
                self.wlan.disconnect()
                self.wlan.active(False)
            else:
                break

        # Handle connection error
        if self.wlan.status() == network.STAT_WRONG_PASSWORD:
            self.flash_buttons_failure()
            self.wlan.deinit()
            raise RuntimeError('network connection failed')
        elif self.wlan.status() != 3:
            self.flash_buttons_failure()
            self.wlan.deinit()
            raise RuntimeError('network connection failed')
        # Handle connection success
        else:
            print('connected')
            self.flash_buttons_success()
            status = self.wlan.ifconfig()
            print('ip = ' + status[0])

    def try_reconnect(self):
        if self.wlan == None:
            return
        if self.wlan.status() < 0 or self.wlan.status() >= 3:
            print("trying to reconnect...")
            self.wlan.disconnect()
            self.wlan.connect(self.ssid, self.password)
            if self.wlan.status() == 3:
                print('connected')
            else:
                print('failed')

    def wifi_status(self):
        if self.wlan == None:
            return None
        return self.wlan.status()


# Enum for current operation mode; OFFLINE will not use any wifi features
class Mode():
    ONLINE = 1
    OFFLINE = 2


# Globals
global bq
bq = []
CONFIG = {}
MODE = Mode.OFFLINE
# base url for API
API_BASE_URL = "http://bigbutton.cluoma.com"
#API_BASE_URL = "http://192.168.0.112:9898"


# GPIO pin setup
button_led_1 = Pin(10, Pin.OUT)
button_led_2 = Pin(11, Pin.OUT)
button_led_3 = Pin(12, Pin.OUT)
button_led_4 = Pin(13, Pin.OUT)

button_1 = Button(Pin(6, Pin.IN, Pin.PULL_UP), button_led_1)
button_2 = Button(Pin(7, Pin.IN, Pin.PULL_UP), button_led_2)
button_3 = Button(Pin(8, Pin.IN, Pin.PULL_UP), button_led_3)
button_4 = Button(Pin(9, Pin.IN, Pin.PULL_UP), button_led_4)

button_lock = _thread.allocate_lock()

# status led on back of box
status_led = Pin(14, Pin.OUT)
status_led.value(0)

# setup I2C and RTC
i2c = I2C(0, scl=Pin(5), sda=Pin(4))
rtc = urtc.PCF8523(i2c)

# init SPI for SD Card reading
cs = machine.Pin(17, machine.Pin.OUT)
spi = machine.SPI(0,
                  baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(18, machine.Pin.OUT),
                  mosi=machine.Pin(19, machine.Pin.OUT),
                  miso=machine.Pin(16, machine.Pin.OUT))

# init SD Card and mount fs
sd = sdcard.SDCard(spi, cs)
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")


def set_rtc_from_api():
    """
    Query the API to get the current time and set the RTC
    """
    try:
        r = ur.get(
            API_BASE_URL + "/api/time",
            headers={'accept': 'application/json'}
        )
        print(r.status_code)
        if r.status_code == 200:
            data = r.json()
            print(data)
            datetime = urtc.datetime_tuple(year=data['year'], month=data['month'], day=data['day'],
                                           hour=data['hour'], minute=data['minute'], second=data['second'])
            rtc.datetime(datetime)
        r.close()
    except:
        print("Failed to get time from server")


def append_press_to_queue(button):
    """
    Pushes a button press object to the button queue
    """
    global bq
    t = rtc.datetime()
    if t != None:
        timestamp = f"{t.year}-{t.month:02d}-{t.day:02d}T{t.hour:02d}:{t.minute:02d}:{t.second:02d}Z"
    else:
        timestamp = "1970-01-01T00:00:00Z"
    bq.append({"button": button, "timestamp": timestamp})

def print_button_press():
    """
    This function runs in a separate thread to read button presses
    """
    global bq
    button_lock.acquire()
    while True:
        if button_1.value() == 0:
            append_press_to_queue(1)
            print("button 1 pressed")
        if button_2.value() == 0:
            append_press_to_queue(2)
            print("button 2 pressed")
        if button_3.value() == 0:
            append_press_to_queue(3)
            print("button 3 pressed")
        if button_4.value() == 0:
            append_press_to_queue(4)
            print("button 4 pressed")


def sd_log_press(presses, file = "log.txt"):
    """
    Log a list of button presses to a file on the SD card
    """
    try:
        f_log = open("/sd/" + file, "a")
        #print(f"Logging {press['button']},{press['timestamp']}")
        print(f"Logging {len(presses)} button presses")
        for press in presses:
            f_log.write('{},{}\n'.format(press['button'], press['timestamp']))
        f_log.close()
    except FileNotFoundError:
        print("Cannot open 'log2.txt'")

def server_log_press(presses):
    """
    Log a list of button presses to the server by sending an HTTP POST request
    """
    ENDPOINT_URL = "/api/button_press/new"
    try:
        data = []
        for press in presses:
            data.append({'kiosk_id': 666, 'button': press['button'], 'clientdate': press['timestamp']})
        r = ur.post(
            API_BASE_URL + ENDPOINT_URL,
            headers={'content-type': 'application/json'},
            json=data
        )
        print(r.status_code)
        r.close()
    except:
        print("Failed to send press to server")
        wifi_conn.try_reconnect()

def load_config(config_file = "config.txt"):
    """
    Load the JSON format config file from the SD card
    """
    try:
        f = open("/sd/" + config_file, "r")
        try:
            return ujson.load(f)
        except ValueError:
            print("Improper formatting in config file: " + config_file)
            return {}
        finally:
            f.close()
    except FileNotFoundError:
        print("Cannot open '" + config_file + "'")
        return {}

def save_config(payload, config_file = "config.txt"):
    """
    Save the JSON format config file to the SD card
    """
    try:
        f = open("/sd/" + config_file, "w")
        ujson.dump(payload, f)
        f.close()
    except FileNotFoundError:
        print("Cannot open '" + config_file + "'")

def config_has_wifi_connection_parameters(config):
    """
    Check if wifi connection parameters are present in the config object
    """
    try:
        config['ssid']
        config['password']
        return True
    except KeyError:
        print("Missing required config parameter")
        return False

def run_webserver():
    """
    Runs a simple HTTP webserver to get wifi connection information from the user
    When connection details are obtained, update the config on the SD card and reset the pico
    """
    w = WebServer("ButtonKiosk", "123456789")
    # light up yellow light while running webserver
    button_led_2.value(1)
    # w.run() should return an object with ssid and password
    new_wifi = w.run()
    print("Got new wifi")
    CONFIG['ssid'] = new_wifi['ssid']
    CONFIG['password'] = new_wifi['password']
    save_config(CONFIG)
    machine.reset()

## Start program
button_lock.acquire()
# if button 4 is held down on boot, start in offline mode
# Offline mode only logs button presses to the SD card
if button_4.raw_value() == Button.DOWN:
    MODE = Mode.OFFLINE
    print("Running in offline mode")
else:
    MODE = Mode.ONLINE
    print("Running in online mode")

# load config and check if wifi connection details are present
CONFIG = load_config()
if MODE == Mode.ONLINE and not config_has_wifi_connection_parameters(CONFIG):
    run_webserver()

# shortcut to run the webserver when button 1 is held down
# this is useful to change wifi details
if MODE == Mode.ONLINE and button_1.raw_value() == Button.DOWN:
    run_webserver()

# connect to the wifi and set RTC
if MODE == Mode.ONLINE:
    wifi_conn = Wifi(CONFIG['ssid'], CONFIG['password'])
    try:
        wifi_conn.connect()
    except:
        print("could not connect to wifi")
        run_webserver()
    set_rtc_from_api()

# start polling for button presses in another thread
if button_2.raw_value() == Button.UP:
   button_lock.release()
   _thread.start_new_thread(print_button_press, ())

while True:
    item_group = []
    while len(bq) > 0 and len(item_group) <= 10:
        item_group.append(bq.pop(0))
    if len(item_group) > 0:
        sd_log_press(item_group)
        if MODE == Mode.ONLINE:
            server_log_press(item_group)
        item_group.clear()
