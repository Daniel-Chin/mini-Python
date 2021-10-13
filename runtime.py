from __future__ import annotations
import os
from typing import List, Dict, Set
from lexems import *
from lexer import Lexer
from parSer import (
    CmdTree, ExpressionTree, FunctionArg, Sequence, CmdsParser, 
    Conditional, WhileLoop, ForLoop, TryExcept, 
    AssignCmd, Empty, ExpressionCmd, 
    IsNot, NotIn, 
    FunctionDefinition, ClassDefinition, 
    Terminal, Parened, TupleDisplay, FunctionCall, 
    DictDisplay, SetDisplay, ListDisplay, Indexing, Slicing, 
    Binary, Unary, Attributing, ListComp, UnaryNegate, 
)
from builtin import assertPrimitive, builtin, instantiate, isTrue, reprString, unprimitize

class NULL: pass

class Thing:
    def __init__(self) -> None:
        self._class : Thing = None
        self.namespace = Namespace()

        # if it is a function
        self.environment = []
        self.mst : FunctionDefinition = None
        self.default_args : Dict[str, Thing] = {}
        self.bound_args = []
        self.runTime = None

        # if it is a primitive
        self.primitive_value = NULL
    
    def copy(self):
        thing = Thing()
        thing._class          = self._class
        thing.namespace       = self.namespace
        thing.environment     = self.environment
        thing.mst             = self.mst
        thing.default_args    = self.default_args
        thing.bound_args      = self.bound_args
        thing.primitive_value = self.primitive_value
        thing.runTime         = self.runTime
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
                raise Helicopter(
                    builtin.TypeError, 
                    f'{reprString(self)} is not callable.', 
                )
    
    def __hash__(self):
        if self.primitive_value is not NULL:
            return hash(self.primitive_value)
        result = self.namespace['__hash__'].call()
        assertPrimitive(result)
        return result.primitive_value

class Namespace(dict):
    def __init__(self):
        super().__init__()
        self.forbidden = set()
    
    def forbid(self, name):
        self.forbidden.add(name)
    
    def __getitem__(self, key):
        if key in self.forbidden:
            raise Helicopter(
                builtin.ImportError, 
                f'Accessing evaluation-postponed variable "{key}" during circular import.', 
            )
        else:
            try:
                return super().__getitem__(key)
            except KeyError:
                raise Helicopter(
                    builtin.NameError, 
                    f'Name "{key}" is not defined in namespace.', 
                )
    
    def __setitem__(self, key, value) -> None:
        try:
            self.forbidden.remove(key)
        except KeyError:
            pass
        return super().__setitem__(key, value)

class Environment(list):
    def assign(self, name : str, value : Thing):
        self[-1][name] = value
    
    def read(self, name : str):
        for namespace in reversed(self):
            if name in namespace:
                return namespace[name]
        raise Helicopter(
            builtin.NameError, f'name "{name}" is not defined in environment.', 
        )
    
    def delete(self, name : str):
        # raises KeyError
        self[-1].pop(name)

class Helicopter(Exception): 
    def __init__(self, minipyException, remark = ''):
        super().__init__()
        self.content : Thing = instantiate(
            minipyException, 
            unprimitize(remark), 
        )
        self.stack = []
        self.below = None
class ReturnAsException(Exception):
    def __init__(self, content = None):
        super().__init__()
        self.content : Thing = content
class BreakAsException(Exception): pass
class ContinueAsException(Exception): pass

def executeFunction(
    func : Thing, args : List[Thing], 
    keyword_args : Dict[str, Thing], 
) -> Thing:
    argument_namespace = Namespace()
    arg_names = [x.name for x in func.mst._def[1:]]
    i = -1
    for i, thing in enumerate(args):
        try:
            name = arg_names[i]
        except IndexError:
            raise Helicopter(
                builtin.TypeError, 
                reprString(func) + ' received too many arguments', 
            )
        argument_namespace[name] = thing
    if len(func.mst._def) > i + 2 and func.mst._def[
        i + 2
    ].value is None:
        raise Helicopter(
            builtin.TypeError, 
            reprString(func) + ' received not enough arguments', 
        )
    for name, thing in keyword_args.items():
        if name in arg_names:
            if name in argument_namespace:
                raise Helicopter(
                    builtin.TypeError, 
                    reprString(func) 
                    + ' got multiple values for argument `'
                    + name + '`.', 
                )
            argument_namespace[name] = thing
        else:
            raise Helicopter(
                builtin.TypeError, 
                reprString(func) 
                + ' got unknown named argument `'
                + name + '`.', 
            )
    argument_namespace = Namespace({
        **func.default_args, **argument_namespace, 
    })
    return executeSequence(
        func.runTime, 
        func.mst.body, 
        Environment([*func.environment, argument_namespace]), 
        func.namespace['__name__'].primitive_value, 
    )

