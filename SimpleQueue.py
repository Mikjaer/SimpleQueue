#!/usr/bin/python


# apt-get install python-setproctitle
# pip install python-daemon flask
# pip install configparser



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
import signal
import logging
from logging.handlers import RotatingFileHandler
import select

interactive = False


if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        if arg == "-i":
            interactive = True
            log("Running interactive")



def log(msg):
    global interactive
    """Write message to log file"""
    if interactive:
        print "LOG:"+msg
    else:
        syslog.openlog("SimpleQueue")
        syslog.syslog(msg)


def err(errorMessage):
    msg = "ERROR: " + errorMessage
    syslog.openlog("SimpleQueue")
    syslog.syslog(msg)
    print msg
    sys.exit(1)
def debug(msg):
    #log(msg)
    pass;




class myConfig:
    def __init__(self):
        self.config = configparser.ConfigParser(inline_comment_prefixes=";")
        
        if os.path.isfile("config.ini"):
            configFile = "config.ini"
        elif os.path.isfile("/etc/SimpleQueue.ini"):
            configFile = "/etc/SimpleQueue.ini"
        elif os.path.isfile("/etc/SimpleQueue/config.ini"):
            configFile = "/etc/SimpleQueue/config.ini"
        else:
            log("SimpleQueue: Could not locate config.ini, giving up");
            sys.exit(1)

        log("Reading config from "+configFile)
        self.config.read(configFile);

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
heartbeat = 0

import lockfile
import setproctitle
from flask import Flask
app = Flask(__name__)
counter = 0


setproctitle.setproctitle("SimpleQueue")

@app.route('/')
def flask_default():
    global heartbeat

    if request.args.get('status'):
        return jsonify({"heartbeat": heartbeat, "idle": int(time.time()) - heartbeat})
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

        #### /Print stats

        if request.args.get('payload'):
            payload = request.args.get('payload')
        else:
            payload = "";

        if not queues[queue].full():
            log("Queue `"+queue+"` job enqued") 
            queues[queue].put(payload,True,None)
            return jsonify({"status":"success"});
        else:
            log("Queue `"+queue+"` job rejected") 
            return jsonify(
                {"status":"rejected", 
                 "message":"Queue full"});
        
        log("Queue `"+queue+"` unfinished_tasks:" + str(queues[queue].unfinished_tasks) + " maxsize:" + str(queues[queue].maxsize)+full)
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
    #app.debug = False
    app.run(config.settings("listen"),int(config.settings("port")));

    #http_server = WSGIServer(('', 5000), app)
    #http_server.serve_forever();

def start():
    global interactive
    log("Starting SimpleQueue")

    pidDir = config.settings("piddir");
    pidFile = config.settings("pidfile")

    pidFileAbs = pidDir + "/" + pidFile
   
    global counter

    if not os.access(pidDir, os.W_OK):
        err("Cannot write to " + pidDir)

    elif os.path.isfile(pidFileAbs):
        pid = lockfile.pidlockfile.read_pid_from_pidfile(pidFileAbs)
        err("Pid "+pidFile+" file already exists (pid="+str(pid)+"), refusing to overwrite possibly existing instance")

    else:
        if interactive:
            queueThread();
        else:
            debug("Deamonizing:"+pidFileAbs);
            context = daemon.DaemonContext(
                pidfile=pidfile.TimeoutPIDLockFile(pidFileAbs),
                signal_map={
                    signal.SIGTERM: terminate,
                    signal.SIGTSTP: terminate
                })
            context.terminate = terminate
            with context:
                queueThread();

def terminate(sugnum, frame):
    log("Shutting down SimpleQueue")
    sys.exit(0)

def queueThread():
    global heartbeat
    i = -1;
    c = 1;
    thread.start_new_thread( flaskThread, ())


    # Setting up queues

    for q in config.queueList():
        queueLength = config.queueSetting(q,"length")
        if queueLength:
            queues[q] = Queue.Queue(maxsize=int(queueLength))
            log("Setting up queue `"+q+"` with '"+str(queueLength)+"' elements")
        else:
            queues[q] = Queue.Queue() 
            queueLength = -1



    while True:
        heartbeat = int(time.time())
        for q in config.queueList():
            if not queues[q].empty():
                payload = queues[q].get()
                log("Processing job from " + q + ", payload: "+payload)
                
                runas = config.queueSetting(q,"runas")
               
                if runas:
                    groups = os.getgroups()
                    try:
                        os.setgroups([])
                        os.setresgid(getpwnam(runas).pw_gid, getpwnam(runas).pw_gid,-1);
                        os.setresuid(getpwnam(runas).pw_uid, getpwnam(runas).pw_uid,-1);
                    except KeyError:
                        log("Unknown user "+runas+", aborting execution");
                        break
                
                process = subprocess.Popen(         # Start process in background, and attach pipes
                    config.queueSetting(q,"run").split(' '),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
              
                process.stdin.write(payload)        # Send payload
                process.stdin.close();

                stdout=select.poll();               # Hook a select.pool to out-pipes
                stdout.register(process.stdout)
            
                stderr=select.poll();
                stderr.register(process.stderr)

                while True:
                    if stdout.poll(1000) or stderr.poll(1000):    # Empty pipes?
                        if stdout.poll(1):
                            line = process.stdout.readline()
                            if line != "":
                                log("stdout:"+line.rstrip())
                    
                        if stderr.poll(1):
                            line = process.stderr.readline()
                            if line != "":
                                log("stderr:"+line.rstrip())
                    
                    else:
                        time.sleep(1)
                
                    if not process.poll() is None:  # Process still running? and pipes empty?
                        break;

                if runas:                   # Regain root-privileges
                    os.setresgid(0,0,-1)
                    os.setresuid(0,0,-1)
                    os.setgroups(groups)
                log("Job done, returncode "+ str(process.returncode))

        time.sleep(1);  # End of loop

start()

