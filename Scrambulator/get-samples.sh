#!/bin/sh
wget http://www.archive.org/download/us_steel/us_steel.mpeg
wget http://www.archive.org/download/409_bathroom_cleaner/409_bathroom_cleaner.mpeg
ffmpeg -i us_steel.mpeg -vcodec copy -f rawvideo -an t1.raw
ffmpeg -i 409_bathroom_cleaner.mpeg -vcodec copy -f rawvideo -an t2.raw