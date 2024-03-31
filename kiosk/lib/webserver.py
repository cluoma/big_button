import machine
import socket
import network
import ujson
import time

def form_page():
    html = """
<!DOCTYPE html>
<html>
<body>

<h2>Enter WiFi Connection Information</h2>

<form action="/set_wifi">
  <label for="ssid">SSID:</label><br>
  <input type="text" id="ssid" name="ssid"><br>
  <label for="password">Password:</label><br>
  <input type="text" id="password" name="password"><br><br>
  <input type="submit" value="Submit">
</form> 

<p>After submitting connection information, the Kiosk will reset and attempt to connect to the given WiFi network.</p>
<p>If the Kiosk is unable to connect, it will start its own access point again to accept different connection information.</p>
<p>By holding the 'GREEN' button when pluggin the Kiosk, the access point will be started to change the current connection information.</p>

</body>
</html>
"""
    return html

def thank_you_page():
    html = """
<!DOCTYPE html>
<html>
<body>

<h2>Thank you! Resetting the Kiosk!</h2>

</body>
</html>
"""
    return html

def unquote(string):
    """unquote('abc%20def') -> b'abc def'.

    Note: if the input is a str instance it is encoded as UTF-8.
    This is only an issue if it contains unescaped non-ASCII characters,
    which URIs should not.
    """
    if not string:
        return b''

    if isinstance(string, str):
        string = string.encode('utf-8')

    # account for '+' in string
    string = string.replace(b'+', b' ')

    bits = string.split(b'%')
    if len(bits) == 1:
        return string

    res = bytearray(bits[0])
    append = res.append
    extend = res.extend

    for item in bits[1:]:
        try:
            append(int(item[:2], 16))
            extend(item[2:])
        except KeyError:
            append(b'%') # type: ignore
            extend(item)

    return bytes(res)

def parse_query_string(data):
    """
    Parse query string and return an object of key-value pairs
    """
    ret = {}

    start = str(data).find("/")
    end = str(data).find("HTTP")
    if start < 0 or end < 0:
        return {}
    query_string = str(data)[start:(end-1)].find("?")
    if query_string < 0:
        return {}
        
    args = str(data)[start:(end-1)][(query_string+1):(end-1)]
    args = args.split("&")
    for arg in args:
        key, value = arg.split("=")
        ret[key] = unquote(value).decode('utf-8')
        
    print(ret)
    return ret

class WebServer():
    def __init__(self, ssid, password):
        self.wlan = None
        self.ssid = ssid
        self.password = password

    def run(self):
        self.wlan = network.WLAN(network.AP_IF)
        self.wlan.config(essid=self.ssid, password=self.password)
        self.wlan.active(True)

        while not self.wlan.active():
            pass

        print("connection successful")
        print(self.wlan.ifconfig())

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 80))
        s.listen(5)

        while True:
            conn, addr = s.accept()
            print("Connected by", addr)
            data = conn.recv(1024)
            if not data:
                pass
            print(data)
            if str(data).find("/set_wifi") != -1:
                wifi_config = parse_query_string(data)
                print(parse_query_string(data))
                conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                conn.send(thank_you_page())
                conn.close()
                try:
                    wifi_config['ssid']
                    wifi_config['password']
                    self.wlan.active(False)
                    self.wlan.disconnect()
                    return wifi_config
                except:
                    print("no password and ssid provided")
                #machine.reset()
            else:
                conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                conn.send(form_page())
                conn.close()
            time.sleep(1)
