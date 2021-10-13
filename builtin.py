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
    if type(primitive) is bool:
        if primitive:
            return builtin.__true__
        return builtin.__false__
    elif type(primitive) is dict:
        thing = instantiate(builtin.dict)
        for key, value in primitive.items():
            thing.namespace('__setitem__').call(key, value)
        return thing
    elif type(primitive) is set:
        thing = instantiate(builtin.set)
        for key in primitive:
            thing.namespace('add').call(key)
        return thing
    _class = {
        int  : builtin.int  , 
        float: builtin.float, 
        str  : builtin.str  , 
        list : builtin.list , 
        tuple: builtin.tuple, 
    }[type(primitive)]
    thing = instantiate(_class)
    thing.primitive_value = primitive
    return thing

def assertPrimitive(thing):
    if thing.primitive_value is rt.NULL:
        raise rt.Helicopter(
            builtin.TypeError, 
            'This operation for non-primitives are not implemented.', 
        )

def isTrue(thing : rt.Thing) -> bool:
    if thing.namespace['__bool__'].call().primitive_value:
        return builtin.__true__
    return builtin.__false__

def wrapFuncion(func):
    thing = instantiate(builtin.Function)
    def wrapped(*args, **kw):
        try:
            return func(*args, **kw)
        except TypeError as e:
            if 'argument' in e.args[0].lower():
                raise rt.Helicopter(
                    builtin.TypeError, 
                    'Builtin function ' + str(e), 
                )
            else:
                raise e
    thing.call = wrapped
    thing.namespace['__name__'] = '(builtin) ' + func.__name__
    return thing

def wrapClass(base = None):
    def _wrapClass(cls):
        thing = instantiate(builtin.Class)
        for key, value in cls.__dict__.items():
            print('   ', key)
            thing.namespace[key] = value
        thing.namespace['__name__'] = unprimitize(cls.__name__)
        if base is not None:
            thing.namespace['__base__'] = base
        return thing
    return _wrapClass

def promotePythonException(e):
    minipyException = {
        StopIteration    : builtin.StopIteration, 
        NameError        : builtin.NameError, 
        TypeError        : builtin.TypeError, 
        IndexError       : builtin.IndexError, 
        KeyError         : builtin.KeyError, 
        AttributeError   : builtin.AttributeError, 
        ImportError      : builtin.ImportError, 
        KeyboardInterrupt: builtin.KeyboardInterrupt, 
        ValueError       : builtin.ValueError, 
    }.get(type(e), builtin.PythonException)
    raise rt.Helicopter(
        minipyException, 
        e.args[0], 
    )

class KeyEncoding: 
    def __hash__(self):
        raise NotImplemented
def encodeKey(thing : rt.Thing):
    if thing.primitive_value is rt.NULL:
        return thing
    return thing.primitive_value
def decodeKey(key):
    if type(key) is rt.Thing:
        return key
    return unprimitize(key)

def reprString(thing):
    return builtin.repr.call(thing).primitive_value

