from runtime import (
    BreakAsException, Environment, Helicopter, Namespace, 
    ContinueAsException, ReturnAsException, RunTime, Thing, 
    assignTo, instantiate, 
    isTrue, ThingIter, isSame, 
)
from lexems import Identifier
from lexer import *
from .parser import (
    AssignCmd, CmdTree, Empty, ExpressionCmd, ExpressionTree, 
    FunctionArg, IsNot, NotIn, 
    Terminal, Parened, TupleDisplay, FunctionCall, 
    DictDisplay, SetDisplay, ListDisplay, Indexing, Slicing, 
    Binary, Unary, Attributing, ListComp, UnaryNegate, 
)
from builtin import builtin

class NameSpaceKeyError(Exception): pass

def evalExpression(
    eTree : ExpressionTree, 
    environment : Environment, 
) -> Thing:
    try:
        if eTree.type is Terminal:
            lexem = eTree[0]
            if type(lexem) is Num:
                if '.' in lexem.value:
                    thing = instantiate(builtin.float, float(lexem.value))
                else:
                    thing = instantiate(builtin.int, int(lexem.value))
            elif type(lexem) is String:
                thing = instantiate(builtin.str, lexem.value)
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
            return instantiate(builtin.tuple, tuple(
                evalExpression(x, environment) for x in eTree
            ))
        elif eTree.type is ListDisplay:
            return instantiate(builtin.list, [
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
            return instantiate(builtin.set, s)
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
                        ...
                        # positional after named! 
                    args.append(evalExpression(funcArg.value, environment))
                else:
                    positional_finished = True
                    arg_name = funcArg.name.value
                    if arg_name in keyword_args:
                        ...
                        # duplicate argument
                    keyword_args[arg_name] = evalExpression(
                        funcArg.value, environment, 
                    )
            return evalExpression(calleeExpr, environment).call(
                *args, **keyword_args, 
            )
        elif eTree.type is Indexing:
            indexee = evalExpression(eTree[0], environment)
            index = evalExpression(eTree[1], environment)
            try:
                return indexee.namespace['__getitem__'].call(index)
            except KeyError:
                raise NameSpaceKeyError('indexing')
        elif eTree.type is Slicing:
            slicee = evalExpression(eTree[0], environment)
            start = evalExpression(eTree[1], environment)
            end = evalExpression(eTree[2], environment)
            step = evalExpression(eTree[3], environment)
            try:
                return slicee.namespace['__getslice__'].call(
                    instantiate(builtin.tuple, (start, end, step))
                )
            except KeyError:
                raise NameSpaceKeyError('slicing')
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
            try:
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
            except KeyError:
                raise NameSpaceKeyError(type(
                    eTree.operationLexem
                ).__name__)
        elif eTree.type is Unary:
            thing = evalExpression(eTree[0], environment)
            if type(eTree.operationLexem) is UnaryNegate:
                try:
                    return thing.namespace['__neg__'].call()
                except KeyError:
                    raise NameSpaceKeyError('UnaryNegate')
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
                raise Helicopter(instantiate(builtin.AttributeError(
                    f'''{
                        thing._class.namespace["__name__"].primitive_value
                    } object does not have "{name}"'''
                )))
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
            return instantiate(builtin.list, buffer)

    except NameSpaceKeyError as e:
        raise Helicopter(instantiate(builtin.TypeError(
            f'"{e.args[0]}" not supported.'
        )))

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
                    raise Helicopter(instantiate(
                        builtin.ImportError, 
                        'importing other things with "*"'
                    ))
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
                    raise Helicopter(instantiate(
                        builtin.ImportError, 
                        'Circular import does not support "*".'
                    ))
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
        raise Helicopter(instantiate(
            builtin.ImportError, 
            'Script path must be identifiers seperated by ".", '
            + f'but encountered "{eTree.type.__name__}".', 
        ))

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
                ...
                # unpacking: dimension mismatch, x != y
            for subSlot, subThing in zip(slot, buffer):
                assignTo(subThing, subSlot, environment)
        if slot.type is Attributing:
            parent = evalExpression(slot[0], environment)
            assignTo(thing, slot[1], [parent.namespace])
        if slot.type in (Indexing, Slicing):
            ...
    else:
        raise TypeError(
            'Cannot assign to non-Identifier non-ExpressionTree. '
        )   # this is a non-miniPy error
