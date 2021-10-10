from runtime import Environment, Thing
from .parser import CmdTree, ExpressionTree

def evalExpression(
    expressionTree : ExpressionTree, 
    environment : Environment, 
) -> Thing:
    ...

def executeCmdTree(cmdTree : CmdTree, environment : Environment):
    pass