class builtin:
    Class = rt.Thing()
    Class._class = Class
    Class.namespace['__name__'] = 'Class'
    Class.namespace['__repr__'] = wrapFuncion(
        lambda thing : unprimitize(
            f'<class "{thing.namespace["__name__"]}">'
        )
    )
    Class.namespace['__str__'] = Class.namespace['__repr__']
    Class.namespace['__dict__'] = wrapFuncion(
        lambda self : unprimitize(self.namespace)
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
            return builtin.__none__
        
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
            return builtin.__none__
        
        @wrapFuncion
        def __repr__(thing):
            return 'None'
    __none__ = instantiate(NoneType)
    
    @wrapClass()
    class Exception:
        @wrapFuncion
        def __init__(thing, *args):
            thing.namespace['args'] = unprimitize(args)
            return builtin.__none__
        
        @wrapFuncion
        def __repr__(thing):
            return unprimitize(
                thing._class.namespace['__name__'].primitive_value 
                + reprString(thing.namespace['args'])
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
    class ValueError: pass
    @wrapClass(base = Exception)
    class PythonException: pass

    @wrapClass()
    class GenericPrimitive:        
        @wrapFuncion
        def __repr__(thing):
            return unprimitize(repr(thing.primitive_value))
        
        @wrapFuncion
        def __add__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value + b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __mul__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value * b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __mod__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value % b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __truediv__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value / b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __pow__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value ** b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __neg__(thing):
            try:
                primitive_value = - thing.primitive_value
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __eq__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value == b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __lt__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value < b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __gt__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value > b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __le__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value <= b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __ge__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value >= b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __bool__(thing):
            try:
                if thing.primitive_value:
                    return builtin.__true__
                return builtin.__false__
            except Exception as e:
                promotePythonException(e)
        
        @wrapFuncion
        def __int__(thing):
            try:
                return unprimitize(int(
                    thing.primitive_value
                ))
            except Exception as e:
                promotePythonException(e)
        
        @wrapFuncion
        def __float__(thing):
            try:
                return unprimitize(float(
                    thing.primitive_value
                ))
            except Exception as e:
                promotePythonException(e)
        
        @wrapFuncion
        def __str__(thing):
            try:
                return unprimitize(str(
                    thing.primitive_value
                ))
            except Exception as e:
                promotePythonException(e)
        
        @wrapFuncion
        def copy(thing):
            other = instantiate(thing._class)
            other.primitive_value = thing.primitive_value
            return other
    
    @wrapClass(base = GenericPrimitive)
    class int:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = 0
            if x is None:
                pass
            else:
                try:
                    thing.primitive_value = x.namespace[
                        '__int__'
                    ].call().primitive_value
                except Exception as e:
                    promotePythonException(e)
            return builtin.__none__
    
    @wrapClass(base = GenericPrimitive)
    class float:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = 0.0
            if x is None:
                pass
            else:
                try:
                    thing.primitive_value = x.namespace[
                        '__float__'
                    ].call().primitive_value
                except Exception as e:
                    promotePythonException(e)
            return builtin.__none__
    
    @wrapClass(base = GenericPrimitive)
    class str:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = ''
            if x is None:
                pass
            else:
                try:
                    thing.primitive_value = x.namespace[
                        '__str__'
                    ].call().primitive_value
                except Exception as e:
                    promotePythonException(e)
            return builtin.__none__
    
    @wrapClass(base = GenericPrimitive)
    class slice:
        @wrapFuncion
        def __init__(thing, *args):
            safeArgs = []
            for arg in args:
                if type(arg.primitive_value) is not int:
                    raise TypeError(
                        '`slice` arguments must be `int`.'
                    )
                safeArgs.append(arg.primitive_value)
            start = 0
            step = 1
            if len(safeArgs) < 1:
                raise TypeError('`slice` expects at least one argument.')
            elif len(safeArgs) == 1:
                stop, = safeArgs
            elif len(safeArgs) == 2:
                start, stop = safeArgs
            elif len(safeArgs) == 3:
                start, stop, step = safeArgs
            else:
                raise TypeError('`slice` expects at most four arguments.')
            thing.primitive_value = slice(start, stop, step)
            thing.namespace['start'] = unprimitize(start)
            thing.namespace['step']  = unprimitize(step )
            thing.namespace['stop']  = unprimitize(stop )
            return builtin.__none__
    
    @wrapClass(base = GenericPrimitive)
    class ListAndTuple:
        @wrapFuncion
        def __getitem__(thing, index_or_slice):
            assertPrimitive(index_or_slice)
            try:
                result = thing.primitive_value[
                    index_or_slice.primitive_value
                ]
            except Exception as e:
                promotePythonException(e)
            if type(index_or_slice.primitive_value) is slice:
                return unprimitize(result)
            return result
        
        @wrapFuncion
        def __len__(thing):
            return unprimitize(len(thing.primitive_value))
        
        @wrapFuncion
        def index(thing, item):
            try:
                return thing.primitive_value.index(item)
            except Exception as e:
                promotePythonException(e)
        
    @wrapClass(base = ListAndTuple)
    class list:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = []
            if x is None:
                pass
            else:
                thing.primitive_value = [*rt.ThingIter(x)]
            return builtin.__none__
        
        @wrapFuncion
        def __setitem__(thing, index_or_slice, value):
            assertPrimitive(index_or_slice)
            if type(index_or_slice.primitive_value) is slice:
                value = value.primitive_value
            try:
                thing.primitive_value[
                    index_or_slice.primitive_value
                ] = value
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__

        @wrapFuncion
        def clear(thing):
            thing.primitive_value.clear()
            return builtin.__none__

        @wrapFuncion
        def append(thing, other):
            thing.primitive_value.append(other)
            return builtin.__none__

        @wrapFuncion
        def pop(thing, index):
            try:
                return thing.primitive_value.pop(index.primitive_value)
            except Exception as e:
                promotePythonException(e)
        
        @wrapFuncion
        def extend(thing, other):
            assertPrimitive(other)
            try:
                thing.primitive_value.extend(
                    other.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__
        
        @wrapFuncion
        def remove(thing, item):
            try:
                return thing.primitive_value.remove(item)
            except Exception as e:
                promotePythonException(e)
        
        @wrapFuncion
        def sort(thing, key = None, reverse = False):
            if key is not None:
                raise rt.Helicopter(
                    builtin.Exception, 
                    'MiniPy does not support sorting with key.', 
                )
            if not all([
                x._class in (
                    builtin.int, builtin.float, builtin.str, 
                ) for x in thing.primitive_value
            ]):
                raise rt.Helicopter(
                    builtin.Exception, 
                    'MiniPy only supports sorting list of int, float, str.', 
                )
            if type(reverse) is rt.Thing:
                reverse = isTrue(reverse)
            try:
                thing.primitive_value.sort(key = lambda x : (
                    x.primitive_value
                ), reverse = reverse)
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__
    
    @wrapClass(base = ListAndTuple)
    class tuple:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = ()
            if x is None:
                pass
            else:
                thing.primitive_value = tuple(
                    *rt.ThingIter(x), 
                )
            return builtin.__none__
    
    @wrapClass(base = GenericPrimitive)
    class dict:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = {}
            if x is None:
                return builtin.__none__
            if x._class is builtin.dict:
                thing.primitive_value = x.primitive_value
                return builtin.__none__
            raise rt.Helicopter(
                builtin.Exception, 
                'MiniPy does not support casting into dict.', 
            )
            # return builtin.__none__

        @wrapFuncion
        def __getitem__(thing, keyThing):
            encoding = encodeKey(keyThing)
            try:
                return thing.primitive_value[
                    encoding
                ]
            except KeyError:
                raise rt.Helicopter(
                    builtin.KeyError, 
                    'No key ' + reprString(keyThing)
                )
            except Exception as e:
                promotePythonException(e)
        
        @wrapFuncion
        def __setitem__(thing, keyThing, value):
            encoding = encodeKey(keyThing)
            try:
                thing.primitive_value[
                    encoding
                ] = value
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__
        
        @wrapFuncion
        def __iter__(thing):
            l = unprimitize([
                decodeKey(x) 
                for x in thing.primitive_value.keys()
            ])
            return builtin.iter.call(l)
        
        @wrapFuncion
        def clear(thing):
            thing.primitive_value.clear()
            return builtin.__none__
        
        get = __getitem__
        
        @wrapFuncion
        def items(thing):
            l = instantiate(builtin.list)
            for key, value in thing.primitive_value.items():
                l.namespace['append'].call(unprimitize(
                    (decodeKey(key), value), 
                ))
            return builtin.iter.call(l)

        @wrapFuncion
        def pop(thing, keyThing):
            encoding = encodeKey(keyThing)
            try:
                return thing.primitive_value.pop(encoding)
            except Exception as e:
                promotePythonException(e)

        @wrapFuncion
        def update(thing, other):
            if type(other.primitive_value) is not dict:
                raise rt.Helicopter(
                    builtin.TypeError, 
                    'Updating a dict expects another dict.', 
                )
            thing.primitive_value.update(other.primitive_value)
            return builtin.__none__
    
    @wrapClass(base = GenericPrimitive)
    class set:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = set()
            if x is None:
                return builtin.__none__
            if x._class is builtin.set:
                thing.primitive_value = x.primitive_value
                return builtin.__none__
            try:
                thing.primitive_value = set([
                    encodeKey(element) 
                    for element in rt.ThingIter(x)
                ])
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__
        
        @wrapFuncion
        def __iter__(thing):
            l = unprimitize([
                decodeKey(x) 
                for x in thing.primitive_value
            ])
            return builtin.iter.call(l)
        
        @wrapFuncion
        def add(thing, other):
            try:
                thing.primitive_value.add(encodeKey(other))
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__
        
        @wrapFuncion
        def clear(thing):
            thing.primitive_value.clear()
            return builtin.__none__
        
        @wrapFuncion
        def discard(thing, other):
            encoding = encodeKey(other)
            thing.primitive_value.discard(encoding)
            return builtin.__none__
        
        @wrapFuncion
        def intersection(thing, other):
            if type(other.primitive_value) is not set:
                raise rt.Helicopter(
                    builtin.TypeError, 
                    'Can onlt intersect with another set, '
                    + f'not {reprString(other)}', 
                )
            newSet = instantiate(builtin.set)
            newSet = thing.primitive_value.intersection(
                other.primitive_value, 
            )
            return newSet
        
        @wrapFuncion
        def union(thing, other):
            if type(other.primitive_value) is not set:
                raise rt.Helicopter(
                    builtin.TypeError, 
                    'Can onlt union with another set, '
                    + f'not {reprString(other)}', 
                )
            newSet = instantiate(builtin.set)
            newSet = thing.primitive_value.union(
                other.primitive_value, 
            )
            return newSet
        
        @wrapFuncion
        def pop(thing):
            try:
                result = thing.primitive_value.pop()
            except Exception as e:
                promotePythonException(e)
            return decodeKey(result)

    @wrapFuncion
    def repr(x : rt.Thing):
        result = x._class.namespace['__repr__'].call(x)
        if result._class is builtin.str:
            return result
        raise rt.Helicopter(
            builtin.TypeError, 
            '__repr__ did not return a str.', 
        )

    del GenericPrimitive, ListAndTuple
