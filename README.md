# mini Python
mini Python is a subset of Python. I wanna see if I can write a Python interpreter of mini Python.  

## Principles
- "MST" = miniPy syntax tree

### Parsing principles
- An expression (can be multiline) is parsed into an expression tree.  
- A cmd (can be multiline) is parsed into a cmd tree.  
- A multi-line cmd must have at least one unclosed bracket/parenthesis in every line except its last line.  
- A sequence of cmd trees are parsed into an MST.  

### Runtime principles
- Runtime is a sequence of configs. 
- A config is (an MST AND a stack OF (Environment AND Program Counter (pointing to a location in MST))s.  
- A namespace is a mapping from Identifier to Object. 
- An Object is a namespace.  
- A function is an MST and an Environment.  
- An Environment is a stack of namespaces (local - nonlocal... - global). 

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
- await, :=
- 1 < 2 < 3
- 4 // 2
- import ... as ...
- +=
- re-raise exception with `raise`
- yield
- tuple cannot omit ()
- multi commands cannot be on same line

## Things
- Memory allocation and garbage collection are inherited from Python. 
- Is minipy a secure sandbox? 
