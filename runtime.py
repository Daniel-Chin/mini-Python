from typing import List, Dict
from lexer import Lexer, LookAheadIO
from .parser import (
    CmdTree, ExpressionTree, FunctionArg, Sequence, CmdsParser, 
    Conditional, WhileLoop, ForLoop, TryExcept, 
    FunctionDefinition, ClassDefinition, 
)
from builtin import builtin
from execEval import evalExpression, executeCmdTree, assignTo

class Thing:
    def __init__(self) -> None:
        self._class : Thing = None
        self.namespace = {}

        # if it is a function
        self.environment = []
        self.mst : FunctionDefinition = None
        self.default_args : Dict[str, Thing] = {}
        self.bound_args = []

        # if it is a primitive
        self.primitive_value = None
    
    def copy(self):
        thing = Thing()
        thing._class          = self._class
        thing.namespace       = self.namespace
        thing.environment     = self.environment
        thing.mst             = self.mst
        thing.default_args    = self.default_args
        thing.bound_args      = self.bound_args
        thing.primitive_value = self.primitive_value
        return thing
    
    def call(self, *args, **keyword_args):
        args = self.bound_args + args
        if self._class is builtin.Function:
            return executeFunction(self, args, keyword_args)
        elif self._class is builtin.Class:
            return instantiate(self, *args, **keyword_args)
        else: 
            try:
                return self.namespace['__call__'].call(
                    *args, **keyword_args, 
                )
            except KeyError:
                raise Helicopter(instantiate(
                    builtin.TypeError, 
                    f'{builtin.repr.call(self)} is not callable.', 
                ))

class Environment(list):
    def assign(self, name : str, value : Thing):
        self[-1][name] = value
    
    def read(self, name : str):
        for namespace in reversed(self):
            try:
                return namespace[name]
            except KeyError:
                pass
        raise Helicopter(instantiate(
            builtin.NameError, f'name "{name}" is not defined.', 
        ))

class Helicopter(Exception): 
    def __init__(self, content = None):
        super().__init__()
        self.content : Thing = content
        self.stack = []
        self.during = None
class ReturnAsException(Exception):
    def __init__(self, content = None):
        super().__init__()
        self.content : Thing = content
class BreakAsException(Exception): pass

def executeFunction(
    func : Thing, args : List[Thing], 
    keyword_args : Dict[str, Thing], 
) -> Thing:
    argument_namespace = {}
    arg_names = [x.name for x in func.mst._def[1:]]
    for i, thing in enumerate(args):
        try:
            name = arg_names[i]
        except IndexError:
            ...
            raise Helicopter
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
    return executeSequence(
        func.mst.body, 
        [*func.environment, argument_namespace], 
    )

def executeScript(f) -> dict:
    lexer = Lexer(LookAheadIO(f))
    root = Sequence()
    root.parse(CmdsParser(lexer))
    namespace = builtin.__dict__.copy()
    returned = executeSequence(root, [namespace])
    if returned is not None:
        # 'return' outside function
        ...
    return namespace

