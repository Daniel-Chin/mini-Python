from runtime import Environment, Thing
from lexer import *
from .parser import (
    CmdTree, ExpressionTree, 
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
            thing = Thing()
            if '.' in lexem.value:
                thing._class = builtin.float
                thing.primitive_value = int(lexem.value)
            else:
                thing._class = builtin.int
                thing.primitive_value = float(lexem.value)

def executeCmdTree(cmdTree : CmdTree, environment : Environment):
    pass
