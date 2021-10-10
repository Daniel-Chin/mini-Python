class Thing:
    def __init__(self) -> None:
        self.type : Type = None
        self.namespace = {}

        # if it is a function
        self.environment = []
        self.mst = None

        self.builtin_repr = None
    
    def call(self):
        if self.type is Function:
            ...
        else: 
            try:
                return self.environment['__call__'].call()
            except KeyError:
                ...
    
    def repr(self):
        if self.builtin_repr is None:
            return self.namespace['__repr__'].call()
        else:
            return self.builtin_repr()

class Type: pass
class UserType(Type): 
    def __init__(self) -> None:
        self.thingTemplate : Thing = None
class BuiltinType(Type): pass
class Function(BuiltinType): pass
class ThingTemplate(BuiltinType): pass
