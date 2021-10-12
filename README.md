# mini Python
mini Python is a subset of Python. I wanna see if I can write a Python interpreter of mini Python.  

## Principles
- "MST" = miniPy syntax tree

### Parsing principles
- An expression (can be multiline) is parsed into an expression tree.  
- A cmd (can be multiline) is parsed into a cmd tree.  
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
- with ... as ...
- `f'{1}'`
- `'%d kg' % 3`
- many built-ins (file system...)
- package import
- multi inheritance
- lambda function
- `1 if 0 else 2`
- `[*'asd']`
- | ^ & << >> @ ~
- await, :=
- `1 < 2 < 3`
- `4 // 2`
- import ... as ...
- `+=`
- re-raise exception with `raise`
- `except Exception as e`
- `yield`
- tuple cannot omit ()
- multi commands cannot be on same line
- `except (Exc1, Exc2):` is not allowed. 
- `help()`
- `10e-5`
- Variable names starting with "__" does not rename the variable into private. 

## what's different
- A multi-line cmd must have at least one unclosed bracket/parenthesis in every line except its last line.  
- Some builtin attributes are read-only in Python. They can be modified by user in miniPy. 
- `isinstanceof` is intentionally not exposed. 
- you can `raise` non-exception things. 
- There's no `BaseException`. just use `Exception`. 
- `object` class is not exposed. 
- Exception raised in "finally" section does not display "During handling of the above exception". 

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

### Another class thing
When instantiating, Python binds the object to the first argument of all the class methods.  
Or does it?  
```python
class F:
 def __call__(self, a):
  print(a)

f=F()

class C:
 a=f

C().a()
```
Reports `TypeError: __call__() missing 1 required positional argument: 'a'`, while  
```python
def g(x):
 print(x)

class C:
 a=g

c().a()
```
returns `<__main__.c object at ...>`

This means, not all callables are binded --- only "functions" are. 

### Ten primitive types
- int, float
- str
- bool, NoneType
- list
- tuple
- dict
- set
- slice

Who would have thought that slice needs to be a primitive type? 

## Security
- a minipy script can read .minipy files
  - under the same dir as the entry script
  - under %MINIPYPATH%

## todo
- minipy interactive shell
