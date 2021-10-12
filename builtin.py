from runtime import Helicopter, Thing, instantiate, unprimitize

def wrapFuncion(func):
    thing = Thing()
    thing._class = builtin.Function
    thing.call = func
    return thing

class Builtin:
    Class = Thing()
    Class._class = Class
    Class.namespace['__name__'] = 'Class'
    Class.namespace['__repr__'] = wrapFuncion(
        lambda self : f'<class "{self.namespace["__name__"]}">'
    )
    Class.namespace['__init__'] = wrapFuncion(
        lambda _ : None
    )
    def tempFunc(a):
        if a.primitive_value is not None:
            try:
                return hash(a.primitive_value)
            except TypeError:
                pass
        ...
        # unhashable type
    Class.namespace['__hash__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc

    Function = Thing()
    Function._class = Class
    Function.namespace['__name__'] = 'Function'

    bool = Thing()
    bool._class = Class
    bool.namespace['__name__'] = 'bool'
    bool.namespace['__repr__'] = wrapFuncion(
        lambda self : 'True' if self is builtin.__true__ else 'False'
    )
    bool.namespace['__bool__'] = wrapFuncion(
        lambda self : self
    )
    __true__  = instantiate(bool)
    __true__ ._class = bool
    __false__ = instantiate(bool)
    __false__._class = bool

    Exception = Thing()
    Exception._class = Class
    Exception.namespace['__name__'] = 'Exception'
    def tempFunc(exception, *args):
        exception.namespace['args'] = instantiate(
            builtin.tuple, args, 
        )
    Exception.namespace['__init__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    Exception.namespace['__repr__'] = wrapFuncion(
        lambda self : self.namespace['__name__'] + builtin.repr.call(self.args)
    )

    StopIteration = Thing()
    StopIteration._class = Class
    StopIteration.namespace['__base__'] = Exception
    StopIteration.namespace['__name__'] = 'StopIteration'
    NameError = Thing()
    NameError._class = Class
    NameError.namespace['__base__'] = Exception
    NameError.namespace['__name__'] = 'NameError'
    TypeError = Thing()
    TypeError._class = Class
    TypeError.namespace['__base__'] = Exception
    TypeError.namespace['__name__'] = 'TypeError'
    IndexError = Thing()
    IndexError._class = Class
    IndexError.namespace['__base__'] = Exception
    IndexError.namespace['__name__'] = 'IndexError'
    KeyError = Thing()
    KeyError._class = Class
    KeyError.namespace['__base__'] = Exception
    KeyError.namespace['__name__'] = 'KeyError'
    AttributeError = Thing()
    AttributeError._class = Class
    AttributeError.namespace['__base__'] = Exception
    AttributeError.namespace['__name__'] = 'AttributeError'

    NoneType = Thing()
    NoneType._class = Class
    NoneType.namespace['__name__'] = 'NoneType'
    NoneType.namespace['__repr__'] = wrapFuncion(
        lambda _ : 'None'
    )
    __none__ = instantiate(NoneType)
    __none__._class = NoneType
    __none__.primitive_value = None

    int = Thing()
    int._class = Class
    int.namespace['__name__'] = 'int'
    int.namespace['__repr__'] = wrapFuncion(
        lambda self : repr(self.primitive_value)
    )
    def tempFunc(intSelf, x = 0):
        intSelf.primitive_value = x
    int.namespace['__init__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        thing = instantiate(a._class)
        try:
            thing.primitive_value = a.primitive_value + b.primitive_value
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''"{
                    builtin.repr.call(a._class)
                }" cannot add "{builtin.repr.call(b._class)}"'''
            ))
    int.namespace['__add__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        thing = instantiate(a._class)
        try:
            thing.primitive_value = a.primitive_value % b.primitive_value
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''"{
                    builtin.repr.call(a._class)
                }" cannot mod "{builtin.repr.call(b._class)}"'''
            ))
    int.namespace['__mod__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        thing = instantiate(a._class)
        try:
            thing.primitive_value = a.primitive_value * b.primitive_value
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''"{
                    builtin.repr.call(a._class)
                }" cannot multiply "{builtin.repr.call(b._class)}"'''
            ))
    int.namespace['__mul__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        thing = instantiate(a._class)
        try:
            thing.primitive_value = a.primitive_value / b.primitive_value
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''"{
                    builtin.repr.call(a._class)
                }" cannot divide "{builtin.repr.call(b._class)}"'''
            ))
    int.namespace['__truediv__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        thing = instantiate(a._class)
        try:
            thing.primitive_value = a.primitive_value ** b.primitive_value
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''"{
                    builtin.repr.call(a._class)
                }" cannot power "{builtin.repr.call(b._class)}"'''
            ))
    int.namespace['__pow__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a):
        thing = instantiate(a._class)
        try:
            thing.primitive_value = - a.primitive_value
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''"{
                    builtin.repr.call(a._class)
                }" cannot be negated. '''
            ))
    int.namespace['__neg__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        if a.primitive_value == b.primitive_value:
            return builtin.__true__
        return builtin.__false__
    int.namespace['__eq__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        try:
            if a.primitive_value < b.primitive_value:
                return builtin.__true__
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''{
                    builtin.repr.call(a._class)
                } < {
                    builtin.repr.call(b._class)
                } unsupported. '''
            ))
        return builtin.__false__
    int.namespace['__lt__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        try:
            if a.primitive_value > b.primitive_value:
                return builtin.__true__
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''{
                    builtin.repr.call(a._class)
                } > {
                    builtin.repr.call(b._class)
                } unsupported. '''
            ))
        return builtin.__false__
    int.namespace['__gt__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        try:
            if a.primitive_value <= b.primitive_value:
                return builtin.__true__
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''{
                    builtin.repr.call(a._class)
                } <= {
                    builtin.repr.call(b._class)
                } unsupported. '''
            ))
        return builtin.__false__
    int.namespace['__le__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        try:
            if a.primitive_value >= b.primitive_value:
                return builtin.__true__
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''{
                    builtin.repr.call(a._class)
                } >= {
                    builtin.repr.call(b._class)
                } unsupported. '''
            ))
        return builtin.__false__
    int.namespace['__ge__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    int.namespace['__bool__'] = wrapFuncion(
        lambda self : builtin.__true__ if self.primitive_value else builtin.__false__
    )

    float = Thing()
    float._class = Class
    float.namespace = int.namespace.copy()
    float.namespace['__name__'] = 'float'
    def tempFunc(floatSelf, x = 0.):
        floatSelf.primitive_value = x
    float.namespace['__init__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc

    str = Thing()
    str._class = Class
    str.namespace = int.namespace.copy()
    str.namespace['__name__'] = 'str'
    def tempFunc(strSelf, x = ''):
        strSelf.primitive_value = x
    str.namespace['__init__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc

    list = Thing()
    list._class = Class
    list.namespace = int.namespace.copy()
    list.namespace['__name__'] = 'list'
    def tempFunc(listSelf, x = []):
        listSelf.primitive_value = list(x)
    list.namespace['__init__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(listSelf, index):
        try:
            result = listSelf.primitive_value[
                index.primitive_value
            ]
            if type(result) is Thing:
                return result
            return unprimitize(result)
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''"{
                    builtin.repr(index._class)
                }" cannot be index/key.'''
            ))
        except IndexError:
            raise Helicopter(instantiate(
                builtin.IndexError, f'''Index {
                    repr(index.primitive_value)
                } invalid.'''
            ))
        except KeyError:
            raise Helicopter(instantiate(
                builtin.KeyError, f'''Key {
                    repr(index.primitive_value)
                } invalid.'''
            ))
    list.namespace['__getitem__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(listSelf, slice_as_tuple):
        t = []
        for x in slice_as_tuple.primitive_value:
            t.append(x.primitive_value)
        result = listSelf.primitive_value[
            slice(*t)
        ]
        return instantiate(listSelf._class, (
            x if type(x) is Thing else unprimitize(x)
            for x in result
        ))
    list.namespace['__slice__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(listSelf, key, value):
        ...
    list.namespace['__setitem__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(listSelf, element):
        if element in listSelf.primitive_value:
            return builtin.__true__
        return builtin.__false__
    list.namespace['__contains__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc

    tuple = Thing()
    tuple._class = Class
    tuple.namespace = list.namespace.copy()
    tuple.namespace['__name__'] = 'tuple'
    def tempFunc(tupleSelf, x = ()):
        tupleSelf.primitive_value = tuple(x)
    tuple.namespace['__init__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc

    dict = Thing()
    dict._class = Class
    dict.namespace = list.namespace.copy()
    dict.namespace['__name__'] = 'dict'
    def tempFunc(dictSelf, x = {}):
        dictSelf.primitive_value = x.copy()
    dict.namespace['__init__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc

    set = Thing()
    set._class = Class
    set.namespace = list.namespace.copy()
    set.namespace['__name__'] = 'set'
    def tempFunc(setSelf, x = set()):
        setSelf.primitive_value = set(x)
    set.namespace['__init__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc

    @wrapFuncion
    def type(self, x : Thing):
        return x._class
    
    @wrapFuncion
    def hash(self, x : Thing):
        return x.namespace['__hash__'].call()
    
    @wrapFuncion
    def repr(self, x : Thing):
        return x._class.namespace['__repr__'].call(x)

builtin = Builtin()
