#!/usr/bin/env python3

import sys
import modpycluster
import uuid


AdvertiseUrl = "http://127.0.0.1:9001"
host = "127.0.0.1"
port = 1234

#generate/load uuid
uuid = str(uuid.uuid4())
uuidfile = ".uuid"
try:
    with open(uuidfile, 'r') as file:
        uuid = file.read().replace('\n', '')
except FileNotFoundError:
    with open(uuidfile, 'w') as file:
        file.write(uuid)

modcluster = modpycluster.modpycluster(AdvertiseUrl=AdvertiseUrl,
                                       host=host,
                                       port=port,
                                       uuid=uuid)

from flask import Flask
app = Flask(__name__)

@app.route("/testpy", methods=['GET'])
def test1():
    return "Hello World!"

@app.route("/some/subpath", methods=['GET'])
def test2():
    return "Return from subpath!"

modcluster.bindFlaskApp(flaskapp=app)
modcluster.run()
app.run(port=port)