def executeSequence(sequence : Sequence, environment) -> Thing:
    for subBlock in sequence:
        try:
            if type(subBlock) is CmdTree:
                executeCmdTree(subBlock, environment)
            elif type(subBlock) is Conditional:
                subBlock : Conditional
                condition = evalExpression(
                    subBlock.condition[0], environment, 
                )
                if isTrue(condition):
                    executeSequence(subBlock.then, environment)
                else:
                    for elIf in subBlock.elIfs:
                        condition = evalExpression(
                            elIf.condition[0], environment, 
                        )
                        if isTrue(condition):
                            executeSequence(elIf.then, environment)
                            break
                    else:
                        if subBlock._else is not None:
                            executeSequence(subBlock._else, environment)
            elif type(subBlock) is WhileLoop:
                subBlock : WhileLoop
                broken = False
                try:
                    while True:
                        condition = evalExpression(
                            subBlock.condition[0], environment, 
                        )
                        if isTrue(condition):
                            executeSequence(subBlock.body, environment)
                        else:
                            break
                except BreakAsException:
                    broken = True
                if not broken and subBlock._else is not None:
                    executeSequence(subBlock._else)
            elif type(subBlock) is ForLoop:
                subBlock : ForLoop
                loopVar : ExpressionTree = subBlock.condition[0]
                iterThing = ThingIter(evalExpression(
                    subBlock.condition[1], environment, 
                ))
                broken = False
                try:
                    for nextThing in iterThing:
                        assignTo(nextThing, loopVar, environment)
                        executeSequence(subBlock.body, environment)
                except BreakAsException:
                    broken = True
                if not broken and subBlock._else is not None:
                    executeSequence(subBlock._else)
            elif type(subBlock) is TryExcept:
                subBlock : TryExcept
                handlers = []
                for oneCatch in subBlock.oneCatches:
                    catching = evalExpression(oneCatch.catching[0], environment)
                    if catching._class is not builtin.Class:
                        ...
                        # cannot catch non-class
                    handlers.append((catching, oneCatch.handler))
                try:
                    executeSequence(subBlock._try, environment)
                except Helicopter as h:
                    raised : Thing = h.content
                    if raised._class is builtin.Class:
                        raisedClass = raised
                    else:
                        raisedClass = raised._class
                    for catching, handler in handlers:
                        if isSubclassOf(raisedClass, catching):
                            try:
                                executeSequence(handler, environment)
                            except Helicopter as innerH:
                                innerH.during = h
                                raise innerH
                            break
                    else:
                        raise h
                else:
                    if subBlock._else is not None:
                        executeSequence(subBlock._else, environment)
                finally:
                    if subBlock._finally is not None:
                        executeSequence(subBlock._finally, environment)
            elif type(subBlock) is FunctionDefinition:
                subBlock : FunctionDefinition
                identifier, *args = subBlock._def
                func = Thing()
                func._class = builtin.Function
                func.environment = environment
                func.mst = subBlock
                arg_names = set()
                mandatory_args_finished = False
                for arg in args:
                    arg: FunctionArg
                    name = arg.name.value
                    if name in arg_names:
                        ...
                        # duplicate argument name
                    arg_names.add(name)
                    if arg.value is None:
                        if mandatory_args_finished:
                            ...
                            # mandatory arg after optional arg
                    else:
                        mandatory_args_finished = True
                        defaultThing = evalExpression(arg.value, environment)
                        func.default_args[name] = defaultThing
                assignTo(func, identifier, environment)
            elif type(subBlock) is ClassDefinition:
                subBlock : ClassDefinition
                identifier, expressionTree = subBlock._class
                base = evalExpression(expressionTree, environment)
                if base._class is not builtin.Class:
                    ...
                    # cannot inherit from a non-class
                thisClass = Thing()
                thisClass._class = builtin.Class
                thisClass.namespace['__base__'] = base
                thisClass.namespace['__name__'] = identifier.value
                executeSequence(
                    subBlock.body, 
                    [*environment, thisClass.namespace], 
                )
                assignTo(thisClass, identifier, environment)
        except ReturnAsException as e:
            return e.content
        except Helicopter as e:
            ...

def isTrue(thing : Thing) -> bool:
    try:
        __bool__ = thing.namespace['__bool__']
    except KeyError:
        ...
        # not found
    return __bool__.call() is builtin.__true__

def isSubclassOf(potentialSubclass : Thing, potentialBaseclass : Thing):
    cursor = potentialSubclass
    while cursor is not potentialBaseclass:
        try:
            cursor = cursor.namespace['__base__']
            if cursor is not Thing:
                raise KeyError
        except KeyError:
            return False
    return True

def instantiate(theClass : Thing, *args, **keyword_args):
    thing = Thing()
    thing._class = theClass
    baseclass = theClass
    while True:
        __base__ = None
        for name, value in baseclass.namepsace.items():
            if name == '__base__':
                __base__ = value
            else:
                if name not in thing.namespace:
                    if value._class is builtin.Function:
                        value = value.copy()
                        value.bound_args.append(thing)
                    thing.namespace[name] = value
        if __base__ is None:
            break
        baseclass = __base__
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

def ThingIter(thing : Thing):
    theIter : Thing = thing.namespace['__iter__'].call()
    while True:
        try:
            nextThing = theIter.namespace['__next__'].call()
        except Helicopter as h:
            if h.content._class is builtin.StopIteration:
                return
            raise h
        else:
            yield nextThing

def isSame(a : Thing, b : Thing):
    if a is b:
        return True
    if a.primitive_value is not None and b.primitive_value is not None:
        return a.primitive_value is b.primitive_value
