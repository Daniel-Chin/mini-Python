from runtime import Environment, Thing, instantiate, isTrue
from lexer import *
from .parser import (
    CmdTree, Empty, ExpressionTree, FunctionArg, 
    Terminal, Parened, TupleDisplay, FunctionCall, 
    DictDisplay, SetDisplay, ListDisplay, Indexing, Slicing, 
    Binary, Unary, Attributing, ListComp, 
)
from builtin import builtin

def evalExpression(
    eTree : ExpressionTree, 
    environment : Environment, 
) -> Thing:
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
        return indexee.namespace['__getitem__'].call(index)
    elif eTree.type is Slicing:
        slicee = evalExpression(eTree[0], environment)
        start = evalExpression(eTree[1], environment)
        end = evalExpression(eTree[2], environment)
        step = evalExpression(eTree[3], environment)
        return slicee.namespace['__getslice__'].call(
            instantiate(builtin.tuple, (start, end, step))
        )
    elif eTree.type is Empty:
        return builtin.__none__
    elif eTree.type is Binary:
        left = evalExpression(eTree[0], environment)
        if type(eTree.operationLexem) is Or:
            if isTrue(left):
                return builtin.__true__
            if isTrue(evalExpression(eTree[1], environment)):
                return builtin.__true__
            return builtin.__false__
        elif type(eTree.operationLexem) is And:
            if isTrue(left):
                if isTrue(evalExpression(eTree[1], environment)):
                    return builtin.__true__
                return builtin.__false__
            return builtin.__false__
        else:
            right = evalExpression(eTree[1], environment)
        if type(eTree.operationLexem) is ToPowerOf:
            

def executeCmdTree(cmdTree : CmdTree, environment : Environment):
    pass

def isSame(a : Thing, b : Thing):
    if a is b:
        return True
    if a.primitive_value is not None and b.primitive_value is not None:
        return a.primitive_value is b.primitive_value
