#!/usr/bin/python

import thread,sys,os
import daemon
from daemon import pidfile
import syslog
import time

import lockfile
import setproctitle
from flask import Flask
app = Flask(__name__)
counter = 0

# apt-get install python-setproctitle
# pip install python-daemon flask
setproctitle.setproctitle("SimpleQueue")

def err(errorMessage):
    print "ERROR: " + errorMessage
    sys.exit(1)

@app.route("/", methods = ['GET'])
def hello():
    global counter
    log("Doing stuff " + str(counter))
    counter = counter + 1
    return "Foobar" + str(counter)

@app.route("/demo", methods = ['GET'])
def flash_demo():
    with open("demo.html", "r") as myfile:
        return myfile.read();

def log(msg):
    """Write message to log file"""
    syslog.openlog("SimpleQueue")
    syslog.syslog(msg)

def flaskThread():
    app.debug = False
    app.run("127.0.0.1","8080");

def start():
    pidDir = "/var/run"
    pidFilename = "SimpleQueue.pid";
    pidFile = pidDir + "/" + pidFilename
    
    global counter

    if not os.access(pidDir, os.W_OK):
        err("Cannot write to " + pidDir)
        sys.exit(1)

    if os.path.isfile(pidFile):
        pid = lockfile.pidlockfile.read_pid_from_pidfile(pidFile)
        err("Pid "+pidFile+" file already exists (pid="+str(pid)+"), refusing to overwrite possibly existing instance")

    with daemon.DaemonContext(pidfile=pidfile.TimeoutPIDLockFile(pidFile)):
        queueThread();

def queueThread():
    i = -1;

    thread.start_new_thread( flaskThread, ())

    log("Starting loop")
    while True:
        log("Loop started")
        if i != counter:
            log("Counter set to "+str(counter))
            i = counter
        time.sleep(1);


start()

