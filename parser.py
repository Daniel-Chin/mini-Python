'''
A script is a miniPy syntax tree ("MST").  
A cmd (can be multiline) is parsed into a cmd tree.  
A sequence of cmd trees are parsed into an MST.  
'''

from lexems import *

PREFIX_KEYWORDS = [
    If, 
    Elif, 
    Else, 
    While, 
    Def, 
    Class, 
    Try, 
    Except, 
    Finally, 
    Pass, 
    Break, 
    Return, 
    Continue, 
    Del, 
    Import, 
    Raise, 
]

class AssignCmd: pass
class ExpressionCmd: pass

class CmdTree(list):
    KNOW_NOTHING = 'KNOW_NOTHING'
    NOT_KEYWORD = 'NOT_KEYWORD'
    ALREADY_TYPED = 'ALREADY_TYPED'

    def __init__(self) -> None:
        self.indent_level = None
        self.type = None    # *PREFIX_KEYWORDS | AssignCmd | ExpressionCmd
        self._type = self.KNOW_NOTHING   # KNOW_NOTHING | NOT_KEYWORD | ALREADY_TYPED
        self.expressionParser = None
    
    def push(self, lexem) -> bool:
        if self._type is self.KNOW_NOTHING:
            if type(lexem) in PREFIX_KEYWORDS:
                self.type = type(lexem)
                self._type = self.ALREADY_TYPED
            else:
                self._type = self.NOT_KEYWORD
                self.expressionParser = ExpressionParser()
                self.expressionParser.push(lexem)
            return False
        elif self._type is self.NOT_KEYWORD:
            result = self.expressionParser.push(lexem)
            if result is None:
                return False
            elif result:
                # last lexem is the end of 1st expression
                self.append(self.expressionParser.root)
                if lexem is Assign:
                    self.type = AssignCmd
                    self._type = self.ALREADY_TYPED
                    self.expressionParser = ExpressionParser()
                    return False
                elif lexem is EoL:
                    self.type = ExpressionCmd
                    self._type = self.ALREADY_TYPED
                    return True
                else:
                    raise SyntaxError(
                        f'An expression should have finished by now, but parser encountered {lexem}.'
                    )
            else:
                raise SyntaxError(
                    f'Failed to parse an expression at {lexem}.'
                )
        elif self.type is AssignCmd:
            result = self.expressionParser.push(lexem)
            if result is None:
                return False
            elif result:
                # last lexem is the end of 2nd expression
                self.append(self.expressionParser.root)
                if lexem is EoL:
                    return True
                else:
                    raise SyntaxError(
                        f'An expression should have finished by now, but parser encountered {lexem}.'
                    )
            else:
                raise SyntaxError(
                    f'Failed to parse an expression at {lexem}'
                )
        else:
            # Keyword prefix
            

def CmdsParser(lexer):
    cmdTree = CmdTree()
    for lexem in lexer:
        finished = cmdTree.push(lexem)
        if finished:
            yield cmdTree
            cmdTree = CmdTree()
