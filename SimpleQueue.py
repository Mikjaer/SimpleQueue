#!/usr/bin/python

import daemon
import syslog
import time

import setproctitle
from flask import Flask
app = Flask(__name__)

# apt-get install python-setproctitle
# pip install python-daemon flask
setproctitle.setproctitle("SimpleQueue")

@app.route("/")
def hello():
    return "Foobar"

def log(msg):
    """Write message to log file"""
    syslog.openlog("SimpleQueue")
    syslog.syslog(msg)

with daemon.DaemonContext():
    app.run("127.0.0.1","8080")
    i = 1;
    while True:
        i = i + 1
        log("Foobar"+str(i));
        time.sleep(1);
