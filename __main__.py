import os
import argparse
from builtin import reprString
from runtime import RunTime, Helicopter

def runScript(entry_filename):
    dir_location, filename = os.path.split(entry_filename)
    name = os.path.splitext(filename)
    runTime = RunTime(dir_location)
    try:
        runTime.imPort(name, '__main__')
    except Helicopter as h:
        printStackTrace(h)

def printStackTrace(helicopter : Helicopter):
    print('Traceback (most recent call last):')
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
        'scriptname', type=str, nargs=1,
        help='filename of the miniPy script to be executed', 
    )

    args = parser.parse_args()
    from console import console
    console({**globals(), **locals()})
    args

main()
