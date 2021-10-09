# mini Python
mini Python is a subset of Python. I wanna see if I can write a Python interpreter of mini Python.  

## Things
- A module is a pair of (namespace, script).  
- A script is a miniPy syntax tree ("MST").  
- A cmd (can be multiline) is parsed into a cmd tree.  
- A sequence of cmd trees are parsed into an MST.  
- An expression (can be multiline) is parsed into an expression tree.  
- A multi-line cmd must have at least one unclosed bracket/parenthesis in every line except its last line.  

## What's missing
- decorator
- with as
- f'{1}'
- '%d kg' % 3
- many built-ins
- package import
- multi inheritance
- lambda function
- 1 if 0 else 2
- [*a]
- | ^ & << >> @ ~
- await, ;=
- 1 < 2 < 3
- 4 // 2
- import as
- named argument
- 