from runtime import (
    Environment, Helicopter, Thing, assignTo, instantiate, 
    isTrue, ThingIter, isSame, executeScript, 
)
from lexems import Identifier
from lexer import *
from .parser import (
    CmdTree, Empty, ExpressionTree, FunctionArg, IsNot, NotIn, 
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
            tempEnv = environment + [{}]
            for nextThing in iterThing:
                assignTo(nextThing, xTree, tempEnv)
                if isTrue(evalExpression(conditionTree, tempEnv)):
                    buffer.append(evalExpression(yTree, tempEnv))
            return instantiate(builtin.list, buffer)

    except NameSpaceKeyError as e:
        raise Helicopter(instantiate(builtin.TypeError(
            f'"{e.args[0]}" not supported.'
        )))

def executeCmdTree(cmdTree : CmdTree, environment : Environment):
    if cmdTree.type in (From, Import):
        newNamespace = executeScript

def assignTo(
    thing : Thing, slot, 
    environment : Environment, 
):
    if type(slot) is Identifier:
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
