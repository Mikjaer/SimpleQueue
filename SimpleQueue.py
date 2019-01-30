#!/usr/bin/python

import thread,sys,os
import daemon
from daemon import pidfile
import syslog
import time
import pprint
import configparser


class myConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
    
    def queues(self):
        self.foobar = "hest";
        return self.config.sections()

config = myConfig()

config = configparser.ConfigParser()
config.read("config.ini")

for key in config.sections():
    print key
    print config[key]["run"]

sys.exit(1)

import lockfile
import setproctitle
from flask import Flask
app = Flask(__name__)
counter = 0

interactive = False

def log(msg):
    global interactive
    """Write message to log file"""
    if interactive:
        print msg
    else:
        syslog.openlog("SimpleQueue")
        syslog.syslog(msg)

if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        if arg == "-i":
            interactive = True
            log("Running interactive")



# apt-get install python-setproctitle
# pip install python-daemon flask
# pip install configparser

setproctitle.setproctitle("SimpleQueue")

def err(errorMessage):
    print "ERROR: " + errorMessage
    sys.exit(1)
    print "--------------"

@app.route("/", methods = ['GET'])
def hello():
    global counter
    log("Doing stuff " + str(counter))
    counter = counter + 1
    return "Foobar" + str(counter)

@app.route("/demo", methods = ['GET'])
def flash_demo():
    with open("/home/mmc/kode/SimpleQueue/demo.html", "r") as myfile:
        return myfile.read();

@app.route("/demo", methods = ['PUT'])
def put_queues():
    log("Got queue put");
    return "Thankyou";

def flaskThread():
    app.debug = False
    app.run("127.0.0.1","8080");

def start():
    global interactive

    pidDir = "/var/run"
    pidFilename = "SimpleQueue.pid";
    pidFile = pidDir + "/" + pidFilename
    
    global counter

    if not os.access(pidDir, os.W_OK):
        err("Cannot write to " + pidDir)

    elif os.path.isfile(pidFile):
        pid = lockfile.pidlockfile.read_pid_from_pidfile(pidFile)
        err("Pid "+pidFile+" file already exists (pid="+str(pid)+"), refusing to overwrite possibly existing instance")

    else:
        log("Starting loop")
        if interactive:
            queueThread();
        else:
            with daemon.DaemonContext(pidfile=pidfile.TimeoutPIDLockFile(pidFile)):
                queueThread();

def queueThread():
    i = -1;
    c = 1;
    thread.start_new_thread( flaskThread, ())

    while True:
        log("Loop started " + str(c))
        c = c + 1
        if i != counter:
            log("Counter set to "+str(counter))
            i = counter
        time.sleep(1);
        for key in config.sections():
            print key

start()

