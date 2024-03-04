import socket
import network

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

        def webpage():
            html = "<html><head><title>Hello</title></head><body><p>Hello world!</p></body></html>"
            return html

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 80))
        s.listen(5)

        while True:
            conn, addr = s.accept()
            print("Connected by", addr)
            data = conn.recv(1024)
            if not data:
                pass
            conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            conn.send(webpage())
            conn.close()
