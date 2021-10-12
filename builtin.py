from __future__ import annotations
from lexems import Except
import runtime as rt

def instantiate(theClass : rt.Thing, *args, **keyword_args):
    thing = rt.Thing()
    thing._class = theClass
    baseclass = theClass
    while True:
        __base__ = None
        for name, value in baseclass.namepsace.items():
            if name == '__base__':
                __base__ = value
            else:
                if (
                    name not in thing.namespace
                    and name not in ('__name__', '__repr__')
                ):
                    if value._class is builtin.Function:
                        value = value.copy()
                        value.bound_args.append(thing)
                    thing.namespace[name] = value
        if __base__ is None:
            break
        baseclass = __base__
    if '__init__' in thing.namespace:
        returned = thing.namespace['__init__'].call(*args, **keyword_args)
        if returned is not builtin.__none__:
            ...
            # init should not return non-None
    return thing

def unprimitize(primitive):
    if type(primitive) is int:
        return instantiate(builtin.int, primitive)
    elif type(primitive) is float:
        return instantiate(builtin.float, primitive)
    elif type(primitive) is str:
        return instantiate(builtin.str, primitive)
    elif type(primitive) is bool:
        if primitive:
            return builtin.__true__
        return builtin.__false__
    elif type(primitive) is type(None):
        return builtin.__none__

def isTrue(thing : rt.Thing) -> bool:
    if thing.namespace['__bool__'].call().primitive_value:
        return builtin.__true__
    return builtin.__false__

def wrapFuncion(func):
    thing = instantiate(builtin.Function)
    thing.call = func
    thing.namespace['__name__'] = '(builtin) ' + func.__name__
    return thing

def wrapClass(base = None):
    def _wrapClass(cls):
        thing = instantiate(builtin.Class)
        for key, value in cls.__dict__.items():
            print('   ', key)
            thing.namespace[key] = value
        thing.namespace['__name__'] = cls.__name__
        if base is not None:
            thing.namespace['__base__'] = base
        return thing
    return _wrapClass

def promotePythonException(e):
    raise rt.Helicopter(instantiate(
        builtin.PythonException, 
        repr(e), 
    ))

class builtin:
    Class = rt.Thing()
    Class._class = Class
    Class.namespace['__name__'] = 'Class'
    Class.namespace['__repr__'] = wrapFuncion(
        lambda self : f'<class "{self.namespace["__name__"]}">'
    )
    Class.namespace['__dict__'] = wrapFuncion(
        lambda self : instantiate(builtin.dict, self.namespace)
    )

    @wrapClass()
    class Function:
        @wrapFuncion
        def __repr__(thing):
            try: 
                name = thing.namespace['__name__']
            except KeyError:
                name = ''
            return unprimitize(f'<function {name}>')
    
    @wrapClass()
    class bool:
        @wrapFuncion
        def __init__(thing, x = None):
            if x is None:
                thing.primitive_value = False
            else:
                thing.primitive_value = x.namespace[
                    '__bool__'
                ].call().primitive_value
        
        @wrapFuncion
        def __repr__(thing):
            if isTrue(thing):
                return unprimitize('True')
            return unprimitize('False')
        
        @wrapFuncion
        def __bool__(thing):
            return thing
    __true__  = instantiate(bool)
    __true__ .primitive_value = True
    __false__ = instantiate(bool)
    
    @wrapClass()
    class NoneType: 
        @wrapFuncion
        def __init__(thing):
            thing.primitive_value = None
        
        @wrapFuncion
        def __repr__(thing):
            return 'None'
    __none__ = instantiate(NoneType)
    
    @wrapClass()
    class Exception:
        @wrapFuncion
        def __init__(thing, *args):
            thing.namespace['args'] = instantiate(
                builtin.tuple, args, 
            )
        
        @wrapFuncion
        def __repr__(thing):
            return (
                thing._class.namespace['__name__'] 
                + builtin.repr.call(thing.namespace['args'])
            )
    
    @wrapClass(base = Exception)
    class StopIteration: pass
    @wrapClass(base = Exception)
    class NameError: pass
    @wrapClass(base = Exception)
    class TypeError: pass
    @wrapClass(base = Exception)
    class IndexError: pass
    @wrapClass(base = Exception)
    class KeyError: pass
    @wrapClass(base = Exception)
    class AttributeError: pass
    @wrapClass(base = Exception)
    class ImportError: pass
    @wrapClass(base = Exception)
    class KeyboardInterrupt: pass
    @wrapClass(base = Exception)
    class PythonException: pass

    @wrapClass()
    class int:
        @wrapFuncion
        def __init__(thing, x = None):
            if x is None:
                thing.primitive_value = 0
            elif x._class in (builtin.float, builtin.str):
                try:
                    thing.primitive_value = int(x.primitive_value)
                except Exception as e:
                    promotePythonException(e)