def executeSequence(
    runTime, sequence : Sequence, environment, label : str, 
) -> Thing:
    for subBlock in sequence:
        try:
            if type(subBlock) is CmdTree:
                try:
                    executeCmdTree(runTime, subBlock, environment)
                except Helicopter as h:
                    recordStackTrace(h, label, subBlock)
                except KeyboardInterrupt:
                    raise Helicopter(
                        builtin.KeyboardInterrupt
                    )
            elif type(subBlock) is Conditional:
                subBlock : Conditional
                try:
                    condition = evalExpression(
                        subBlock.condition[0], environment, 
                    )
                except Helicopter as h:
                    recordStackTrace(h, label, subBlock.condition)
                if isTrue(condition):
                    executeSequence(runTime, subBlock.then, environment, label)
                else:
                    for elIf in subBlock.elIfs:
                        try:
                            condition = evalExpression(
                                elIf.condition[0], environment, 
                            )
                        except Helicopter as h:
                            recordStackTrace(h, label, elIf.condition)
                        if isTrue(condition):
                            executeSequence(runTime, elIf.then, environment, label)
                            break
                    else:
                        if subBlock._else is not None:
                            executeSequence(runTime, subBlock._else, environment, label)
            elif type(subBlock) is WhileLoop:
                subBlock : WhileLoop
                broken = False
                try:
                    while True:
                        try:
                            condition = evalExpression(
                                subBlock.condition[0], environment, 
                            )
                        except Helicopter as h:
                            recordStackTrace(h, label, subBlock.condition)
                        if isTrue(condition):
                            try:
                                executeSequence(runTime, subBlock.body, environment, label)
                            except ContinueAsException:
                                pass
                        else:
                            break
                except BreakAsException:
                    broken = True
                if not broken and subBlock._else is not None:
                    executeSequence(runTime, subBlock._else, environment, label)
            elif type(subBlock) is ForLoop:
                subBlock : ForLoop
                loopVar : ExpressionTree = subBlock.condition[0]
                try:
                    iterThing = ThingIter(evalExpression(
                        subBlock.condition[1], environment, 
                    ))
                except Helicopter as h:
                    recordStackTrace(h, label, subBlock.condition)
                broken = False
                try:
                    while True:
                        try:
                            nextThing = next(iterThing)
                        except StopIteration:
                            break
                        except Helicopter as h:
                            recordStackTrace(h, label, subBlock.condition)
                        assignTo(nextThing, loopVar, environment)
                        executeSequence(runTime, subBlock.body, environment, label)
                except BreakAsException:
                    broken = True
                if not broken and subBlock._else is not None:
                    executeSequence(runTime, subBlock._else, environment, label)
            elif type(subBlock) is TryExcept:
                subBlock : TryExcept
                handlers = []
                for oneCatch in subBlock.oneCatches:
                    try:
                        catching = evalExpression(oneCatch.catching[0], environment)
                    except Helicopter as h:
                        recordStackTrace(h, label, oneCatch.catching)
                    if catching._class is not builtin.Class:
                        raise Helicopter(
                            builtin.TypeError, 
                            f'{reprString(catching)} is a non-class, so miniPy cannot catch this.'
                        )
                    handlers.append((catching, oneCatch.handler))
                try:
                    executeSequence(runTime, subBlock._try, environment, label)
                except Helicopter as h:
                    raised : Thing = h.content
                    if raised._class is builtin.Class:
                        raisedClass = raised
                    else:
                        raisedClass = raised._class
                    for catching, handler in handlers:
                        if isSubclassOf(raisedClass, catching):
                            try:
                                executeSequence(runTime, handler, environment, label)
                            except Helicopter as innerH:
                                h.below = innerH
                                raise h
                            break
                    else:
                        raise h
                else:
                    if subBlock._else is not None:
                        executeSequence(runTime, subBlock._else, environment, label)
                finally:
                    if subBlock._finally is not None:
                        executeSequence(runTime, subBlock._finally, environment, label)
            elif type(subBlock) is FunctionDefinition:
                subBlock : FunctionDefinition
                identifier, *args = subBlock._def
                func = instantiate(builtin.Function)
                func.namespace['__name__'] = unprimitize(identifier.value)
                func.environment = environment
                func.mst = subBlock
                func.runTime = runTime
                arg_names = set()
                mandatory_args_finished = False
                try:
                    for arg in args:
                        arg: FunctionArg
                        name = arg.name.value
                        if name in arg_names:
                            raise Helicopter(
                                builtin.TypeError, 
                                'Duplicate argument name ' + name, 
                            )
                        arg_names.add(name)
                        if arg.value is None:
                            if mandatory_args_finished:
                                raise Helicopter(
                                    builtin.TypeError, 
                                    f'''Mandatory argument {
                                        name
                                    } after optional argument.''', 
                                )
                        else:
                            mandatory_args_finished = True
                            defaultThing = evalExpression(arg.value, environment)
                            func.default_args[name] = defaultThing
                except Helicopter as h:
                    recordStackTrace(h, label, subBlock._def)
                assignTo(func, identifier, environment)
            elif type(subBlock) is ClassDefinition:
                subBlock : ClassDefinition
                identifier, expressionTree = subBlock._class
                try:
                    base = evalExpression(expressionTree, environment)
                except Helicopter as h:
                    recordStackTrace(h, label, subBlock._class)
                if base._class is not builtin.Class:
                    raise Helicopter(
                        builtin.TypeError, 
                        reprString(base) + ' is a non-class. '
                        + 'New class cannot inherit from a non-class.', 
                    )
                thisClass = instantiate(builtin.Class)
                thisClass.namespace['__base__'] = base
                thisClass.namespace['__name__'] = unprimitize(identifier.value)
                executeSequence(
                    runTime, 
                    subBlock.body, 
                    [*environment, thisClass.namespace], 
                    identifier.value, 
                )
                assignTo(thisClass, identifier, environment)
        except ReturnAsException as e:
            return e.content

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

