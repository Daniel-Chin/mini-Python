from typing import List, Dict
from parser import Sequence, FunctionDefinition, FunctionArg

class Thing:
    def __init__(self) -> None:
        self.type : Type = None
        self.namespace = {}

        # if it is a function
        self.environment = []
        self.mst : FunctionDefinition = None
        self.default_args = {}

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

class Helicopter(Exception): 
    def __init__(self, content = None):
        super().__init__()
        self.content : Thing = content
        self.stack = []

class Environment(list):
    def assign(self, name, value : Thing):
        self[-1][name] = value
    
    def read(self, name):
        for namespace in reversed(self):
            try:
                return namespace[name]
            except KeyError:
                pass
        raise Helicopter(NameError(f'name "{name}" is not defined.'))
        # No! this needs to be an in-user exception. todo

def executeSequence(sequence : Sequence, environment):
    ...

def executeFunction(
    func : Thing, args : List[Thing], 
    keyword_args : Dict[str, Thing], 
):
    argument_namespace = {}
    arg_names = [x.name for x in func.mst._def[1:]]
    for i, thing in enumerate(args):
        try:
            name = arg_names[i]
        except IndexError:
            raise Helicopter
            # todo
        argument_namespace[name] = thing
    if func.mst._def[i + 2].value is None:
        # not enough args. 
        ...
    for name, thing in keyword_args.items():
        if name in arg_names:
            if name in argument_namespace:
                # multiple values for argument
                ...
            argument_namespace[name] = thing
        else:
            # unknown argument
            ...
    argument_namespace = {
        **func.default_args, **argument_namespace, 
    }
    func.environment.append(argument_namespace)

def executeScript():
    ...
