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
parser.add_argument('-z', '--direction', default='random', help=r'direction for hex-filling')
parser.add_argument('-e', '--stripes', default=None, help=r'fill the complete area by stripes')
parser.add_argument('-f', '--chess', default=None, help=r'fill the complete area by chessboard-pattern')
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

def sortdirection(direction):
    if direction == 'chooserandom':
        direction = random.choice(['hsnake', 'l2r', 'vsnake', 'hsnake', 'clockwise', 'down', 'random'])
    arr = []
    for x in range(8):
        for y in range(8):
            koord = [x, y]
            arr.append(koord)
    if direction == 'hsnake':
        idx = [0, 8, 16, 24, 32, 40, 48, 56, 
            57, 49, 41, 33, 25, 17, 9, 1,
            2, 10, 18, 26, 34, 42, 50, 58,
            59, 51, 43, 35, 27, 19, 11, 3,
            4, 12, 20, 28, 36, 44, 52, 60,
            61, 53, 45, 37, 29, 21, 13, 5,
            6, 14, 22, 30, 38, 46, 54, 62,
            63, 55, 47, 39, 31, 23, 15, 7]
        arr = [arr[i] for i in idx]
    elif direction == 'l2r':
        idx = [0, 8, 16, 24, 32, 40, 48, 56,
               1, 9, 17, 25, 33, 41, 49, 57,
               2, 10, 18, 26, 34, 42, 50, 58,
               3, 11, 19, 27, 35, 43, 51, 59,
               4, 12, 20, 28, 36, 44, 52, 60,
               5, 13, 21, 29, 37, 45, 53, 61,
               6, 14, 22, 30, 38, 46, 54, 62,
               7, 15, 23, 31, 39, 47, 55, 63]
        arr = [arr[i] for i in idx]
    elif direction == 'vsnake':
        idx = [0, 1, 2, 3, 4, 5, 6, 7,
               15, 14, 13, 12, 11, 10, 9, 8,
               16, 17, 18, 19, 20, 21, 22, 23,
               31, 30, 29, 28, 27, 26, 25, 24,
               32, 33, 34, 35, 36, 37, 38, 39,
               47, 46, 45, 44, 43, 42, 41, 40,
               48, 49, 50, 51, 52, 53, 54, 55,
               63, 62, 61, 60, 59, 58, 57, 56]
        arr = [arr[i] for i in idx]
    elif direction == 'clockwise':
        idx = [0, 1, 2, 3, 4, 5, 6, 7,
               15, 23, 31, 39, 47, 55, 63,
               62, 61, 60, 59, 58, 57, 56,
               48, 40, 32, 24, 16, 8, 9,
               10, 11, 12, 13, 14, 22, 30,
               38, 46, 54, 53, 52, 51, 50,
               49, 41, 33, 25, 17, 18, 19,
               20, 21, 29, 37, 45, 44, 43,
               42, 34, 26, 27, 28, 36, 35]        
        arr = [arr[i] for i in idx]
    elif direction != 'down':
        random.shuffle(arr)
    return arr

def fill_image(client, imgpath, direction):
    img = Image.open(imgpath)
    arr = np.array(img)
    arr_koords = sortdirection(direction)
    for mykoord in arr_koords:
        send_col(mykoord[0], mykoord[1], max(arr[mykoord[1], mykoord[0], 0], 1), max(arr[mykoord[1], mykoord[0], 1], 1), max(arr[mykoord[1], mykoord[0], 2], 1), client)
        time.sleep(args.sleep)

def fill_color(client, color, direction):
    arr = sortdirection(direction)
    for mykoord in arr:
        send_col(mykoord[0], mykoord[1], color[0], color[1], color[2], client)
        time.sleep(args.sleep)

def fill_random(client, direction):
    arr = sortdirection(direction)
    for mykoord in arr:
        send_col(mykoord[0], mykoord[1], random.randrange(255)+1, random.randrange(255)+1, random.randrange(255)+1, client)
        time.sleep(args.sleep)

def fill_random_complete(client, direction):
    color = [random.randrange(255)+1, random.randrange(255)+1, random.randrange(255)+1]
    arr = sortdirection(direction)
    for mykoord in arr:
        send_col(mykoord[0], mykoord[1], color[0], color[1], color[2], client)
        time.sleep(args.sleep)

def fill_random_stripes(client, direction):
    color1 = [random.randrange(255)+1, random.randrange(255)+1, random.randrange(255)+1]
    color2 = [random.randrange(255)+1, random.randrange(255)+1, random.randrange(255)+1]
    direction = random.randrange(1)
    arr = sortdirection(direction)
    for mykoord in arr:
        if direction == 1:
            if mykoord[0]%2 == 0:
                send_col(mykoord[0], mykoord[1], color1[0], color1[1], color1[2], client)
            else:
                send_col(mykoord[0], mykoord[1], color2[0], color2[1], color2[2], client)
        else:
            if mykoord[1]%2 == 0:
                send_col(mykoord[0], mykoord[1], color1[0], color1[1], color1[2], client)
            else:
                send_col(mykoord[0], mykoord[1], color2[0], color2[1], color2[2], client)
        time.sleep(args.sleep)

def fill_random_chess(client, direction):
    color1 = [random.randrange(255)+1, random.randrange(255)+1, random.randrange(255)+1]
    color2 = [random.randrange(255)+1, random.randrange(255)+1, random.randrange(255)+1]
    arr = sortdirection(direction)
    for mykoord in arr:
        if (mykoord[0]%2 == 0 and mykoord[1]%2 == 1) or (mykoord[0]%2 == 1 and mykoord[1]%2 == 0):
            send_col(mykoord[0], mykoord[1], color1[0], color1[1], color1[2], client)
        else:
            send_col(mykoord[0], mykoord[1], color2[0], color2[1], color2[2], client)
        time.sleep(args.sleep)

client = mqtt.Client(transport=args.transport)
client.tls_set_context(context=None)
client.ws_set_options(path=args.mqttpath, headers=None)

client.on_connect = on_connect
client.on_message = on_message

client.connect(args.server, args.port, 60)
args.sleep = float(args.sleep)

if args.allrandom:
    fill_random(client, args.direction)

if args.random:
    fill_random_complete(client, args.direction)

if args.image is not None:
    fill_image(client, args.image, args.direction)

if args.hex is not None:
    fill_color(client, hex_to_rgb(args.hex), args.direction)

if args.stripes:
    fill_random_stripes(client, args.direction)

if args.chess:
    fill_random_chess(client, args.direction)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
if args.listen:
    client.loop_forever()

