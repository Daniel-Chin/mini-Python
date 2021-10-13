from __future__ import annotations
import os
from typing import List, Dict, Set
from functools import partial
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

class NULL: pass

class Thing:
    def __init__(self) -> None:
        self._class : Thing = None
        self.namespace = Namespace()

        # if it is a function
        self.environment = None
        self.mst : FunctionDefinition = None
        self.default_args : Dict[str, Thing] = {}
        self.runTime = None

        # if it is a primitive
        self.primitive_value = NULL

        # if it is a wrapper
        self.wrappedFrom = None
    
    def copy(self):
        thing = Thing()
        thing._class          = self._class
        thing.namespace       = Namespace(self.namespace)
        thing.environment     = self.environment
        thing.mst             = self.mst
        thing.default_args    = self.default_args
        thing.primitive_value = self.primitive_value
        thing.runTime         = self.runTime
        thing.call            = self.call
        thing.wrappedFrom     = self.wrappedFrom
        return thing
    
    def call(self, *args, **keyword_args):
        if self._class is builtin.Function:
            return executeFunction(self, args, keyword_args)
        elif self._class is builtin.Class:
            return instantiate(self, args, keyword_args)
        else: 
            return self.namespace['__call__'].call(
                *args, **keyword_args, 
            )
    
    def __hash__(self):
        if self.primitive_value is not NULL:
            return hash(self.primitive_value)
        result = self.namespace['__hash__'].call()
        assertPrimitive(result)
        return result.primitive_value
    
    def __repr__(self):
        if '__name__' in self.namespace:
            name = self.namespace['__name__'].primitive_value
        elif self.wrappedFrom is not None:
            name = 'wrapped ' + self.wrappedFrom.__name__
        else:
            name = '?'
        _class = self._class
        if '__name__' in _class.namespace:
            class_name = _class.namespace['__name__'].primitive_value
        elif _class.wrappedFrom is not None:
            class_name = 'wrapped ' + _class.wrappedFrom.__name__
        else:
            class_name = '?'
        return f'<Thing {name} of {class_name}>'

def instantiate(
    theClass : Thing, args = (), keyword_args = {}, 
    skip_init = False, 
):
    thing = Thing()
    thing._class = theClass
    baseclass = theClass
    while True:
        __base__ = None
        for name, value in baseclass.namespace.items():
            if name == '__base__':
                __base__ = value
            else:
                if (
                    name not in thing.namespace
                    and name not in ('__name__', '__repr__')
                ):
                    if value._class is builtin.Function:
                        value = value.copy()
                        value.call = partial(value.call, thing)
                    thing.namespace[name] = value
        if __base__ is None:
            break
        baseclass = __base__
    if not skip_init and '__init__' in thing.namespace:
        returned = thing.namespace['__init__'].call(*args, **keyword_args)
        if not isNone(returned):
            raise Helicopter(
                builtin.TypeError, 
                '__init__ should return None, not'
                + reprString(returned), 
            )
    return thing

def unprimitize(primitive):
    if type(primitive) is bool:
        if primitive:
            return builtin.__true__
        return builtin.__false__
    elif primitive is None:
        return builtin.__none__
    elif type(primitive) is dict:
        thing = instantiate(builtin.dict)
        for key, value in primitive.items():
            thing.namespace['__setitem__'].call(key, value)
        return thing
    elif type(primitive) is set:
        thing = instantiate(builtin.set)
        for key in primitive:
            thing.namespace['add'].call(key)
        return thing
    _class = {
        int  : builtin.int  , 
        float: builtin.float, 
        str  : builtin.str  , 
        list : builtin.list , 
        tuple: builtin.tuple, 
    }[type(primitive)]
    thing = instantiate(_class)
    thing.primitive_value = primitive
    return thing

def assertPrimitive(thing):
    if thing.primitive_value is NULL:
        raise Helicopter(
            builtin.TypeError, 
            'This operation for non-primitives are not implemented.', 
        )

def isTrue(thing : Thing) -> bool:
    return builtin.bool.call(thing).primitive_value
def isNone(thing : Thing) -> bool:
    return thing.primitive_value is None

setNameJobs = []
def setName():
    for thing, s in setNameJobs:
        thing.namespace['__name__'] = unprimitize(s)

