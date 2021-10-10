# mini Python
mini Python is a subset of Python. I wanna see if I can write a Python interpreter of mini Python.  

## Principles
- "MST" = miniPy syntax tree

### Parsing principles
- An expression (can be multiline) is parsed into an expression tree.  
- A cmd (can be multiline) is parsed into a cmd tree.  
- A multi-line cmd must have at least one unclosed bracket/parenthesis in every line except its last line.  
- A sequence of cmd trees are parsed into an MST.  

### Runtime principles: State Machine Version
This will support nice keyboard interrupt, error-time stack output, and threading. 
- Runtime is a sequence of configs. 
- A config is (an MST AND a stack OF (Environment AND Program Counter (pointing to a location in MST) AND partially evaluated cmdTree)s.  
- A namespace is a mapping from Identifier to Object. 
- An Object is a namespace.  
- A function is an MST and an Environment.  
- An Environment is a stack of namespaces (local - nonlocal... - global). 
- Importing and calling function will push (Env, PC) on stack of config. 

### Runtime principles: Recursive Interpreter Version
This is much easier to implement. 
How to error-time output stack? define exception? 
- A namespace is a mapping from Identifier to Thing. 
- A Thing has a namespace.  
- Executing an MST evolves an Environment. 
- An Environment is a stack of namespaces (local - nonlocal... - global). 
- A function has an MST and an Environment.  
- A function is a Thing. 
- type(thing) -> thingTemplate
- class.__base__ = None | class

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
- `except Exception as e`
- yield
- tuple cannot omit ()
- multi commands cannot be on same line
- Some builtin attributes are read-only in Python. They can be modified by user in miniPy. 
- `except (Exc1, Exc2):` is not allowed. 
- `isinstanceof` is intentionally not exposed. 
- you can `raise` non-exception things. 
- There's no `BaseException`. just use `Exception`. 
- `object` class is not exposed. 

## Remarks
- Memory allocation and garbage collection are inherited from Python. 
- Is minipy a secure sandbox? 

### class thing
```python
class c:
 def print(x):
  print(x+1)

 print(3)
```
prints "4" in Python.  
I have no idea what they did. 

## todo
- minipy interactive shell
