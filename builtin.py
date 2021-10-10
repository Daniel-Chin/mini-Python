from runtime import Thing

def wrapFuncion(func):
    thing = Thing()
    thing._class = builtin.Function
    thing.call = func

def setBuiltinRepr(thing, name, is_class = True):
    thing.namespace['__repr__'] = wrapFuncion(
        lambda: f'<builtin class "{name}">'
        if is_class else
        lambda: name
    )

class Builtin:
    Class = Thing()
    Class._class = Class
    setBuiltinRepr(Class, 'Class')

    Function = Thing()
    Function._class = Class
    setBuiltinRepr(Function, 'Function')

    bool = Thing()
    bool._class = Class
    setBuiltinRepr(bool, 'bool')
    __true__ = Thing()
    __true__._class = bool
    setBuiltinRepr(__true__, 'True', is_class=False)
    __false__ = Thing()
    __false__._class = bool
    setBuiltinRepr(__false__, 'False', is_class=False)

    Exception = Thing()
    Exception._class = Class
    setBuiltinRepr(Exception, 'Exception')
    StopIteration = Thing()
    StopIteration._class = Exception
    setBuiltinRepr(StopIteration, 'StopIteration')

    def __init__(self):
        ...
    
    def type(self, x : Thing):
        return x._class

builtin = Builtin()