def wrapFuncion(func):
    thing = instantiate(builtin.Function)
    # this funcThing doesn't have a runTime or a __dict__, which is fine
    def wrapped(*args, **kw):
        try:
            return func(*args, **kw)
        except TypeError as e:
            if 'argument' in e.args[0].lower():
                raise Helicopter(
                    builtin.TypeError, 
                    'Builtin function ' + str(e), 
                )
            else:
                raise e
    thing.call = wrapped
    setNameJobs.append((thing, '(builtin) ' + func.__name__))
    thing.wrappedFrom = func
    return thing

def wrapClass(base = None):
    def _wrapClass(cls):
        thing = instantiate(builtin.Class)
        for key, value in cls.__dict__.items():
            if type(value) is Thing:
                thing.namespace[key] = value
        setNameJobs.append((thing, 'builtin ' + cls.__name__))
        if base is not None:
            thing.namespace['__base__'] = base
        thing.wrappedFrom = cls
        return thing
    return _wrapClass

class Namespace(dict):
    def __init__(self, *args):
        super().__init__(*args)
        self.forbidden = set()
    
    def forbid(self, name):
        self.forbidden.add(name)
    
    def wrapSelf(self):
        return unprimitize(self)

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
                if key == '__dict__':
                    return self.wrapSelf()
                if '__name__' in self:
                    name = self['__name__']
                else:
                    name = '?'
                raise Helicopter(
                    builtin.NameError, 
                    f'Name "{key}" is not defined in namespace "{name}".', 
                )
    
    def __setitem__(self, key, value) -> None:
        try:
            self.forbidden.remove(key)
        except KeyError:
            pass
        return super().__setitem__(key, value)

class Environment(list):
    def __init__(self, *args):
        super().__init__(*args)
        self.insert(0, Namespace({
            'environment': wrapFuncion(self.wrapSelf), 
        }))

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
    
    def wrapSelf(self):
        return unprimitize([unprimitize(x) for x in self])