def ThingIter(thing : Thing):
    theIter : Thing = builtin.iter.call(thing)
    while True:
        try:
            nextThing = builtin.next.call(theIter)
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

class RunTime:
    class ImportJob:
        def __init__(self, filename, namespace):
            self.filename : str = filename
            self.namespace = namespace
            self.onDone = []
        
        def __bool__(self):
            return True

    def __init__(self, dir_location):
        self.dir_location = dir_location
        self.minipypaths = [*reversed(os.environ.get(
            'MINIPYPATH', '', 
        ).split(';'))]
        self._modules : Dict[str, dict] = {}
        # filename -> namespace
        self.nowImportJobs : Set[self.ImportJob] = set()
    
    def resolveName(self, name):
        parts = name.split('.')
        for base in [self.dir_location, *self.minipypaths]:
            filename = os.path.join(base, *parts) + '.minipy'
            if filename in os.listdir(os.path.dirname(filename)):
                return os.path.normpath(filename)
        else:
            raise Helicopter(
                builtin.ImportError, 
                f'Script "{name}" not found. Hint: ' 
                + 'Name is case-sensitive. ".minipy" ' 
                + 'extension is also case-sensitive.'
            )
    
    def getModule(self, name):
        filename = self.resolveName(name)
        return self._modules[filename]

    def isImportCircular(self, name):
        filename = self.resolveName(name)
        for job in self.nowImportJobs:
            if job.filename == filename:
                return job
        return False

    def imPort(self, name, __Name__):
        try:
            return self.getModule(name)
        except KeyError:
            pass
        assert not self.isImportCircular(name)
        filename = self.resolveName(name)
        namespace = Namespace({
            **builtin.__dict__.copy(), 
            '__name__': __Name__, 
        })
        job = self.ImportJob(filename, namespace)
        self.nowImportJobs.add(job)
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lexer = Lexer(f)
                root = Sequence()
                root.parse(CmdsParser(lexer, filename))
                returned = executeSequence(
                    self, root, [namespace], f'<module {name}>', 
                )
                if returned is not None:
                    raise Helicopter(
                        builtin.Exception, 
                        '"return" outside function.', 
                    )
        finally:
            self.nowImportJobs.remove(job)
        self._modules[filename] = namespace
        for func, cmdTree, environment in job.onDone:
            func(self, cmdTree, environment)
        return namespace

