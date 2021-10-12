import os
from runtime import RunTime

def runScript(entry_filename):
    dir_location, filename = os.path.split(entry_filename)
    name = os.path.splitext(filename)
    runTime = RunTime(dir_location)
    runTime.imPort(name, '__main__')
