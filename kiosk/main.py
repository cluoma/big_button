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
from webserver import WebServer

"""Button - handles debouncing and button led status"""
class Button:
    def __init__(self, pin, led_pin, timeout=50):
        self.pin = pin
        self.led_pin = led_pin
        self.timeout = timeout
        self.debounce_timer = Timer(-1)
        self.is_timeout = False
        self.cur_value = pin.value()
        self.last_value = self.value

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
            return 0
        elif self.cur_value == 1 and self.last_value != 1 and not self.is_timeout:
            self.is_timeout = True
            self._start_debounce_timer()
            self.last_value = self.cur_value
            return 1
        else:
            self.last_value = self.cur_value
            return 1

class Wifi:
    def __init__(self, ssid, password):
        self.wlan = None
        self.ssid = ssid
        self.password = password

    def connect(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)

        # Wait for connect or fail
        max_wait = 60
        while max_wait > 0:
            if self.wlan.status() < 0 or self.wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)

        # Handle connection error
        if self.wlan.status() != 3:
            raise RuntimeError('network connection failed')
        else:
            print('connected')
            status_led.value(1)
            led_flash = Timer(-1)
            led_flash.init(mode=Timer.ONE_SHOT, period=5000, callback=self.turn_off_status_led)
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

    def turn_off_status_led(self, t):
        status_led.value(0)
        t.deinit()


# button queue
global bq
CONFIG = {}

# GPIO pin setup
button_led_1 = Pin(10, Pin.OUT)
button_led_2 = Pin(11, Pin.OUT)
button_led_3 = Pin(12, Pin.OUT)
button_led_4 = Pin(13, Pin.OUT)

button_1 = Button(Pin(6, Pin.IN, Pin.PULL_UP), button_led_1)
button_2 = Button(Pin(7, Pin.IN, Pin.PULL_UP), button_led_2)
button_3 = Button(Pin(8, Pin.IN, Pin.PULL_UP), button_led_3)
button_4 = Button(Pin(9, Pin.IN, Pin.PULL_UP), button_led_4)

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
            "http://bigbutton.cluoma.com/time",
            # "http://192.168.0.112:9898/api/time",
            headers={'accept': 'application/json'}
        )
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
    timestamp = f"{t.year}-{t.month:02d}-{t.day:02d}T{t.hour:02d}:{t.minute:02d}:{t.second:02d}Z"
    bq.append({"button": button, "timestamp": timestamp})

def print_button_press():
    """
    This function runs in a separate thread to read button presses
    """
    global bq

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


def sd_log_press(press):
    # log a button press to a file on the SD card
    try:
        f_log = open("/sd/log2.txt", "a")
        print(f"Logging {press['button']},{press['timestamp']}")
        f_log.write('{},{}\n'.format(press['button'], press['timestamp']))
        f_log.close()
    except FileNotFoundError:
        print("Cannot open 'log2.txt'")

def server_log_press(press):
    # send an http POST to button logging API
    try:
        r = ur.post(
            "http://bigbutton.cluoma.com/api/button_press/new",
            # "http://192.168.0.112:9898/api/button_press/new",
            headers={'content-type': 'application/json'},
            json=[{'kiosk_id': 666, 'button': press['button'], 'clientdate': press['timestamp']}]
        )
        print(r.status_code)
        r.close()
    except:
        print("Failed to send press to server")
        wifi_conn.try_reconnect()

def load_config(config_file = "config.txt"):
    # load config parameters from file
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


## Start program

#w = WebServer("test", "123456789")
#w.run()

# load config and check we got everything
CONFIG = load_config()
try:
    CONFIG['ssid']
    CONFIG['password']
except KeyError:
    print("Missing required config parameter")
    sys.exit(1)

# connect to the wifi
wifi_conn = Wifi(CONFIG['ssid'], CONFIG['password'])
wifi_conn.connect()

set_rtc_from_api()

bq = []
_thread.start_new_thread(print_button_press, ())

while True:
    if len(bq) > 0:
        item = bq.pop(0)
        sd_log_press(item)
        server_log_press(item)
