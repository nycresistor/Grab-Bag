#!/usr/bin/python
import os

# I'm lazy: from
# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

# find FFMPEG
try:
    ffmpeg_name = os.environ['FFMPEG']
except KeyError:
    ffmpeg_name = 'ffmpeg'
ffmpeg_path = which(ffmpeg_name)

if not ffmpeg_path:
    raise("Could not find ffmpeg. Make sure it's installed, or try setting the FFMPEG environment variable.")

def extract_raw(path):
    import subprocess
    import tempfile
    (handle,outpath) = tempfile.mkstemp(suffix='.raw')
    os.close(handle)
    args = [ffmpeg_path,'-i',path,'-vcodec','copy','-f','rawvideo','-an','-y',outpath]
    retcode = subprocess.call(args)
    return outpath

def encode_raw(in_path,out_path):
    import subprocess
    import tempfile
    args = [ffmpeg_path,'-i',in_path,'-vcodec','copy','-y',out_path]
    retcode = subprocess.call(args)
    return out_path