def evalExpression(
    eTree : ExpressionTree, 
    environment : Environment, 
) -> Thing:
    if eTree.type is Terminal:
        lexem = eTree[0]
        if type(lexem) is Num:
            if '.' in lexem.value:
                thing = unprimitize(float(lexem.value))
            else:
                thing = unprimitize(int(lexem.value))
        elif type(lexem) is String:
            thing = unprimitize(lexem.value)
        elif type(lexem) is Boolean:
            if lexem.value:
                thing = builtin.__true__
            else:
                thing = builtin.__false__
        elif type(lexem) is NONE:
            thing = builtin.__none__
        elif type(lexem) is Identifier:
            thing = environment.read(lexem.value)
        return thing
    elif eTree.type is Parened:
        return evalExpression(eTree[0], environment)
    elif eTree.type is TupleDisplay:
        return unprimitize(tuple(
            evalExpression(x, environment) for x in eTree
        ))
    elif eTree.type is ListDisplay:
        return unprimitize([
            evalExpression(x, environment) for x in eTree
        ])
    elif eTree.type is SetDisplay:
        s = set()
        for x in eTree:
            thing = evalExpression(x, environment)
            if thing.primitive_value is None:
                key = thing
            else:
                key = thing.primitive_value
            s.add(key)
        return unprimitize(s)
    elif eTree.type is DictDisplay:
        d = {}
        for keyTree, valueTree in eTree:
            keyThing = evalExpression(keyTree, environment)
            if keyThing.primitive_value is None:
                key = keyThing
            else:
                key = keyThing.primitive_value
            d[key] = evalExpression(valueTree, environment)
        return instantiate(builtin.dict, d)
    elif eTree.type is FunctionCall:
        calleeExpr, *funcArgs = eTree
        args = []
        keyword_args = {}
        positional_finished = False
        for funcArg in funcArgs:
            funcArg : FunctionArg
            if funcArg.name is None:
                if positional_finished:
                    raise Helicopter(
                        builtin.TypeError, 
                        'Positional argument after named arguments.', 
                    )
                args.append(evalExpression(funcArg.value, environment))
            else:
                positional_finished = True
                arg_name = funcArg.name.value
                if arg_name in keyword_args:
                    raise Helicopter(
                        builtin.TypeError, 
                        'Duplicate argument `' + arg_name + '`. ', 
                    )
                keyword_args[arg_name] = evalExpression(
                    funcArg.value, environment, 
                )
        return evalExpression(calleeExpr, environment).call(
            *args, **keyword_args, 
        )
    elif eTree.type is Indexing:
        indexee = evalExpression(eTree[0], environment)
        index = evalExpression(eTree[1], environment)
        return indexee.namespace['__getitem__'].call(index)
    elif eTree.type is Slicing:
        slicee = evalExpression(eTree[0], environment)
        start = evalExpression(eTree[1], environment)
        stop = evalExpression(eTree[2], environment)
        step = evalExpression(eTree[3], environment)
        return slicee.namespace['__getitem__'].call(
            instantiate(builtin.slice, start, stop, step), 
        )
    elif eTree.type is Empty:
        return builtin.__none__
    elif eTree.type is Binary:
        left = evalExpression(eTree[0], environment)
        if type(eTree.operationLexem) is Or:
            if isTrue(left):
                return left
            return evalExpression(eTree[1], environment)
        elif type(eTree.operationLexem) is And:
            if isTrue(left):
                return evalExpression(eTree[1], environment)
            return left
        else:
            right = evalExpression(eTree[1], environment)
        if type(eTree.operationLexem) is ToPowerOf:
            return left.namespace['__pow__'].call(right)
        elif type(eTree.operationLexem) is Times:
            return left.namespace['__mul__'].call(right)
        elif type(eTree.operationLexem) is Divide:
            return left.namespace['__truediv__'].call(right)
        elif type(eTree.operationLexem) is ModDiv:
            return left.namespace['__mod__'].call(right)
        elif type(eTree.operationLexem) is Plus:
            return left.namespace['__add__'].call(right)
        elif type(eTree.operationLexem) is Minus:
            return left.namespace['__add__'].call(
                right.namespace['__neg__'].call()
            )
        elif type(eTree.operationLexem) is Is:
            if isSame(left, right):
                return builtin.__true__
            return builtin.__false__
        elif type(eTree.operationLexem) is IsNot:
            if isSame(left, right):
                return builtin.__false__
            return builtin.__true__
        elif type(eTree.operationLexem) is In:
            if right.namespace['__contains__'].call(left):
                return builtin.__true__
            return builtin.__false__
        elif type(eTree.operationLexem) is NotIn:
            if right.namespace['__contains__'].call(left):
                return builtin.__false__
            return builtin.__true__
        elif type(eTree.operationLexem) is Equal:
            if left.namespace['__eq__'].call(right):
                return builtin.__true__
            return builtin.__false__
        elif type(eTree.operationLexem) is NotEqual:
            if left.namespace['__eq__'].call(right):
                return builtin.__false__
            return builtin.__true__
        elif type(eTree.operationLexem) is LessThan:
            if left.namespace['__lt__'].call(right):
                return builtin.__true__
            return builtin.__false__
        elif type(eTree.operationLexem) is GreaterThan:
            if left.namespace['__gt__'].call(right):
                return builtin.__true__
            return builtin.__false__
        elif type(eTree.operationLexem) is LessThanOrEqual:
            if left.namespace['__le__'].call(right):
                return builtin.__true__
            return builtin.__false__
        elif type(eTree.operationLexem) is GreaterThanOrEqual:
            if left.namespace['__ge__'].call(right):
                return builtin.__true__
            return builtin.__false__
    elif eTree.type is Unary:
        thing = evalExpression(eTree[0], environment)
        if type(eTree.operationLexem) is UnaryNegate:
            return thing.namespace['__neg__'].call()
        if type(eTree.operationLexem) is Not:
            if isTrue(thing):
                return builtin.__false__
            return builtin.__true__
    elif eTree.type is Attributing:
        thing = evalExpression(eTree[0], environment)
        name = eTree[1][0].value
        try:
            return thing.namespace[name]
        except KeyError:
            raise Helicopter(
                builtin.AttributeError, 
                f'''{
                    thing._class.namespace["__name__"].primitive_value
                } object does not have "{name}"'''
            )
    elif eTree.type is ListComp:
        yTree = eTree[0]
        xTree = eTree[1]
        iterTree = eTree[2]
        try:
            conditionTree = eTree[3]
        except IndexError:
            conditionTree = None
        iterThing = ThingIter(evalExpression(iterTree, environment))
        buffer = []
        tempEnv = environment + [Namespace()]
        for nextThing in iterThing:
            assignTo(nextThing, xTree, tempEnv)
            if isTrue(evalExpression(conditionTree, tempEnv)):
                buffer.append(evalExpression(yTree, tempEnv))
        return unprimitize(buffer)

