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

class IsNot      (Lexem): pass
class NotIn      (Lexem): pass
class UnaryNegate(Lexem): pass
OPERATION_PRECEDENCE = (
    Dot, 
    ToPowerOf, 
    UnaryNegate, 
    Times, 
    Divide, 
    ModDiv, 
    Plus, 
    Minus, 
    IsNot, 
    NotIn, 
    Is, 
    In, 
    NotEqual, 
    Equal, 
    LessThanOrEqual, 
    LessThan, 
    GreaterThanOrEqual, 
    GreaterThan, 
    Not, 
    And, 
    Or, 
)

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
        expect(lexem, Indentation)
        self.indent_level = lexem.value
        lexem = next(lexer)
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
        self.operationLexem = None  # if type is Binary or Unary

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
                reduce(
                    sub_content      [:column_i],
                    sub_content_types[:column_i],
                ), 
                reduce(
                    sub_content      [column_i+1 :], 
                    sub_content_types[column_i+1 :], 
                ), 
            ])
        else:
            element = reduce(sub_content, sub_content_types)
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
                            reduce(content, content_types), 
                        ])
                else:
                    theList, _ = parseDisplay(
                        content, content_types, 
                    )
                    theList.type = ListDisplay
                    buffer.append(theList)
        else:
            unclosed = {LParen, LSquareBracket, LBracket}.intersection(
                {type(x) for x in buffer}
            )
            if unclosed:
                if type(lexem) is EoL:
                    expect(next(lexer), Indentation)
                else:
                    raise SyntaxError(
                        f'Expression terminated by {lexem} but has unclosed {unclosed}.'
                    )
            else:
                return reduce(buffer, [type(x) for x in buffer]), lexem

def reduce(content, content_types):
    for i in range(len(content) - 1, -1, -1):
        if content_types[i] is EoL:
            content_types.pop(i)
            content      .pop(i)
    for right_i in range(len(content) - 1, 0, -1):
        selected = content_types[right_i-1 : right_i+1]
        replace = None
        if selected == [Is, Not]:
            replace = IsNot
        elif selected == [Not, In]:
            replace = NotIn
        if replace is not None:
            content_types = content_types[
                : right_i - 1
            ] + [
                replace
            ] + content_types[right_i + 1 :]
            content       = content      [
                : right_i - 1
            ] + [
                replace().lineNumber(selected[0].line_number)
            ] + content      [right_i + 1 :]
    for right_i in range(len(content) - 1, 0, -1):
        if content_types[right_i] is Minus and (
            right_i == 0 
        or
            content_types[right_i - 1] is Lexem
        ):
            content_types[right_i] = UnaryNegate
            content      [right_i] = UnaryNegate().lineNumber(
                content[right_i].line_number
            )
    for operation in OPERATION_PRECEDENCE:
        while True:
            try:
                operation_i = content_types.index(operation)
            except ValueError:
                break
            if operation in (UnaryNegate, Not):
                right = content.pop(operation_i + 1)
                content_types  .pop(operation_i + 1)
                tree = ExpressionTree(Unary, [right])
                tree.operationLexem = operation
                content_types[operation_i] = ExpressionTree
                content      [operation_i] = tree
            else:
                # binary operation
                right = content.pop(operation_i + 1)
                content_types  .pop(operation_i + 1)
                left  = content.pop(operation_i - 1)
                content_types  .pop(operation_i - 1)
                operation_i -= 1
                tree = ExpressionTree(Binary, [left, right])
                tree.operationLexem = operation
                content_types[operation_i] = ExpressionTree
                content      [operation_i] = tree
    if len(content) > 1:
        raise SyntaxError(f'{len(content)} expressions concatenated. ')
    return content[0]
