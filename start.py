#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring, line-too-long, bare-except, invalid-name

import time
import random
import argparse

import paho.mqtt.client as mqtt
import numpy as np
from PIL import Image

parser = argparse.ArgumentParser(
    description='Send pixels to a mqtt websocket device')

parser.add_argument('-s', '--server', default='broker.host.name', help=r'hostname of the server/broker we send the data to')
parser.add_argument('-p', '--port', default=8084, help=r'the portnumber the server listens to')
parser.add_argument('-b', '--sleep', default=0.3, help=r'sleep x seconds between pixels')
parser.add_argument('-m', '--mqttpath', default='/mqtt', help=r'the path for mqtt-call')
parser.add_argument('-t', '--transport', default='websockets', help=r'the transport-type')
parser.add_argument('-c', '--connect', default='name/draw/connect', help=r'path of the connect-socket')
parser.add_argument('-d', '--draw', default='name/draw', help=r'path of the draw-socket')
parser.add_argument('-i', '--image', default=None, help=r'path of an image. the first to-left 64 pixels are send to the server')
parser.add_argument('-r', '--random', default=False, help=r'Fill the image by pixels of 1 random color')
parser.add_argument('-a', '--allrandom', default=False, help=r'Fill the image by pixels of 64 random colors')
parser.add_argument('-x', '--hex', default=None, help=r'fill the complete area by a certain color given by rgbhex')
parser.add_argument('-l', '--listen', default=False, help=r'stay in listening-mode after call')
args = parser.parse_args()
# print(args)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #client.subscribe("$SYS/#")
    client.subscribe(args.connect)
    client.subscribe(args.draw)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def send_col(x, y, r, g, b, client):
    message = [x, y, r, g, b]
    client.publish(args.draw, payload=bytes(message), qos=0, retain=False)
    # print(message)

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))

def fill_image(client, imgpath):
    img = Image.open(imgpath)
    arr = np.array(img)
    arr_koords = []
    for x in range(8):
        for y in range(8):
            koord = [x, y]
            arr_koords.append(koord)
    random.shuffle(arr_koords)
    for mykoord in arr_koords:
        send_col(mykoord[0], mykoord[1], max(arr[mykoord[1], mykoord[0], 0], 1), max(arr[mykoord[1], mykoord[0], 1], 1), max(arr[mykoord[1], mykoord[0], 2], 1), client)
        time.sleep(args.sleep)

def fill_color(client, color):
    arr = []
    for x in range(8):
        for y in range(8):
            koord = [x, y]
            arr.append(koord)
    random.shuffle(arr)
    for mykoord in arr:
        send_col(mykoord[0], mykoord[1], color[0], color[1], color[2], client)
        time.sleep(args.sleep)

def fill_random(client):
    arr = []
    for x in range(8):
        for y in range(8):
            koord = [x, y]
            arr.append(koord)
    random.shuffle(arr)
    for mykoord in arr:
        send_col(mykoord[0], mykoord[1], random.randrange(255)+1, random.randrange(255)+1, random.randrange(255)+1, client)
        time.sleep(args.sleep)

def fill_random_complete(client):
    color = [random.randrange(255)+1, random.randrange(255)+1, random.randrange(255)+1]
    arr = []
    for x in range(8):
        for y in range(8):
            koord = [x, y]
            arr.append(koord)
    random.shuffle(arr)
    for mykoord in arr:
        send_col(mykoord[0], mykoord[1], color[0], color[1], color[2], client)
        time.sleep(args.sleep)

client = mqtt.Client(transport=args.transport)
client.tls_set_context(context=None)
client.ws_set_options(path=args.mqttpath, headers=None)

client.on_connect = on_connect
client.on_message = on_message

client.connect(args.server, args.port, 60)

if args.allrandom:
    fill_random(client)

if args.random:
    fill_random_complete(client)

if args.image is not None:
    fill_image(client, args.image)

if args.hex is not None:
    fill_color(client, hex_to_rgb(args.hex))

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
if args.listen:
    client.loop_forever()

