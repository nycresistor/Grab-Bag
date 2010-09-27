 rem Atari 2600 Demo for NYC Resistor Booth at Worlds Maker Faire 2010
 rem
 rem Copyright (c) 2010, Ben Combee
 rem All rights reserved.
 rem
 rem Redistribution and use in source and binary forms, with or without modification, are permitted 
 rem provided that the following conditions are met:
 rem 
 rem  * Redistributions of source code must retain the above copyright notice, this list of conditions 
 rem    and the following disclaimer.
 rem  * Redistributions in binary form must reproduce the above copyright notice, this list of 
 rem    conditions and the following disclaimer in the documentation and/or other materials provided 
 rem    with the distribution.
 rem  * Neither the name of NYC Resistor nor the names of its contributors may be used to endorse 
 rem    or promote products derived from this software without specific prior written permission.
 rem 
 rem THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
 rem IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
 rem FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS 
 rem BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
 rem BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR 
 rem BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT 
 rem LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
 rem SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

 set kernel_options pfcolors
 set smartbranching on
 const noscore = 1

 dim NYCR_COLOR = a
 dim YPOSIDX = b
 dim NYCR_XPOS = c
 dim NYCR_XDIR = d
 dim FRAMECOUNT = e
 dim SCROLLIDX = f
 dim NEWPF = g

 pfcolors:
 $72
 $72
 $76
 $78
 $7A
 $7C
 $78
 $76
 $74
 $72
 $72
end

 player0:
 %00111100
 %00111100
 %01000010
 %01000010
 %10000001
 %10000001
 %11010101
 %11010101
 %10101011
 %10101011
 %10000001
 %10000001
 %01000010
 %01000010
 %00111100
 %00111100
end

main

 NYCR_COLOR = $10
 NYCR_XPOS = 1
 NYCR_XDIR = 1
 FRAMECOUNT = 0
 SCROLLIDX = $FF

loop

 rem Double Width Player 0
 NUSIZ0 = %101

 rem player goes behind playfield
 CTRLPF = %101

 NYCR_COLOR = NYCR_COLOR + 1
 if NYCR_COLOR > $4F then NYCR_COLOR = $10
 COLUP0 = NYCR_COLOR

 COLUBK = $00

 temp1 = FRAMECOUNT & $03
 if temp1 <> 0 then goto dontupdatex
 NYCR_XPOS = NYCR_XPOS + NYCR_XDIR
 if NYCR_XPOS = 1 then NYCR_XDIR = 1
 if NYCR_XPOS = 140 then NYCR_XDIR = $FF
dontupdatex
 player0x = NYCR_XPOS

 temp1 = FRAMECOUNT & $01
 if temp1 <> 0 then goto dontupdatey
 YPOSIDX = YPOSIDX + 1
 if YPOSIDX = 32 then YPOSIDX = 0
dontupdatey
 player0y = 86 - YPOS[YPOSIDX]

 rem  this command instructs the program to write data to the TV screen.
 drawscreen

 rem only scroll every other frame
 FRAMECOUNT = FRAMECOUNT + 1
 if FRAMECOUNT{0} then goto loop

 pfscroll left

 SCROLLIDX = SCROLLIDX + 1
 if SCROLLIDX = $4e then SCROLLIDX = 0

 NEWPF = SCROLLINGPF[SCROLLIDX]
 if NEWPF{0} then pfpixel 31 8 on else pfpixel 31 8 off
 if NEWPF{1} then pfpixel 31 7 on else pfpixel 31 7 off
 if NEWPF{2} then pfpixel 31 6 on else pfpixel 31 6 off
 if NEWPF{3} then pfpixel 31 5 on else pfpixel 31 5 off
 if NEWPF{4} then pfpixel 31 4 on else pfpixel 31 4 off
 if NEWPF{5} then pfpixel 31 3 on else pfpixel 31 3 off
 if NEWPF{6} then pfpixel 31 2 on else pfpixel 31 2 off

 rem you have to have a game loop, so tell the program to jump back to the beginning.
 goto loop


 data SCROLLINGPF
 %01111111,
 %00100000,
 %00010000,
 %00001000,
 %01111111,
 %00000000,

 %01100000,
 %00011000,
 %00000111,
 %00011000,
 %01100000,
 %00000000,

 %00111110,
 %01000001,
 %01000001,
 %01000001,
 %00100010,
 %00000000,

 %00000000,
 %00000000,
 %00000000,
 %00000000,

 %01111111,
 %01001000,
 %01001100,
 %01001010,
 %00110001,
 %00000000,
 
 %01111111,
 %01001001,
 %01001001,
 %01001001,
 %01000001,
 %00000000,
 
 %00110001,
 %01001001,
 %01001001,
 %01001001,
 %01000110,
 %00000000,
 
 %01000001,
 %01000001,
 %01111111,
 %01000001,
 %01000001,
 %00000000,
 
 %00110001,
 %01001001,
 %01001001,
 %01001001,
 %01000110,
 %00000000,
 
 %01000000,
 %01000000,
 %01111111,
 %01000000,
 %01000000,
 %00000000,
 
 %00111110,
 %01000001,
 %01000001,
 %01000001,
 %00111110,
 %00000000,
 
 %01111111,
 %01001000,
 %01001100,
 %01001010,
 %00110001,
 %00000000,

 %00000000,
 %00000000,
 %00000000,
 %00000000
 %00000000,
 %00000000,
 %00000000,
 %00000000

end

 data YPOS
  0,  7, 14, 20, 27, 33, 39, 44,
 49, 54, 58, 62, 65, 67, 69, 70,
 70, 70, 69, 67, 65, 62, 58, 54,
 50, 44, 39, 33, 27, 20, 14, 7
end
