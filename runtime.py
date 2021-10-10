from typing import List, Dict
from lexems import Identifier
from lexer import Lexer, LookAheadIO
from .parser import (
    CmdTree, ExpressionTree, FunctionArg, Sequence, CmdsParser, 
    Conditional, WhileLoop, ForLoop, TryExcept, 
    FunctionDefinition, ClassDefinition, 
)
from builtin import builtin

class Thing:
    def __init__(self) -> None:
        self._class : Thing = None
        self.namespace = {}

        # if it is a function
        self.environment = []
        self.mst : FunctionDefinition = None
        self.default_args : Dict[str, Thing] = {}

        # if it is a primitive
        self.primitive_value = None
    
    def call(self, args = [], keyword_args = {}):
        if self._class is builtin.Function:
            return executeFunction(self, args, keyword_args)
        elif self._class is builtin.Class:
            ...
        else: 
            try:
                return self.namespace['__call__'].call(
                    args, keyword_args, 
                )
            except KeyError:
                ...

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

class Helicopter(Exception): 
    def __init__(self, content = None):
        super().__init__()
        self.content : Thing = content
        self.stackOfStack = []
        # Inner stack: stack trace. Outer stack: "During handling of the above exception"
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
    return executeSequence(
        func.mst.body, 
        [*func.environment, argument_namespace], 
    )

def executeScript(f):
    lexer = Lexer(LookAheadIO(f))
    root = Sequence()
    root.parse(CmdsParser(lexer))
    namespace = builtin.__dict__.copy()
    returned = executeSequence(root, [namespace])
    if returned is not None:
        # 'return' outside function
        ...

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
                theIter : Thing = evalExpression(
                    subBlock.condition[1], environment, 
                ).namespace['__iter__'].call()
                broken = False
                try:
                    while True:
                        try:
                            nextThing = theIter.namespace['__next__'].call()
                        except Helicopter as e:
                            if e.content._class is builtin.StopIteration:
                                break
                            raise e
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
                except Helicopter as e:
                    raised : Thing = e.content
                    if raised._class is builtin.Class:
                        raisedClass = raised
                    else:
                        raisedClass = raised._class
                    for catching, handler in handlers:
                        if isSubclassOf(raisedClass, catching):
                            executeSequence(handler, environment)
                            break
                    else:
                        raise e
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
    return thing.namespace['__bool__'].call() is builtin.__true__

def evalExpression(expressionTree, environment : Environment) -> Thing:
    ...

def executeCmdTree(cmdTree : CmdTree, environment : Environment):
    pass

def assignTo(
    thing : Thing, slot, 
    environment : Environment, 
):
    if type(slot) is Identifier:
        ...
    elif type(slot) is ExpressionTree:
        ...
    else:
        raise TypeError(
            'Cannot assign to non-Identifier non-ExpressionTree. '
        )

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
