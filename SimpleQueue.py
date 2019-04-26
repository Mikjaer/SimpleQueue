#!/usr/bin/python



import thread,sys,os
import daemon
from daemon import pidfile
import syslog
import time
import pprint
import configparser
from gevent.pywsgi import WSGIServer
from flask import send_from_directory
from flask import jsonify
from flask import request
import Queue
from pwd import getpwnam
import subprocess

class myConfig:
    def __init__(self):
        self.config = configparser.ConfigParser(inline_comment_prefixes=";")
        
        if os.path.isfile("config.ini"):
            self.config.read("config.ini")
        elif os.path.isfile("/etc/SimpleQueue.ini"):
            self.config.read("/etc/SimpleQueue.ini")
        elif os.path.isfile("/etc/SimpleQueue/config.ini"):
            self.config.read("/etc/SimpleQueue/config.ini")
        else:
            print "SimpleQueue: Could not locate config.ini";
            sys.exit(1)

    def queues(self):
        self.foobar = "hest";
        return self.config.sections()

    def queueExists(self, queue):
        try:
            self.config[queue]["run"]
        except KeyError:
            return False;
        else:
            return True;

    def queueList(self):
        queues = []
        for key in self.config.sections():
            if self.queueExists(key):
                queues.append(key)

        return queues

    def settings(self, key):
        if key in self.config["Settings"]:
            return self.config["Settings"][key];

    def queueSetting(self, queue, key):
        if key in self.config[queue]:
            return self.config[queue][key];
        else:
            return False
            print "SimpleQueue: Could not locate "+key+" in "+queue 

config = myConfig()
queues = {}

# Setting up queues

for q in config.queueList():
    queueLength = config.queueSetting(q,"length")
    if queueLength:
        queues[q] = Queue.Queue(maxsize=int(queueLength))
        print "Initialized queue `"+q+"` with '"+str(queueLength)+"' elements"
    else:
        queues[q] = Queue.Queue() 
        queueLength = -1

#for key in config.sections():
#    print key
#    print config[key]["run"]

#sys.exit(1)

import lockfile
import setproctitle
from flask import Flask
app = Flask(__name__)
counter = 0

interactive = True  # False

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

@app.route('/')
def flask_default():
    html = "<strong>Active queues:</strong><ul>"
    for queue in config.queueList():
        html = html + "<li><a href='/"+queue+"'>" + queue + "</a></li>";
    return html + "</ul>"; 

@app.route('/<path:queue>')
def hello(queue):
    if (config.queueExists(queue)):
        #### Print stats
        if queues[queue].full():
            full = " queue is full"
        else:
            full = " queue is NOT full";

        log("Queue `"+queue+"` unfinished_tasks:" + str(queues[queue].unfinished_tasks) + " " + str(queues[queue].maxsize)+full)
        #### /Print stats

        if request.args.get('payload'):
            payload = request.args.get('payload')
        else:
            payload = "";

        if not queues[queue].full():
            queues[queue].put(payload,True,None)
            return jsonify({"status":"success"});
        else:
            return jsonify(
                {"status":"rejected", 
                 "message":"Queue full"});
    else:
        log("Queue not found")
        return "Queue not found";

@app.route("/demo", methods = ['GET'])
def flash_demo():
    with open("/home/mmc/kode/SimpleQueue/demo.html", "r") as myfile:
        return myfile.read();

@app.route("/demo", methods = ['PUT'])
def put_queues():
    log("Got queue put");
    return "Thankyou";

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'./artwork/favico/favicon.ico', mimetype='image/vnd.microsoft.icon')


def flaskThread():
    app.debug = False
    app.run(config.settings("listen"),config.settings("port"));

    #http_server = WSGIServer(('', 5000), app)
    #http_server.serve_forever();

def start():
    global interactive

    pidDir = config.settings("piddir");
    pidFile = config.settings("pidfile")

    pidFileAbs = pidDir + "/" + pidFile
    
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
    #    log("Loop started " + str(c))
    #    c = c + 1
    #    if i != counter:
    #        log("Counter set to "+str(counter))
    #        i = counter
        time.sleep(1);
        for q in config.queueList():
            if not queues[q].empty():
                print "Processing job from " + q + ", payload: "+queues[q].get()
                
                runas = config.queueSetting(q,"runas")
               
                if runas:
                    groups = os.getgroups()
                    os.setgroups([])
                    os.setresgid(getpwnam(runas).pw_gid, getpwnam(runas).pw_gid,-1);
                    os.setresuid(getpwnam(runas).pw_uid, getpwnam(runas).pw_uid,-1);
                
                subprocess.call([config.queueSetting(q,"run")])

                if runas:
                    os.setresgid(0,0,-1)
                    os.setresuid(0,0,-1)
                    os.setgroups(groups)

        #for key in config.sections():
         #   print key

start()

