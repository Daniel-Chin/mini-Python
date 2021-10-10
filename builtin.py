from runtime import Thing

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

    def repr(self, x : Thing):
        return x._class.namespace['__repr__'].call(x)

    Function = Thing()
    Function._class = Class
    Function.namespace['__name__'] = 'Function'

    bool = Thing()
    bool._class = Class
    bool.namespace['__name__'] = 'bool'
    bool.namespace['__repr__'] = wrapFuncion(
        lambda self : 'True' if self is __true__ else 'False'
    )
    __true__ = Thing()
    __true__._class = bool
    __false__ = Thing()
    __false__._class = bool

    Exception = Thing()
    Exception._class = Class
    Exception.namespace['__name__'] = 'Exception'
    def initException(exception, *args):
        exception.namespace['args'] = args
    Exception.namespace['__init__'] = wrapFuncion(
        initException
    )
    Exception.namespace['__repr__'] = wrapFuncion(
        lambda self : self.namespace['__name__'] + repr(self.args)
    )

    StopIteration = Thing()
    StopIteration._class = Class
    StopIteration.namespace['__base__'] = Exception
    StopIteration.namespace['__name__'] = 'StopIteration'
    NameError = Thing()
    NameError._class = Class
    NameError.namespace['__base__'] = Exception
    NameError.namespace['__name__'] = 'NameError'

    def __init__(self):
        ...
    
    def type(self, x : Thing):
        return x._class

builtin = Builtin()
