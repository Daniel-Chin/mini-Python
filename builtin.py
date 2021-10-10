from runtime import Helicopter, Thing, instantiate

def wrapFuncion(func):
    thing = Thing()
    thing._class = builtin.Function
    thing.call = func

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

    def repr(self, x : Thing):
        return x._class.namespace['__repr__'].call(x)

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
    __true__ = Thing()
    __true__._class = bool
    __false__ = Thing()
    __false__._class = bool

    Exception = Thing()
    Exception._class = Class
    Exception.namespace['__name__'] = 'Exception'
    def tempFunc(exception, *args):
        exception.namespace['args'] = instantiateTuple(*args)
    Exception.namespace['__init__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    Exception.namespace['__repr__'] = wrapFuncion(
        lambda self : self.namespace['__name__'] + builtin.repr(self.args)
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

    NoneType = Thing()
    NoneType._class = Class
    NoneType.namespace['__name__'] = 'NoneType'
    NoneType.namespace['__repr__'] = wrapFuncion(
        lambda _ : 'None'
    )
    __none__ = Thing()
    __none__._class = NoneType

    int = Thing()
    int._class = Class
    int.namespace['__name__'] = 'int'
    int.namespace['__repr__'] = wrapFuncion(
        lambda self : repr(self.primitive_value)
    )
    def tempFunc(a, b):
        thing = instantiate(a._class)
        try:
            thing.primitive_value = a.primitive_value + b.primitive_value
        except TypeError:
            raise Helicopter(instantiate(
                builtin.TypeError, f'''"{
                    builtin.repr(a._class)
                }" cannot add "{builtin.repr(b._class)}"'''
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
                    builtin.repr(a._class)
                }" cannot mod "{builtin.repr(b._class)}"'''
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
                    builtin.repr(a._class)
                }" cannot multiply "{builtin.repr(b._class)}"'''
            ))
    int.namespace['__mul__'] = wrapFuncion(
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
                    builtin.repr(a._class)
                }" cannot power "{builtin.repr(b._class)}"'''
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
                    builtin.repr(a._class)
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
        if a.primitive_value < b.primitive_value:
            return builtin.__true__
        return builtin.__false__
    int.namespace['__lt__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        if a.primitive_value > b.primitive_value:
            return builtin.__true__
        return builtin.__false__
    int.namespace['__gt__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        if a.primitive_value <= b.primitive_value:
            return builtin.__true__
        return builtin.__false__
    int.namespace['__le__'] = wrapFuncion(
        tempFunc
    )
    del tempFunc
    def tempFunc(a, b):
        if a.primitive_value >= b.primitive_value:
            return builtin.__true__
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

    str = Thing()
    str._class = Class
    str.namespace = int.namespace.copy()
    str.namespace['__name__'] = 'str'

    list = Thing()
    list._class = Class
    list.namespace = int.namespace.copy()
    list.namespace['__name__'] = 'list'

    tuple = Thing()
    tuple._class = Class
    tuple.namespace = int.namespace.copy()
    tuple.namespace['__name__'] = 'tuple'

    dict = Thing()
    dict._class = Class
    dict.namespace = int.namespace.copy()
    dict.namespace['__name__'] = 'dict'

    set = Thing()
    set._class = Class
    set.namespace = int.namespace.copy()
    set.namespace['__name__'] = 'set'

    def type(self, x : Thing):
        return x._class

builtin = Builtin()
