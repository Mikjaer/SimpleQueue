#!/usr/bin/python -u

import sys
import time
import subprocess
import fileinput

payload = ""
for line in fileinput.input():
	payload = payload + line

print "Got payload: "+payload

print "SimpleQueue testjob"
subprocess.call(["id"])
for i in range(0,10):
	print "Doing stuph "+str(i)
	time.sleep(1)


sys.stderr.write("Diz is error\n")

print "Stopping execution with errorcode 123\n"
sys.exit(123)