def executeCmdTree(runTime : RunTime, cmdTree : CmdTree, environment : Environment):
    if cmdTree.type in (From, Import):
        if cmdTree.type is Import:
            name = cmdTree[0].value
        elif cmdTree.type is From:
            name = parsePackaging(cmdTree[0])
            lexems = cmdTree[1:]
            lexem_types = [type(x) for x in lexems]
            if Times in lexem_types:
                if len(lexems) != 1:
                    raise Helicopter(
                        builtin.ImportError, 
                        'importing other things with "*"', 
                    )
                targets = '*'
            else:
                assert all([x is Identifier for x in lexem_types])
                # A non-minipy assertion
                targets = [x.value for x in lexems]
        importJob : RunTime.ImportJob = runTime.isImportCircular(name)
        if importJob:
            forbid = environment[-1].forbid
            if cmdTree.type is Import:
                forbid(name)
            elif cmdTree.type is From:
                if targets == '*':
                    raise Helicopter(
                        builtin.ImportError, 
                        'Circular import does not support "*".', 
                    )
                else:
                    for target in targets:
                        forbid(target)
            importJob.onDone.append((
                executeCmdTree, cmdTree, environment, 
            ))
        else:
            moduleNamepsace = runTime.imPort(name, name)
            if cmdTree.type is Import:
                module = instantiate(builtin.Module)
                module.namespace = moduleNamepsace
                assignTo(module, name, environment)
            elif cmdTree.type is From:
                if targets == '*':
                    for key, value in moduleNamepsace.items():
                        if not key.startswith('__'):
                            assignTo(value, key, environment)
                else:
                    for target in targets:
                        assignTo(
                            moduleNamepsace[target], target, 
                            environment, 
                        )
    elif cmdTree.type is Del:
        assignTo(Undefined(), cmdTree[0], environment)
    elif cmdTree.type is Raise:
        raise Helicopter(evalExpression(
            cmdTree[0], environment, 
        ))
    elif cmdTree.type is Return:
        raise ReturnAsException(evalExpression(
            cmdTree[0], environment, 
        ))
    elif cmdTree.type is Break:
        raise BreakAsException
    elif cmdTree.type is Continue:
        raise ContinueAsException
    elif cmdTree.type is Pass:
        pass
    elif cmdTree.type is ExpressionCmd:
        return evalExpression(cmdTree[0], environment)
        # Returning for REPL
    elif cmdTree.type is AssignCmd:
        thing = evalExpression(cmdTree[1], environment)
        assignTo(thing, cmdTree[0], environment)

