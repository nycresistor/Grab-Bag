#!/usr/bin/python

import sys

START_MARKER = [0x00,0x00,0x01]

END_CODE = 0xb9
SEQUENCE_CODE = 0xb3
PICTURE_CODE = 0x00

I_FRAME=1
P_FRAME=2
B_FRAME=3
D_FRAME=4

# When completed, return a set of tuple describing the picture
# frames:
# (picture_type,start_pos,size)

def marker_iter(f):
    c = f.read(1)
    scan_idx = 0
    while(len(c) != 0):
        b = ord(c)
        if b == START_MARKER[scan_idx]:
            scan_idx = scan_idx + 1
            if scan_idx == len(START_MARKER):
                yield f.tell()-3
                scan_idx = 0
        elif b == 0:
            # handle, say, 00 00 00 01
            pass
        else:
            scan_idx = 0
        c = f.read(1)

def scan_file(path):
    scan_idx = 0
    f = open(path,"rb")
    l = []
    cur = None
    for pos in marker_iter(f):
        code = ord(f.read(1))
        #print "Code ",hex(code)
        if code >= 0x01 and code <= 0xaf:
            # slice, continue
            continue
        elif cur != None:
            # other code, end frame
            curlen = pos - cur[1]
            print hex(pos), hex(cur[1]), hex(curlen)
            l.append((cur[0],cur[1],curlen))
            cur = None
        # Handle non-slice codes
        if code == END_CODE:
            return l
        elif code == PICTURE_CODE:
            f.read(1)
            picture_type = 0x07 & (ord(f.read(1)) >> 3)
            cur = (picture_type,pos)
    # possible unterminated block!
    # raise Exception("Unterminated MPG stream! No program end code found.")
    # nah, we only get end codes in packed formats.
    return l

paths=sys.argv[1:]
markers = []
for path in paths:
    print "Scanning file", path, "..."
    l = scan_file(path)
    markers.append(l)
    print len(l), "frames scanned."
    i = reduce(lambda x,y:x+int(y[0]==I_FRAME),l,0)
    print i,"I-frames found."

if len(paths) == 1:
    print l

def copyChunk(tag,src,dest):
    src.seek(tag[1])
    data = src.read(tag[2])
    dest.write(data)

if len(paths) == 2:
    outpath = "puitn.raw"
    print "Scrambulating into",outpath
    outf = open(outpath,"wb")
    files = map(lambda x:open(x,"rb"),paths)
    pSrcIdx = 0
    iSrcIdx = 0
    # 0 is progressive source; 1 is i-frame source
    while True:
        while markers[0][pSrcIdx][0] != I_FRAME:
            print "Copying non-Iframe chunk",pSrcIdx,"size",markers[0][pSrcIdx][2]
            copyChunk(markers[0][pSrcIdx],files[0],outf)
            pSrcIdx = pSrcIdx+1
            if pSrcIdx >= len(markers[0]):
                break
        # skip I-frame
        pSrcIdx = pSrcIdx+1
        if pSrcIdx >= len(markers[0]):
            break
        # skip non-I-frames
        while markers[1][iSrcIdx][0] != I_FRAME:
            iSrcIdx = (iSrcIdx + 1) % len(markers[1])
        # copy I-frame
        print "Copying Iframe chunk",iSrcIdx,"size",markers[0][iSrcIdx][2]
        copyChunk(markers[1][iSrcIdx],files[1],outf)
        # pass frame
        iSrcIdx = (iSrcIdx + 1) % len(markers[1])
        
        
        
