#!/usr/bin/python

import daemon
import syslog
import time

def log(msg):
    """Write message to log file"""
    syslog.openlog("SimpleQueue")
    syslog.syslog(msg)

with daemon.DaemonContext():
    i = 1;
    while True:
        i = i + 1
        log("Foobar"+str(i));
        time.sleep(1);
