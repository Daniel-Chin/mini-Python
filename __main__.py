import os
import argparse
from runtime import RunTime, Helicopter, reprString

def runScript(entry_filename):
    dir_location, filename = os.path.split(entry_filename)
    name, _ = os.path.splitext(filename)
    runTime = RunTime(dir_location)
    try:
        runTime.imPort(name, '__main__')
    except Helicopter as h:
        printStackTrace(h)

def printStackTrace(helicopter : Helicopter):
    print('miniPy traceback (most recent call last):')
    while True:
        for filename, line_number, label in helicopter.stack:
            acc = line_number
            with open(filename, 'r') as f:
                for line in f:
                    if acc == 0:
                        break
                    acc -= 1
            print(
                '  File "', filename, '", line ', line_number, 
                ', in ', label, 
                sep='', 
            )
            print(' ' * 4, line, sep='')
        print(reprString(helicopter.content))
        helicopter = helicopter.below
        if helicopter is None:
            break
        print('\nDuring handling of the above exception, the below occured:\n')

def main():
    parser = argparse.ArgumentParser(
        description='miniPy', 
    )
    parser.add_argument(
        'scriptname', type=str, nargs='?', default=None, 
        help='filename of the miniPy script to be executed', 
    )
    scriptname = parser.parse_args().scriptname
    scriptname = 'test.minipy'
    if scriptname is None:
        repl()
    else:
        filename = os.path.abspath(scriptname)
        with open(filename, 'r') as _:
            pass    # just to check permission, isfile...
        runScript(filename)

def repl():
    print('Under construction')

main()
