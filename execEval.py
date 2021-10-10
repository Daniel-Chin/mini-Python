from runtime import Environment, Thing, instantiate
from lexer import *
from .parser import (
    CmdTree, ExpressionTree, FunctionArg, 
    Terminal, Parened, TupleDisplay, FunctionCall, 
    DictDisplay, SetDisplay, ListDisplay, Indexing, Slicing, 
    Binary, Unary, KeyValuePair, Attributing, ListComp, 
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
        return instantiate(builtin.set, set(
            evalExpression(x, environment) for x in eTree
        ))
    elif eTree.type is DictDisplay:
        d = {}
        for key, value in eTree:
            keyThing = evalExpression(key, environment)
            d[
                keyThing.primitive_value
            ] = evalExpression(value, environment)
            # ... this is wrong!!!
        return instantiate(builtin.set, d)
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
        return evalExpression(calleeExpr).call(*args, **keyword_args)
def executeCmdTree(cmdTree : CmdTree, environment : Environment):
    pass
