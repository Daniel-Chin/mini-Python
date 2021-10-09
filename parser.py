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
    From, 
    Import, 
    Raise, 
]

class IsNot      (Lexem): pass
class NotIn      (Lexem): pass
class UnaryNegate(Lexem): pass
OPERATION_PRECEDENCE = (
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

def expect(lexem, LexemTypes):
    if type(LexemTypes) is not tuple:
        LexemTypes = (LexemTypes, )
    if type(lexem) not in LexemTypes:
        expecting = " or ".join([x.__name__ for x in LexemTypes])
        raise SyntaxError(
            'Expecting ' + expecting 
            + ', but parser encountered ' + repr(lexem)
        )

class CmdTree(list):
    def __init__(self):
        super().__init__()
        self.indent_level = None
        self.type = None    # *PREFIX_KEYWORDS | AssignCmd | ExpressionCmd
    
    def __repr__(self):
        return self.type.__name__ + super().__repr__()
    
    def pprint(self, depth = 0):
        print(' ' * depth, self.type.__name__, '[', sep='', end='')
        if self:
            print()
        for x in self:
            x.pprint(depth + 1)
        print(' ' * depth, ']', sep='')

    def parse(self, lexer):
        while True:
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
                    expect(last_lexem, Of)
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
                        expect(lexem, (Identifier, RParen))
                        if type(lexem) is RParen:
                            break
                        arg = FunctionArg(lexem)
                        self.append(arg)
                        lexem = next(lexer)
                        expect(lexem, (Comma, RParen, Assign))
                        if type(lexem) is Assign: 
                            expressionTree, last_lexem = parseExpression(lexer)
                            arg.setDefault(expressionTree)
                            expect(last_lexem, (Comma, RParen))
                            lexem = last_lexem
                        if type(lexem) is RParen:
                            break
                    expect(next(lexer), Column)
                    expect(next(lexer), EoL)
                elif type(lexem) is Class:
                    lexem = next(lexer)
                    expect(lexem, Identifier)
                    self.append(lexem)
                    lexem = next(lexer)
                    expect(lexem, (Column, LParen))
                    if type(lexem) is LParen:
                        expressionTree, last_lexem = parseExpression(lexer)
                        self.append(expressionTree)
                        expect(last_lexem, RParen)
                        expect(next(lexer), Column)
                    lexem = next(lexer)
                    expect(lexem, (EoL, Pass))
                    if type(lexem) is Pass:
                        expect(next(lexer), EoL)
                elif type(lexem) is Import:
                    lexem = next(lexer)
                    expect(lexem, Identifier)
                    self.append(lexem)
                    expect(next(lexer), EoL)
                elif type(lexem) is From:
                    expressionTree, last_lexem = parseExpression(lexer)
                    self.append(expressionTree)
                    expect(last_lexem, Import)
                    while True:
                        lexem = next(lexer)
                        expect(lexem, (Identifier, Times))
                        self.append(lexem)
                        lexem = next(lexer)
                        expect(lexem, (Comma, EoL))
                        if type(lexem) is EoL:
                            break
                elif type(lexem) in (Del, Raise):
                    expressionTree, last_lexem = parseExpression(lexer)
                    self.append(expressionTree)
                    expect(last_lexem, EoL)
                elif type(lexem) in (Pass, Break, Continue):
                    expect(next(lexer), EoL)
                elif type(lexem) is Return:
                    lexem = next(lexer)
                    if type(lexem) is not EoL:
                        expressionTree, last_lexem = parseExpression(lexer, lexem)
                        self.append(expressionTree)
                        expect(last_lexem, EoL)
            elif type(lexem) is EoL:
                continue
            else:
                expressionTree, last_lexem = parseExpression(lexer, lexem)
                self.append(expressionTree)
                if type(last_lexem) is Assign:
                    self.type = AssignCmd
                    expressionTree, last_lexem = parseExpression(lexer)
                    self.append(expressionTree)
                    expect(last_lexem, EoL)
                elif type(last_lexem) is EoL:
                    self.type = ExpressionCmd
                else:
                    expect(last_lexem, (Assign, EoL))
            break

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
class Attributing  (ExpressionType): pass
class ListComp     (ExpressionType): pass

class FunctionArg: 
    def __init__(self, identifierLexem):
        self.identifierLexem = identifierLexem
        self.has_default = False
        self.default = None
    
    def setDefault(self, default):
        self.has_default = True
        self.default = default
    
    def __repr__(self):
        s = repr(self.identifierLexem)
        if self.has_default:
            s += '=' + repr(self.default)
        return 'arg(' + s + ')'
    
    def pprint(self, depth = 0):
        print(' ' * depth, 'arg(', self.identifierLexem, sep='', end='')
        if self.has_default:
            print(' = ')
            self.default.pprint(depth + 1)
            print(' ' * depth, end='')
        print(')')

class ExpressionTree(list):
    def __init__(self, _type, x = []):
        super().__init__(x)
        self.type = _type
        self.operationLexem = None  # if type is Binary or Unary
    
    def friendlyName(self):
        if self.type in (Binary, Unary):
            return self.operationLexem.__name__
        else:
            return self.type.__name__

    def __repr__(self):
        return self.friendlyName() + list.__repr__(self)
    
    def pprint(self, depth = 0):
        print(' ' * depth, self.friendlyName(), '(', sep='', end='')
        if self:
            print()
        for x in self:
            x.pprint(depth + 1)
        print(' ' * depth, ')', sep='')

class Empty:
    '''
    For example, x[5:] is x[5:Empty]
    '''
    def __repr__(self):
        return '<Empty>'
    def pprint(self, depth = 0):
        print(' ' * depth, repr(self), sep='')

def parseDisplay(
    content, content_types, is_dict = False, 
    delimiter = Comma, allow_empty = False, 
):
    tree = ExpressionTree(None, [])
    def parseOneElement(sub_content, sub_content_types):
        if not sub_content:
            if allow_empty:
                tree.append(Empty())
                return
            else:
                raise SyntaxError(
                    '`parseDisplay` encounters empty segment while `allow_empty` is False. '
                )
        if is_dict:
            try:
                column_i = sub_content_types.index(Column)
            except ValueError:
                raise SyntaxError(
                    'Mixed set and dict: '
                    + repr(sub_content)
                )
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

def parseExpression(lexer, first_lexem = None):
    buffer = []
    unclosed = 0
    while True:
        interupted = False
        buffer_types = [type(x) for x in buffer]
        if first_lexem is None:
            try:
                lexem = next(lexer)
            except StopIteration:
                interupted = True
                lexem = None
        else:
            lexem = first_lexem
            first_lexem = None
        if type(lexem) in (Num, String, Boolean, NONE, Identifier):
            buffer.append(ExpressionTree(Terminal, [lexem]))
            if type(lexem) is Identifier:
                buffer_types.append(type(buffer[-1]))
                if len(buffer_types) >= 3 and buffer_types[-2] is Dot:
                    expect(buffer[-3], ExpressionTree)
                    buffer, left, right = buffer[:-3], buffer[-3], buffer[-1]
                    buffer.append(ExpressionTree(
                        Attributing, [left, right]
                    ))
        elif type(lexem) in (RParen, RBracket, RSquareBracket):
            try:
                content_len = buffer_types[::-1].index(
                    lexem.MATCH
                )
            except ValueError:
                interupted = True
            else:
                unclosed -= 1
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
                    if buffer and type(buffer[-1]) is ExpressionTree:
                        callee = buffer.pop(-1)
                        theTuple.type = TupleDisplay
                        buffer.append(ExpressionTree(
                            FunctionCall, [callee, theTuple], 
                        ))
                    else:
                        if len(theTuple) == 1 and not trialing_comma:
                            theTuple.type = Parened
                            theParened = theTuple
                            buffer.append(theParened)
                        else:
                            theTuple.type = TupleDisplay
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
                    if buffer and type(buffer[-1]) is ExpressionTree:
                        indexable = buffer.pop(-1)
                        if Column in content_types:
                            tree = ExpressionTree(
                                Slicing, [indexable]
                            )
                            theSlice, trialing_column = parseDisplay(
                                content, content_types, 
                                delimiter=Column, allow_empty=True, 
                            )
                            if trialing_column:
                                theSlice.append(Empty())
                            if len(theSlice) == 2:
                                theSlice.append(Num(1))
                            tree.extend(theSlice)
                            buffer.append(tree)
                        else:
                            ExpressionTree(Indexing, [
                                indexable, 
                                reduce(content, content_types), 
                            ])
                    else:
                        if For in content_types or Of in content_types:
                            if For not in content_types or Of not in content_types:
                                raise SyntaxError(
                                    'List comp must have both "for" and "of", but you gave'
                                    + repr(content)
                                )
                            theListComp = ExpressionTree(
                                ListComp, []
                            )
                            sep = content_types.index(For)
                            y, content_types = content_types[:sep], content_types[sep+1:]
                            x, content       = content      [:sep], content      [sep+1:]
                            theListComp.append(reduce(x, y))
                            sep = content_types.index(Of)
                            y, content_types = content_types[:sep], content_types[sep+1:]
                            x, content       = content      [:sep], content      [sep+1:]
                            theListComp.append(reduce(x, y))
                            if If in content_types:
                                sep = content_types.index(If)
                                y, content_types = content_types[:sep], content_types[sep+1:]
                                x, content       = content      [:sep], content      [sep+1:]
                            else:
                                x, y = content, content_types
                            theListComp.append(reduce(x, y))
                            if If in content_types:
                                theListComp.append(reduce(content, content_types))
                            buffer.append(theListComp)
                        else:
                            theList, _ = parseDisplay(
                                content, content_types, 
                            )
                            theList.type = ListDisplay
                            buffer.append(theList)
        elif type(lexem) in (
            LParen, LSquareBracket, LBracket, Comma, 
            Or, And, Not, LessThanOrEqual, LessThan, 
            GreaterThanOrEqual, GreaterThan, NotEqual, 
            Equal, In, Is, Plus, Minus, Times, Divide, 
            ModDiv, ToPowerOf, Dot, 
        ):
            buffer.append(lexem)
            if type(lexem) in (LParen, LSquareBracket, LBracket):
                unclosed += 1
        elif type(lexem) in (Column, Of, For, If):
            if unclosed > 0:
                buffer.append(lexem)
            else:
                interupted = True
        else:
            interupted = True
        if interupted:
            if unclosed:
                which = {LParen, LSquareBracket, LBracket}.intersection(
                    buffer_types
                )
                if type(lexem) is EoL:
                    expect(next(lexer), Indentation)
                else:
                    raise SyntaxError(
                        'Expression terminated by '
                        + repr(lexem) 
                        + ' but has unclosed '
                        + repr([x.__name__ for x in which])
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
        line_number = content[right_i - 1]
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
                replace().lineNumber(line_number)
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
            try:
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
            except IndexError:
                raise SyntaxError(repr(content))
    if len(content) > 1:
        raise SyntaxError(
            str(len(content)) + ' expressions concatenated: \n'
            + '\n'.join([repr(x) for x in content])
        )
    return content[0]

if __name__ == '__main__':
    from lexer import Lexer, LookAheadIO
    with open('test.minipy', 'r') as f:
        lexer = Lexer(LookAheadIO(f))
        for cmdTree in CmdsParser(lexer):
            cmdTree.pprint()
