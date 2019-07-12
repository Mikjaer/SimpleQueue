#!/usr/bin/python
import requests
import pprint
import sys

if len(sys.argv) < 2:
    print "Usage: sq [queue]\n";
    sys.exit(-1)

resp = requests.get('http://127.0.0.1:8080/'+sys.argv[1])
if resp.status_code != 200:
    # This means something went wrong.
    raise ApiError('GET /tasks/ {}'.format(resp.status_code))

print resp.json()["status"]