class Helicopter(Exception): 
    def __init__(self, minipyException, remark = ''):
        super().__init__()
        self.content : Thing = instantiate(
            minipyException, 
            (unprimitize(remark), ), 
        )
        self.stack = []
        self.below = None
        self.remark = remark
    def __repr__(self):
        return 'Helicopter -> ' + repr(self.content) + self.remark
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
        if '__base__' in cursor.namespace:
            cursor = cursor.namespace['__base__']
            if cursor is not Thing:
                return False
            continue
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
        self.minipypaths = [x for x in reversed(
            os.environ.get('MINIPYPATH', '', ).split(';')
        ) if os.path.isdir(x)]
        self._modules : Dict[str, dict] = {}
        # filename -> namespace
        self.nowImportJobs : Set[self.ImportJob] = set()
    
    def resolveName(self, name):
        parts = name.split('.')
        for base in [self.dir_location, *self.minipypaths]:
            filename = os.path.join(base, *parts) + '.minipy'
            dir_name, no_dir = os.path.split(filename)
            if os.path.isdir(
                dir_name
            ) and no_dir in os.listdir(dir_name):
                return os.path.normpath(filename)
        else:
            raise Helicopter(
                builtin.ImportError, 
                f'Script "{name}" not found. Hint: ' 
                + 'Name is case-sensitive. ".minipy" ' 
                + 'extension is also case-sensitive.', 
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
            **builtin.toNamespace(), 
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
                    self, root, Environment([namespace]), f'<module {name}>', 
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
        if type(lexem) in (Num, String):
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
        return instantiate(builtin.dict, (d, ))
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
            instantiate(builtin.slice, (start, stop, step)), 
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
        return thing.namespace[name]
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
        tempEnv = Environment(environment + [Namespace()])
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
                    builtin.slice, (
                    evalExpression(slot[1], environment), 
                    evalExpression(slot[2], environment), 
                    evalExpression(slot[3], environment), 
                    ), 
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

def promotePythonException(e):
    if type(e) is Helicopter:
        raise e
    minipyException = {
        StopIteration    : builtin.StopIteration, 
        NameError        : builtin.NameError, 
        TypeError        : builtin.TypeError, 
        IndexError       : builtin.IndexError, 
        KeyError         : builtin.KeyError, 
        AttributeError   : builtin.AttributeError, 
        ImportError      : builtin.ImportError, 
        KeyboardInterrupt: builtin.KeyboardInterrupt, 
        ValueError       : builtin.ValueError, 
    }.get(type(e), builtin.PythonException)
    raise Helicopter(
        minipyException, 
        e.args[0] if e.args else '', 
    )

class KeyEncoding: 
    def __hash__(self):
        raise NotImplemented
def encodeKey(thing : Thing):
    if thing.primitive_value is NULL:
        return thing
    return thing.primitive_value
def decodeKey(key):
    if type(key) is Thing:
        return key
    return unprimitize(key)

def reprString(thing):
    return builtin.repr.call(thing).primitive_value

class Builtin: 
    def toNamespace(self):
        namespace = Namespace()
        for key, value in self.__dict__.items():
            if type(value) is Thing:
                namespace[key] = value
        return namespace
builtin = Builtin()

builtin.Class = Thing()
builtin.Class._class = builtin.Class

def buildFunc():
    Function = Thing()
    Function._class = builtin.Class
    def __func_repr__(thing):
        if '__name__' in thing.namespace:
            name = thing.namespace['__name__'].primitive_value
        else:
            name = 'anonymous'
        return unprimitize(f'<function {name}>')
    Function.namespace['__repr__'] = Thing()
    Function.namespace['__repr__']._class = Function
    Function.namespace['__repr__'].call = __func_repr__
    builtin.Function = Function
buildFunc()

def rebuildClassFunc():
    builtin.Class.namespace['__repr__'] = wrapFuncion(
        lambda thing : unprimitize(
            f'<class "{thing.namespace["__name__"].primitive_value}">'
        )
    )
    setNameJobs.append((
        builtin.Class.namespace['__repr__'], '__repr__', 
    ))
    setNameJobs.append((
        builtin.Class, 'Class', 
    ))
    
    setNameJobs.append((
        builtin.Function.namespace['__repr__'], '__repr__', 
    ))
    setNameJobs.append((
        builtin.Function, 'Function', 
    ))
rebuildClassFunc()

def buildNone():
    @wrapClass()
    class NoneType: 
        @wrapFuncion
        def __repr__(thing):
            return 'None'
    builtin.NoneType = NoneType
    builtin.__none__ = instantiate(NoneType, skip_init = True)
    builtin.__none__.primitive_value = None
buildNone()

class DummyBuiltin:
    @wrapClass()
    class bool:
        @wrapFuncion
        def __init__(thing, x = None):
            if x is None:
                thing.primitive_value = False
            else:
                thing.primitive_value = x.namespace[
                    '__bool__'
                ].call().primitive_value
            return builtin.__none__
        
        @wrapFuncion
        def __repr__(thing):
            if isTrue(thing):
                return unprimitize('True')
            return unprimitize('False')
        
        @wrapFuncion
        def __bool__(thing):
            return thing
    __true__  = instantiate(bool)
    __true__ .primitive_value = True
    __false__ = instantiate(bool)
    
    @wrapClass()
    class Exception:
        @wrapFuncion
        def __init__(thing, *args):
            thing.namespace['args'] = unprimitize(args)
            return builtin.__none__
        
        @wrapFuncion
        def __repr__(thing):
            return unprimitize(
                thing._class.namespace['__name__'].primitive_value 
                + reprString(thing.namespace['args'])
            )
    
    @wrapClass(base = Exception)
    class StopIteration: pass
    @wrapClass(base = Exception)
    class NameError: pass
    @wrapClass(base = Exception)
    class TypeError: pass
    @wrapClass(base = Exception)
    class IndexError: pass
    @wrapClass(base = Exception)
    class KeyError: pass
    @wrapClass(base = Exception)
    class AttributeError: pass
    @wrapClass(base = Exception)
    class ImportError: pass
    @wrapClass(base = Exception)
    class KeyboardInterrupt: pass
    @wrapClass(base = Exception)
    class ValueError: pass
    @wrapClass(base = Exception)
    class PythonException: pass

    @wrapClass()
    class GenericPrimitive:        
        @wrapFuncion
        def __repr__(thing):
            return unprimitize(repr(thing.primitive_value))
        
        @wrapFuncion
        def __add__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value + b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __mul__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value * b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __mod__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value % b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __truediv__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value / b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __pow__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value ** b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __neg__(thing):
            try:
                primitive_value = - thing.primitive_value
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __eq__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value == b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __lt__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value < b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __gt__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value > b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __le__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value <= b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __ge__(a, b):
            assertPrimitive(b)
            try:
                primitive_value = (
                    a.primitive_value >= b.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(primitive_value)
        
        @wrapFuncion
        def __bool__(thing):
            try:
                if thing.primitive_value:
                    return builtin.__true__
                return builtin.__false__
            except Exception as e:
                promotePythonException(e)
        
        @wrapFuncion
        def __int__(thing):
            try:
                result = int(
                    thing.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(result)
        
        @wrapFuncion
        def __float__(thing):
            try:
                result = float(
                    thing.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return unprimitize(result)
                
        @wrapFuncion
        def copy(thing):
            other = instantiate(thing._class)
            other.primitive_value = thing.primitive_value
            return other
    
    @wrapClass(base = GenericPrimitive)
    class int:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = 0
            if x is None:
                pass
            else:
                thing.primitive_value = x.namespace[
                    '__int__'
                ].call().primitive_value
            return builtin.__none__
    
    @wrapClass(base = GenericPrimitive)
    class float:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = 0.0
            if x is None:
                pass
            else:
                thing.primitive_value = x.namespace[
                    '__float__'
                ].call().primitive_value
            return builtin.__none__
    
    @wrapClass(base = GenericPrimitive)
    class str:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = ''
            if x is None:
                pass
            else:
                thing.primitive_value = reprString(x)
            return builtin.__none__
    
    @wrapClass(base = GenericPrimitive)
    class slice:
        @wrapFuncion
        def __init__(thing, *args):
            safeArgs = []
            for arg in args:
                if type(arg.primitive_value) not in (
                    int, type(None), 
                ):
                    raise TypeError(
                        '`slice` arguments must be `int` or `None`.'
                    )
                safeArgs.append(arg.primitive_value)
            start = 0
            step = 1
            if len(safeArgs) < 1:
                raise TypeError('`slice` expects at least one argument.')
            elif len(safeArgs) == 1:
                stop, = safeArgs
            elif len(safeArgs) == 2:
                start, stop = safeArgs
            elif len(safeArgs) == 3:
                start, stop, step = safeArgs
            else:
                raise TypeError('`slice` expects at most four arguments.')
            thing.primitive_value = slice(start, stop, step)
            thing.namespace['start'] = unprimitize(start)
            thing.namespace['stop' ] = unprimitize(stop )
            thing.namespace['step' ] = unprimitize(step )
            return builtin.__none__
        
        @wrapFuncion
        def __repr__(thing):
            return unprimitize(f'''slice({
                reprString(thing.namespace['start'])
            }, {
                reprString(thing.namespace['stop' ])
            }, {
                reprString(thing.namespace['step' ])
            })''')
    
    @wrapClass()
    class ListIterator:
        @wrapFuncion
        def __init__(thing, underlying):
            thing.namespace['underlying'] = underlying
            thing.namespace['acc'] = unprimitize(0)
            return builtin.__none__
        
        @wrapFuncion
        def __next__(thing):
            if (
                thing.namespace['acc'].primitive_value 
                >= builtin.len.call(thing.namespace[
                    'underlying'
                ]).primitive_value
            ):
                raise Helicopter(builtin.StopIteration)
            result = thing.namespace['underlying'].namespace[
                '__getitem__'
            ].call(thing.namespace['acc'])
            thing.namespace['acc'].primitive_value += 1
            return result
        
        @wrapFuncion
        def __iter__(thing):
            return thing
        
        @wrapFuncion
        def __repr__(thing):
            return unprimitize('<listIterator>')

    @wrapClass(base = GenericPrimitive)
    class ListAndTuple:
        @wrapFuncion
        def __getitem__(thing, index_or_slice):
            assertPrimitive(index_or_slice)
            try:
                result = thing.primitive_value[
                    index_or_slice.primitive_value
                ]
            except Exception as e:
                promotePythonException(e)
            if type(index_or_slice.primitive_value) is slice:
                return unprimitize(result)
            return result
        
        @wrapFuncion
        def __len__(thing):
            return unprimitize(len(thing.primitive_value))
        
        @wrapFuncion
        def __contains__(a, b):
            try:
                result = b in a.primitive_value
            except Exception as e:
                promotePythonException(e)
            return unprimitize(result)
        
        @wrapFuncion
        def __iter__(thing):
            return instantiate(builtin.ListIterator, (thing, ))
        
        @wrapFuncion
        def index(thing, item):
            try:
                return thing.primitive_value.index(item)
            except Exception as e:
                promotePythonException(e)
    
    @wrapClass(base = ListAndTuple)
    class list:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = []
            if x is None:
                pass
            else:
                thing.primitive_value = [*ThingIter(x)]
            return builtin.__none__
        
        @wrapFuncion
        def __setitem__(thing, index_or_slice, value):
            assertPrimitive(index_or_slice)
            if type(index_or_slice.primitive_value) is slice:
                value = value.primitive_value
            try:
                thing.primitive_value[
                    index_or_slice.primitive_value
                ] = value
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__

        @wrapFuncion
        def __repr__(thing):
            reprs = [
                reprString(x) for x in ThingIter(thing)
            ]
            return unprimitize('[' + ', '.join(reprs) + ']')

        @wrapFuncion
        def clear(thing):
            thing.primitive_value.clear()
            return builtin.__none__

        @wrapFuncion
        def append(thing, other):
            thing.primitive_value.append(other)
            return builtin.__none__

        @wrapFuncion
        def pop(thing, index):
            try:
                return thing.primitive_value.pop(index.primitive_value)
            except Exception as e:
                promotePythonException(e)
        
        @wrapFuncion
        def extend(thing, other):
            assertPrimitive(other)
            try:
                thing.primitive_value.extend(
                    other.primitive_value
                )
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__
        
        @wrapFuncion
        def remove(thing, item):
            try:
                return thing.primitive_value.remove(item)
            except Exception as e:
                promotePythonException(e)
        
        @wrapFuncion
        def sort(thing, key = None, reverse = False):
            if key is not None:
                raise Helicopter(
                    builtin.Exception, 
                    'MiniPy does not support sorting with key.', 
                )
            if not all([
                x._class in (
                    builtin.int, builtin.float, builtin.str, 
                ) for x in thing.primitive_value
            ]):
                raise Helicopter(
                    builtin.Exception, 
                    'MiniPy only supports sorting list of int, float, str.', 
                )
            if type(reverse) is Thing:
                reverse = isTrue(reverse)
            try:
                thing.primitive_value.sort(key = lambda x : (
                    x.primitive_value
                ), reverse = reverse)
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__
    
    @wrapClass(base = ListAndTuple)
    class tuple:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = ()
            if x is None:
                pass
            else:
                thing.primitive_value = tuple(
                    *ThingIter(x), 
                )
            return builtin.__none__
        
        @wrapFuncion
        def __repr__(thing):
            reprs = [
                reprString(x) for x in ThingIter(thing)
            ]
            if len(reprs) == 1:
                reprs.append('')
            return unprimitize('(' + ', '.join(reprs) + ')')
    
    @wrapClass(base = GenericPrimitive)
    class dict:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = {}
            if x is None:
                return builtin.__none__
            if x._class is builtin.dict:
                thing.primitive_value = x.primitive_value
                return builtin.__none__
            raise Helicopter(
                builtin.Exception, 
                'MiniPy does not support casting into dict.', 
            )
            # return builtin.__none__

        @wrapFuncion
        def __getitem__(thing, keyThing):
            encoding = encodeKey(keyThing)
            try:
                return thing.primitive_value[
                    encoding
                ]
            except KeyError:
                raise Helicopter(
                    builtin.KeyError, 
                    'No key ' + reprString(keyThing)
                )
            except Exception as e:
                promotePythonException(e)
        
        @wrapFuncion
        def __setitem__(thing, keyThing, value):
            encoding = encodeKey(keyThing)
            try:
                thing.primitive_value[
                    encoding
                ] = value
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__
        
        @wrapFuncion
        def __iter__(thing):
            l = unprimitize([
                decodeKey(x) 
                for x in thing.primitive_value.keys()
            ])
            return builtin.iter.call(l)

        @wrapFuncion
        def __contains__(a, b):
            try:
                result = encodeKey(b) in a.primitive_value
            except Exception as e:
                promotePythonException(e)
            return unprimitize(result)
        
        @wrapFuncion
        def __repr__(thing):
            reprs = []
            for key, value in thing.primitive_value.items():
                reprs.append(f'''{reprString(decodeKey(key))}: {
                    reprString(value)
                }''')
            return unprimitize('{' + ', '.join(reprs) + '}')

        @wrapFuncion
        def clear(thing):
            thing.primitive_value.clear()
            return builtin.__none__
        
        get = __getitem__
        
        @wrapFuncion
        def items(thing):
            l = instantiate(builtin.list)
            for key, value in thing.primitive_value.items():
                l.namespace['append'].call(unprimitize(
                    (decodeKey(key), value), 
                ))
            return builtin.iter.call(l)

        @wrapFuncion
        def pop(thing, keyThing):
            encoding = encodeKey(keyThing)
            try:
                return thing.primitive_value.pop(encoding)
            except Exception as e:
                promotePythonException(e)

        @wrapFuncion
        def update(thing, other):
            if type(other.primitive_value) is not dict:
                raise Helicopter(
                    builtin.TypeError, 
                    'Updating a dict expects another dict.', 
                )
            thing.primitive_value.update(other.primitive_value)
            return builtin.__none__
    
    @wrapClass(base = GenericPrimitive)
    class set:
        @wrapFuncion
        def __init__(thing, x = None):
            thing.primitive_value = set()
            if x is None:
                return builtin.__none__
            if x._class is builtin.set:
                thing.primitive_value = x.primitive_value
                return builtin.__none__
            l = [
                encodeKey(element) 
                for element in ThingIter(x)
            ]
            try:
                thing.primitive_value = set(l)
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__
        
        @wrapFuncion
        def __iter__(thing):
            l = unprimitize([
                decodeKey(x) 
                for x in thing.primitive_value
            ])
            return builtin.iter.call(l)
        
        @wrapFuncion
        def __contains__(a, b):
            encoding = encodeKey(b)
            try:
                result = encoding in a.primitive_value
            except Exception as e:
                promotePythonException(e)
            return unprimitize(result)
        
        @wrapFuncion
        def __repr__(thing):
            reprs = []
            for key in thing.primitive_value:
                reprs.append(reprString(decodeKey(key)))
            if reprs:
                return unprimitize('{' + ', '.join(reprs) + '}')
            else:
                return unprimitize('set()')

        @wrapFuncion
        def add(thing, other):
            encoding = encodeKey(other)
            try:
                thing.primitive_value.add(encoding)
            except Exception as e:
                promotePythonException(e)
            return builtin.__none__
        
        @wrapFuncion
        def clear(thing):
            thing.primitive_value.clear()
            return builtin.__none__
        
        @wrapFuncion
        def discard(thing, other):
            encoding = encodeKey(other)
            thing.primitive_value.discard(encoding)
            return builtin.__none__
        
        @wrapFuncion
        def intersection(thing, other):
            if type(other.primitive_value) is not set:
                raise Helicopter(
                    builtin.TypeError, 
                    'Can onlt intersect with another set, '
                    + f'not {reprString(other)}', 
                )
            newSet = instantiate(builtin.set)
            newSet = thing.primitive_value.intersection(
                other.primitive_value, 
            )
            return newSet
        
        @wrapFuncion
        def union(thing, other):
            if type(other.primitive_value) is not set:
                raise Helicopter(
                    builtin.TypeError, 
                    'Can onlt union with another set, '
                    + f'not {reprString(other)}', 
                )
            newSet = instantiate(builtin.set)
            newSet = thing.primitive_value.union(
                other.primitive_value, 
            )
            return newSet
        
        @wrapFuncion
        def pop(thing):
            try:
                result = thing.primitive_value.pop()
            except Exception as e:
                promotePythonException(e)
            return decodeKey(result)
    
    @wrapClass()
    class range:
        @wrapFuncion
        def __init__(thing, *args):
            safeArgs = []
            for arg in args:
                if type(arg.primitive_value) is not int:
                    raise TypeError(
                        '`range` arguments must be `int`.'
                    )
                safeArgs.append(arg.primitive_value)
            start = 0
            step = 1
            if len(safeArgs) < 1:
                raise TypeError('`range` expects at least one argument.')
            elif len(safeArgs) == 1:
                stop, = safeArgs
            elif len(safeArgs) == 2:
                start, stop = safeArgs
            elif len(safeArgs) == 3:
                start, stop, step = safeArgs
            else:
                raise TypeError('`range` expects at most four arguments.')
            thing.namespace['start'] = unprimitize(start)
            thing.namespace['stop' ] = unprimitize(stop )
            thing.namespace['step' ] = unprimitize(step )
            thing.namespace['acc'  ] = builtin.__none__
            return builtin.__none__
        
        @wrapFuncion
        def __repr__(thing):
            s = f'''range({
                reprString(thing.namespace['start'])
            }, {
                reprString(thing.namespace['stop' ])
            }, {
                reprString(thing.namespace['step' ])
            })'''
            acc = thing.namespace['acc']
            if not isNone(acc):
                s = f'<iter {s} next={reprString(acc)}>'
            return unprimitize(s)
        
        @wrapFuncion
        def __iter__(thing : Thing):
            other = thing.copy()
            other.namespace['acc'] = thing.namespace['start']
            return other
        
        @wrapFuncion
        def __next__(thing):
            acc = thing.namespace['acc'].primitve_value
            if acc is None:
                raise Helicopter(
                    builtin.TypeError, 
                    '`range` object is not iterable. ' 
                    + 'Hint: `iter()` it first?', 
                )
            step = thing.namespace['step'].primitve_value
            stop = thing.namespace['stop'].primitve_value
            if not (
                type(acc ) is int and 
                type(step) is int and 
                type(stop) is int
            ):
                raise Helicopter(
                    builtin.TypeError, 
                    "`range`'s `acc`, `stop`, and `step` must be int.", 
                )
            if step == 0:
                raise Helicopter(
                    builtin.ValueError, 
                    "`range`'s `step` must be non-zero.", 
                )
            if (acc - stop) * step >= 0:
                raise Helicopter(
                    builtin.StopIteration, 
                )
            thing.namespace['acc'] = unprimitize(acc + step)
            return unprimitize(acc)

    @wrapFuncion
    def repr(x : Thing):
        base_class = x._class
        while True:
            if '__repr__' in base_class.namespace:
                result = base_class.namespace['__repr__'].call(x)
                break
            if '__base__' in base_class.namespace:
                base_class = base_class.namespace['__base__']
            else:
                raise Exception('__repr__ not implemented in a thing.')
        if result._class is builtin.str:
            return result
        raise Helicopter(
            builtin.TypeError, 
            '__repr__ did not return a str.', 
        )

    @wrapFuncion
    def type(x : Thing):
        return x._class
    
    @wrapFuncion
    def iter(x : Thing):
        return x.namespace['__iter__'].call()
    
    @wrapFuncion
    def next(x : Thing):
        return x.namespace['__next__'].call()
    
    @wrapFuncion
    def len(x : Thing):
        return x.namespace['__len__'].call()
    
    @wrapFuncion
    def print(*args, sep=None, end=None, flush=None):
        if sep is None:
            sep = ' '
        else:
            sep = sep.primitive_value
            if type(sep) is not str:
                raise TypeError('`print` argument `sep` must be str.')
        if end is None:
            end = '\n'
        else:
            end = end.primitive_value
            if type(end) is not str:
                raise TypeError('`print` argument `end` must be str.')
        if flush is None:
            flush = False
        else:
            flush = flush.primitive_value
            if type(flush) is not bool:
                raise TypeError('`print` argument `flush` must be bool.')
        instantiate(builtin.str, (args[0], ))
        parts = [
            instantiate(builtin.str, (x, )).primitive_value 
            for x in args
        ]
        print(*parts, sep=sep, end=end, flush=flush)
        return builtin.__none__
    
    @wrapFuncion
    def input(prompt = None):
        if prompt is not None:
            print(reprString(prompt), end='', flush=True)
        return unprimitize(input())

for key, value in DummyBuiltin.__dict__.items():
    if type(value) is Thing:
        builtin.__setattr__(key, value)

setName()

if __name__ == '__main__':
    from console import console
    console({**globals(), **locals()})
