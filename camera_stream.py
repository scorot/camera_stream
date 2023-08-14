#!/usr/bin/python3
# Web streaming example
# Source code from the official PiCamera package
# http://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming

import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
import RPi.GPIO as GPIO
import time

PAGE="""\
<html>
<head>
<title>Raspberry Pi - Surveillance Camera</title>
</head>
<body style="background-color:black;color:white">
<center><h1>Raspberry Pi - Surveillance Camera</h1></center>
<form action="/" method="POST">
    Turn LED :
    <input type="submit" name="submit" value="On">
    <input type="submit" name="submit" value="Off">
</form>
<form action="/" method="POST">
    Roof :
    <input type="submit" name="roof" value="Open">
    <input type="submit" name="roof" value="Close">
</form>
<center><img src="stream.mjpg" width="640" height="480"></center>
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

    def do_POST(self):
        """ do_POST() can be tested using curl command
            'curl -d "submit=On" http://server-ip-address:port'
        """
        # Get the size of data
        content_length = int(self.headers['Content-Length'])
        # Get the data
        post_data = self.rfile.read(content_length).decode("utf-8")
        post_data = post_data.split("=")[1]    # Only keep the value

        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        # Relay pin numbers in BCM mode
        outPin1 = 19  # WiringPi 24
        outPin2 = 26  # WiringPi 25
        outPin3 = 20  # WiringPi 28
        outPin4 = 21  # WiringPi 29
        GPIO.setup(outPin1, GPIO.OUT)
        GPIO.setup(outPin2, GPIO.OUT)
        GPIO.setup(outPin3, GPIO.OUT)

        if post_data == 'Off':
            GPIO.output(outPin3, GPIO.HIGH)
            print("LED is {}".format(post_data))
        elif post_data == 'On':
            GPIO.output(outPin3, GPIO.LOW)
            print("LED is {}".format(post_data))
        elif post_data == 'Open':
            GPIO.output(outPin1, GPIO.LOW)
            time.sleep(1)
            GPIO.output(outPin1, GPIO.HIGH)
            print("Opening roof...".format(post_data))
        elif post_data == 'Close':
            GPIO.output(outPin2, GPIO.LOW)
            time.sleep(1)
            GPIO.output(outPin2, GPIO.HIGH)
            print("Closing roof...".format(post_data))
        else:
            print("unknown command.")
        #print("LED is {}".format(post_data))
        self._redirect('/')    # Redirect back to the root url

    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='640x480', framerate=5) as camera:
    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    #camera.rotation = 90
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()

