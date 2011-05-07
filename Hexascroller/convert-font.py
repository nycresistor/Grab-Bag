#!/usr/bin/python

import PIL.Image

f = PIL.Image.open("font-src.png")

(w,h) = f.size
d = f.getdata()

inventory = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.!?@/:;()#"

charData = ['0'] * (8*8*128)

def getRow(x,offset):
    global charData
    global d
    hasPixel = False
    for y in range(7):
        i = w*y + x
        if d[i] == (0,0,0):
            hasPixel = True
            charData[offset+y] = '1'
        else:
            charData[offset+y] = '0'
    return hasPixel

x = 0

for c in inventory:
    offset = ord(c)*8*8
    more = True
    while more:
        more = getRow(x,offset)
        if not more:
            charData[offset+7] = '1'
        x = x + 1
        offset = offset + 8

print "uint8_t charData[] PROGMEM = {"

for i in range(8*128):
    sub = charData[i*8:(i+1)*8]
    print "    0b"+"".join(sub)+","

print "};"

