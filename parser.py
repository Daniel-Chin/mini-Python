'''
A script is a miniPy syntax tree ("MST").  
A cmd (can be multiline) is parsed into a cmd tree.  
A sequence of cmd trees are parsed into an MST.  
An expression (can be multiline) is parsed into an expression tree.  
'''

from typing import Tuple
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

def expect(lexem, *LexemTypes) -> None:
    if type(lexem) not in LexemTypes:
        raise SyntaxError(
            f'''Expecting {
                " or ".join([x.__name__ for x in LexemTypes])
            }, but parser encountered {lexem}.'''
        )

class CmdTree(list):
    def __init__(self) -> None:
        super().__init__()
        self.indent_level = None
        self.type = None    # *PREFIX_KEYWORDS | AssignCmd | ExpressionCmd

    def parse(self, lexer) -> None:
        lexem = next(lexer)
        if type(lexem) is Indentation:
            self.indent_level = lexem.value
            lexem = next(lexer)
        else:
            self.indent_level = 0
        if type(lexem) in PREFIX_KEYWORDS:
            self.type = type(lexem)
            if type(lexem) in (If, Elif, While, Except):
                expressionTree, last_lexem = parseExpression(lexer)
                self.append(expressionTree)
                expect(last_lexem, Column)
                expect(next(lexer), EoL)
            elif type(lexem) is For:
                expressionTree, last_lexem = parseExpression(lexer)
                self.append(expressionTree)
                expect(last_lexem, In)
                expressionTree, last_lexem = parseExpression(lexer)
                self.append(expressionTree)
                expect(last_lexem, Column)
                expect(next(lexer), EoL)
            elif type(lexem) in (Else, Try, Finally):
                expect(next(lexer), Column)
                expect(next(lexer), EoL)
            elif type(lexem) is Def:
                lexem = next(lexer)
                expect(lexem, Identifier)
                self.append(lexem)
                expect(next(lexer), LParen)
                while True:
                    lexem = next(lexer)
                    if type(lexem) is RParen:
                        break
                    expect(lexem, Identifier, RParen)
                    self.append(lexem)
                expect(next(lexer), Column)
                expect(next(lexer), EoL)
            elif type(lexem) is Class:
                lexem = next(lexer)
                expect(lexem, Identifier)
                self.append(lexem)
                lexem = next(lexer)
                if type(lexem) is LParen:
                    expressionTree, last_lexem = parseExpression(lexer)
                    self.append(expressionTree)
                    expect(last_lexem, RParen)
                    expect(lexem, Column)
                else:
                    expect(lexem, Column, LParen)
                expect(next(lexer), EoL)
            elif type(lexem) is Import:
                lexem = next(lexer)
                expect(lexem, Identifier)
                self.append(lexem)
                expect(next(lexer), EoL)
            elif type(lexem) in (Del, Raise):
                expressionTree, last_lexem = parseExpression(lexer)
                self.append(expressionTree)
                expect(last_lexem, EoL)
            elif type(lexem) in (Pass, Break, Return, Continue):
                expect(next(lexer), EoL)
        else:
            expressionTree, last_lexem = parseExpression(lexer)
            self.append(expressionTree)
            if type(last_lexem) is Assign:
                self.type = AssignCmd
                expressionTree, last_lexem = parseExpression(lexer)
                self.append(expressionTree)
                expect(last_lexem, EoL)
            elif type(last_lexem) is EoL:
                self.type = ExpressionCmd
            else:
                expect(last_lexem, Assign, EoL)

def CmdsParser(lexer):
    while True:
        cmdTree = CmdTree()
        cmdTree.parse(lexer)
        yield cmdTree

class ExpressionTree(list):
    def __init__(self):
        super().__init__()
        self.type = None

def parseExpression(lexer) -> Tuple(ExpressionTree, Lexem):
    buffer = []
    while True:
        lexem = next(lexer)
        if type(lexem) in (Num, String, Boolean, None, Identifier):
            buffer.append(ExpressionTree([lexem]))
        elif type(lexem) in (RParen, RBracket, RSquareBracket):
            try:
                content_len = buffer[::-1].index(lexem.MATCH)
            except ValueError:
                raise SyntaxError(f'Unmatched {lexem}')
