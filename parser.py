'''
A script is a miniPy syntax tree ("MST").  
A cmd (can be multiline) is parsed into a cmd tree.  
A sequence of cmd trees are parsed into an MST.  
An expression (can be multiline) is parsed into an expression tree.  
'''

from typing import Tuple, List
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

class ExpressionType: pass
class Terminal     (ExpressionType): 
    '''
    Child is leaf lexem
    '''
class Parened      (ExpressionType): pass
class TupleDisplay (ExpressionType): pass
class FunctionCall (ExpressionType): pass
class DictDisplay  (ExpressionType): pass
class SetDisplay   (ExpressionType): pass
class ListDisplay  (ExpressionType): pass
class Indexing     (ExpressionType): pass
class Slicing      (ExpressionType): pass
class Binary       (ExpressionType): pass
class Unary        (ExpressionType): pass
class KeyValuePair (ExpressionType): pass

class ExpressionTree(list):
    def __init__(self, _type, x = []):
        super().__init__(x)
        self.type = _type

def parseDisplay(
    content, content_types, is_dict = False, 
    delimiter = Comma, 
) -> Tuple(
    ExpressionTree, bool
):
    tree = ExpressionTree(None, [])
    def parseOneElement(sub_content, sub_content_types):
        if is_dict:
            try:
                column_i = sub_content_types.index(Column)
            except ValueError:
                raise SyntaxError('Mixed set and dict.')
            element = ExpressionTree(KeyValuePair, [
                reduce(sub_content[:column_i]), 
                reduce(sub_content[column_i+1 :]), 
            ])
        else:
            element = reduce(sub_content)
        tree.append(element)
    while True:
        try:
            delimiter_i = content_types.index(delimiter)
        except ValueError:
            break
        parseOneElement(content[:delimiter_i], content_types[:delimiter_i])
        content       = content      [delimiter_i+1 :]
        content_types = content_types[delimiter_i+1 :]
    trialing_delimiter = True
    if content:
        trialing_delimiter = False
        parseOneElement(content, content_types)
    return tree, trialing_delimiter

def parseExpression(lexer) -> Tuple(ExpressionTree, Lexem):
    buffer = []
    while True:
        lexem = next(lexer)
        if type(lexem) in (Num, String, Boolean, None, Identifier):
            buffer.append(ExpressionTree(Terminal, [lexem]))
        elif type(lexem) in (RParen, RBracket, RSquareBracket):
            try:
                content_len = buffer[::-1].index(lexem.MATCH)
            except ValueError:
                raise SyntaxError(f'Unmatched {lexem}')
            if content_len == 0:
                content = []
            else:
                content = buffer[-content_len:]
            buffer = buffer[:-content_len - 1]
            content_types = [type(x) for x in content]
            if type(lexem) is RParen:
                theTuple, trialing_comma = parseDisplay(
                    content, content_types, 
                )
                if len(theTuple) == 1 and not trialing_comma:
                    theTuple.type = Parened
                    theParened = theTuple
                    buffer.append(theParened)
                else:
                    theTuple.type = TupleDisplay
                    if type(buffer[-1]) is ExpressionTree:
                        callee = buffer.pop(-1)
                        buffer.append(ExpressionTree(
                            FunctionCall, [callee, theTuple], 
                        ))
                    else:
                        buffer.append(theTuple)
            elif type(lexem) is RBracket:
                if Column in content_types:
                    theDict, _ = parseDisplay(
                        content, content_types, is_dict=True, 
                    )
                    theDict.type = DictDisplay
                    buffer.append(theDict)
                else:
                    theSet, _ = parseDisplay(
                        content, content_types, 
                    )
                    theSet.type = SetDisplay
                    if len(theSet) == 0:
                        theSet.type = DictDisplay
                        theDict = theSet
                    buffer.append(theDict)
            elif type(lexem) is RSquareBracket:
                if type(buffer[-1]) is ExpressionTree:
                    indexable = buffer.pop(-1)
                    if Column in content_types:
                        tree = ExpressionTree(
                            Slicing, [indexable]
                        )
                        theSlice, trialing_column = parseDisplay(
                            content, content_types, 
                            delimiter=Column
                        )
                        if trialing_column:
                            raise SyntaxError(
                                f'Trialing column not accepted in slicing starting with {lexem}. '
                            )
                        if len(theSlice) == 2:
                            theSlice.append(1)
                        tree.extend(theSlice)
                        buffer.append(tree)
                    else:
                        ExpressionTree(Indexing, [
                            indexable, 
                            reduce(content), 
                        ])
                else:
                    theList, _ = parseDisplay(
                        content, content_types, 
                    )
                    theList.type = ListDisplay
                    buffer.append(theList)