def parsePackaging(eTree : ExpressionTree):
    if eTree.type is Attributing:
        return parsePackaging(eTree[0]) + '.' + eTree[1].value
    else:
        raise Helicopter(
            builtin.ImportError, 
            'Script path must be identifiers seperated by ".", '
            + f'but encountered "{eTree.type.__name__}".', 
        )

class Undefined:
    def __iter__(self):
        return self
    
    def __next__(self):
        return self

def assignTo(
    thing : Thing, slot, 
    environment : Environment, 
):
    if type(slot) is Identifier:
        if type(thing) is Undefined:
            environment.delete(slot.value)
        else:
            environment.assign(slot.value, thing)
    elif type(slot) is ExpressionTree:
        if slot.type in (Parened, Terminal):
            assignTo(thing, slot[0], environment)
        if slot.type in (ListDisplay, TupleDisplay):
            buffer = [*ThingIter(thing)]
            if len(buffer) != len(slot):
                raise Helicopter(
                    builtin.ValueError, 
                    'Dimension mismatch during unpacking, ' 
                    + f'{len(slot)} ≠ {len(buffer)}. ', 
                )
            for subSlot, subThing in zip(slot, buffer):
                assignTo(subThing, subSlot, environment)
        if slot.type is Attributing:
            parent = evalExpression(slot[0], environment)
            assignTo(thing, slot[1], [parent.namespace])
        if slot.type in (Indexing, Slicing):
            indexee = evalExpression(slot[0], environment)
            if slot.type is Indexing:
                slice_or_index = evalExpression(slot[1], environment)
            elif slot.type is Slicing:
                slice_or_index = instantiate(
                    builtin.slice, 
                    evalExpression(slot[1], environment), 
                    evalExpression(slot[2], environment), 
                    evalExpression(slot[3], environment), 
                )
            indexee.namespace['__setitem__'].call(slice_or_index, thing)
    else:
        raise TypeError(
            'Cannot assign to non-Identifier non-ExpressionTree. '
        )   # this is a non-miniPy error

def recordStackTrace(helicopter, label, cmdTree):
    helicopter.stack.append(
        (cmdTree.filename, cmdTree.line_number, label), 
    )
    raise helicopter
