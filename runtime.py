class Thing:
    def __init__(self) -> None:
        self.type : Type = None
        self.namespace = {}

        # if it is a function
        self.environment = []
        self.mst = None
    
    def call(self):
        if self.type is Function:
            ...
        else: 
            try:
                return self.environment['__call__'].call()
            except KeyError:
                ...

class Type: pass
class UserType(Type): 
    def __init__(self) -> None:
        self.thingTemplate : Thing = None
class BuiltinType(Type): pass
class Function(BuiltinType): pass
class ThingTemplate(BuiltinType): pass
