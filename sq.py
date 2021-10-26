#!/usr/bin/python3
import requests
import pprint
import sys

if len(sys.argv) < 2:
    print ("Usage: sq <queue> [payload]\n");
    sys.exit(-1)

if len(sys.argv) > 2: # Got payload
    payload = "?payload="+(" ".join(sys.argv[2:]))
else:
    payload = "";


if sys.argv[1] == "list":
    try:
        resp = requests.get('http://127.0.0.1:8080/?status=true')
    except Exception:
        print ("Error: Could not connect to 127.0.0.1:8080\n");
        sys.exit(-1);

    if resp.status_code != 200: 
        print ("Error: unknown error, status code:".format(resp.status_code))
    try:
        queues = " ".join(resp.json()["queues"])
    except Exception:
        print ("Error: response not well-formated json:\n");
        print (resp.content);
        sys.exit(-1);
    
    if len(sys.argv) == 3 and sys.argv[2] == "complete":
        print (queues)
    else:
        print ("Available queues: "+queues)
 
    sys.exit(0)

try:
	resp = requests.get('http://127.0.0.1:8080/'+sys.argv[1]+payload)
except Exception:
	print ("Error: Could not connect to 127.0.0.1:8080\n");
	sys.exit(-1);

if resp.status_code != 200:
	print ("Error: unknown error, status code:".format(resp.status_code))

try:
	print (resp.json()["status"])
except Exception:
	print ("Error: response not well-formated json:\n");
	print (resp.content);
	sys.exit(-1);
