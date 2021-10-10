from lexems import *
from typing import List

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
    For, 
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
    '''
    A sequence of expressionTree | lexem. 
    '''
    def __init__(self):
        super().__init__()
        self.indent_level = None
        self.type = None    # *PREFIX_KEYWORDS | AssignCmd | ExpressionCmd
        self.line_number = None
    
    def __repr__(self):
        s = self.type.__name__ + super().__repr__()
        if self:
            return s 
        else:
            return s + ' @ line ' + str(self.line_number)
    
    def pprint(self, depth = 0):
        print(' ' * depth, self.type.__name__, '[', sep='', end='')
        if self:
            print()
            for x in self:
                x.pprint(depth + 1)
            print(' ' * depth, end='')
        print(']', end='')
        if not self:
            print(' @ line', self.line_number, end='')
        print()

    def parse(self, lexer):
        while True:
            lexem = next(lexer)
            expect(lexem, Indentation)
            self.indent_level = lexem.value
            if self.line_number is None:
                self.line_number = lexem.line_number
                if self.line_number == 165:
                    # For breakpoint
                    _ = 0
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
                        arg = FunctionArg()
                        arg.name = lexem
                        self.append(arg)
                        lexem = next(lexer)
                        expect(lexem, (Comma, RParen, Assign))
                        if type(lexem) is Assign: 
                            expressionTree, last_lexem = parseExpression(lexer)
                            arg.value = expressionTree
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
        try:
            cmdTree.parse(lexer)
        except StopIteration:
            return
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
    def __init__(self):
        self.name : Identifier = None
        self.value : ExpressionTree = None
    
    def __repr__(self):
        s = '='.join((repr(self.name), repr(self.value)))
        return 'arg(' + s + ')'
    
    def pprint(self, depth = 0):
        print(' ' * depth, 'arg(', sep='', end='')
        if self.name is not None:
            print(self.name, end='')
            if self.value is not None:
                print(' = ', end='')
        if self.value is not None:
            print()
            self.value.pprint(depth + 1)
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
    parsingCallArgs = False, 
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
            if parsingCallArgs:
                element = FunctionArg()
                if Assign in sub_content_types:
                    expect(sub_content[1], Assign)
                    try:
                        if sub_content_types[0] is not ExpressionTree:
                            raise IndexError
                        expect(sub_content[0][0], Identifier)
                    except IndexError:
                        raise SyntaxError(
                            'Expecting Identifier, but encountered' 
                            + repr(sub_content[0])
                        )
                    element.name = sub_content[0][0]
                    sub_content       = sub_content      [2:]
                    sub_content_types = sub_content_types[2:]
                element.value = reduce(sub_content, sub_content_types)
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
                    if buffer and type(buffer[-1]) is ExpressionTree:
                        callee = buffer.pop(-1)
                        theArgs, _ = parseDisplay(
                            content, content_types, 
                            parsingCallArgs = True, 
                        )
                        buffer.append(ExpressionTree(
                            FunctionCall, [callee, *theArgs], 
                        ))
                    else:
                        theTuple, trialing_comma = parseDisplay(
                            content, content_types, 
                        )
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
                            buffer.append(ExpressionTree(Indexing, [
                                indexable, 
                                reduce(content, content_types), 
                            ]))
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
        elif type(lexem) in (Column, Of, For, If, Assign):
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
    if not content:
        raise SyntaxError('Reducing empty expression.')
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
            if len(content) < operation_i + 2:
                raise SyntaxError(repr(content))
            if operation in (UnaryNegate, Not):
                right = content.pop(operation_i + 1)
                content_types  .pop(operation_i + 1)
                tree = ExpressionTree(Unary, [right])
                tree.operationLexem = operation
                content_types[operation_i] = ExpressionTree
                content      [operation_i] = tree
            else:
                # binary operation
                if operation_i == 0:
                    raise SyntaxError(repr(content))
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
        e_text = (
            str(len(content)) 
            + ' expressions concatenated: \n'
            + '\n'.join([repr(x) for x in content])
        )
        if type(content[1]) is Comma:
            e_text += '\nHint: Did you mean a tuple? Don\'t omit the parenthesis.'
        raise SyntaxError(e_text)
    return content[0]

UNEXPECTED = 'Unexpected'
MISSING = 'Missing'
WRONG = 'Wrong'
def errorIndent(cmd, remark):
    raise IndentationError(
        remark + ' indentation @ line ' + str(cmd.line_number)
    )

class Sequence(list): 
    '''
    Sequence of cmdTree | substructure. 
    '''
    def parse(
        self, cmdsParser, first_cmd = None, 
        min_indent = None, 
    ):
        indent_level = None
        cmd = first_cmd
        while True:
            if cmd is None:
                try:
                    cmd : CmdTree = next(cmdsParser)
                except StopIteration:
                    cmd = CmdTree()
                    cmd.indent_level = -1
                    return cmd
            if indent_level is None:
                indent_level = cmd.indent_level
                if min_indent is not None and indent_level < min_indent:
                    errorIndent(cmd, MISSING)
            if cmd.indent_level < indent_level:
                return cmd
            if cmd.indent_level > indent_level:
                errorIndent(cmd, UNEXPECTED)
            try:
                SubstructureClass = {
                    If: Conditional, 
                    While: WhileLoop, 
                    For: ForLoop, 
                    Try: TryExcept, 
                    Def: FunctionDefinition, 
                    Class: ClassDefinition, 
                }[cmd.type]
            except KeyError:
                if cmd.type in (Else, Elif, Except, Finally):
                    raise SyntaxError(
                        'Dangling ' + cmd.type.__name__
                        + ' @ line ' + str(cmd.line_number)
                    )
                else:
                    self.append(cmd)
                    cmd = None
            else:
                substructure = SubstructureClass()
                cmd = substructure.parse(cmdsParser, cmd)
                self.append(substructure)
    
    def pprint(self, depth = 0):
        print(' ' * depth, '{', sep='')
        for x in self:
            x.pprint(depth + 1)
        print(' ' * depth, '}', sep='')

class Conditional: 
    class _Elif:
        def __init__(self):
            self.condition : CmdTree = None
            self.then : Sequence = None
    
    def __init__(self):
        self.condition : CmdTree = None
        self.then : Sequence = None
        self.elIfs : List[self._Elif] = []
        self._else : Sequence = None
    
    def parse(self, cmdsParser, first_cmd : CmdTree = None):
        self.condition = first_cmd
        indent_level = first_cmd.indent_level
        self.then = Sequence()
        cmd = self.then.parse(
            cmdsParser, 
            min_indent = indent_level + 1,
        )
        if cmd.indent_level < indent_level:
            return cmd
        if cmd.indent_level > indent_level:
            errorIndent(cmd, WRONG)
        while cmd.type is Elif:
            elIf = self._Elif()
            elIf.condition = cmd
            elIf.then = Sequence()
            cmd = elIf.then.parse(
                cmdsParser, min_indent = indent_level + 1,
            )
            self.elIfs.append(elIf)
            if cmd.indent_level < indent_level:
                return cmd
            if cmd.indent_level > indent_level:
                errorIndent(cmd, WRONG)
        if cmd.type is Else:
            self._else = Sequence()
            cmd = self._else.parse(
                cmdsParser, min_indent = indent_level + 1,
            )
            if cmd.indent_level > indent_level:
                errorIndent(cmd, WRONG)
        return cmd
    
    def pprint(self, depth = 0):
        self.condition.pprint(depth)
        self.then.pprint(depth)
        for elIf in self.elIfs:
            elIf.condition.pprint(depth)
            elIf.then.pprint(depth)
        if self._else is not None:
            print(' ' * depth, 'else', sep='')
            self._else.pprint(depth)

class WhileLoop: 
    def __init__(self):
        self.condition : CmdTree = None
        self.body : Sequence = None
        self._else : Sequence = None
    
    def parse(self, cmdsParser, first_cmd : CmdTree = None):
        self.condition = first_cmd
        indent_level = first_cmd.indent_level
        self.body = Sequence()
        cmd = self.body.parse(
            cmdsParser, min_indent = indent_level + 1, 
        )
        if cmd.indent_level < indent_level:
            return cmd
        if cmd.indent_level > indent_level:
            errorIndent(cmd, WRONG)
        if cmd.type is Else:
            self._else = Sequence()
            cmd = self._else.parse(
                cmdsParser, min_indent = indent_level + 1,
            )
            if cmd.indent_level > indent_level:
                errorIndent(cmd, WRONG)
        return cmd

    def pprint(self, depth = 0):
        self.condition.pprint(depth)
        self.body.pprint(depth)
        if self._else is not None:
            print(' ' * depth, 'else', sep='', end=' ')
            self._else.pprint(depth)

class ForLoop: 
    def __init__(self):
        self.condition : CmdTree = None
        self.body : Sequence = None
        self._else : Sequence = None
    
    def parse(self, cmdsParser, first_cmd : CmdTree = None):
        return WhileLoop.parse(self, cmdsParser, first_cmd)
    def pprint(self, depth = 0):
        return WhileLoop.pprint(self, depth)

class TryExcept: 
    class OneCatch:
        def __init__(self):
            self.catching : CmdTree = None
            self.handler : Sequence = None
    
    def __init__(self):
        self._try : Sequence = None
        self.oneCatches : List[self.OneCatch] = []
        self._else : Sequence = None
        self._finally : Sequence = None
    
    def parse(self, cmdsParser, first_cmd : CmdTree = None):
        indent_level = first_cmd.indent_level
        self._try = Sequence()
        cmd = self._try.parse(
            cmdsParser, 
            min_indent = indent_level + 1,
        )
        if cmd.indent_level < indent_level:
            return cmd
        if cmd.indent_level > indent_level:
            errorIndent(cmd, WRONG)
        while cmd.type is Except:
            oneCatch = self.OneCatch()
            oneCatch.catching = cmd
            oneCatch.handler = Sequence()
            cmd = oneCatch.handler.parse(
                cmdsParser, min_indent = indent_level + 1,
            )
            self.oneCatches.append(oneCatch)
            if cmd.indent_level < indent_level:
                return cmd
            if cmd.indent_level > indent_level:
                errorIndent(cmd, WRONG)
        if cmd.type is Else:
            self._else = Sequence()
            cmd = self._else.parse(
                cmdsParser, min_indent = indent_level + 1,
            )
            if cmd.indent_level < indent_level:
                return cmd
            if cmd.indent_level > indent_level:
                errorIndent(cmd, WRONG)
        if cmd.type is Finally:
            self._finally = Sequence()
            cmd = self._finally.parse(
                cmdsParser, min_indent = indent_level + 1,
            )
            if cmd.indent_level > indent_level:
                errorIndent(cmd, WRONG)
        return cmd
    
    def pprint(self, depth = 0):
        print(' ' * depth, 'try', sep='')
        self._try.pprint(depth)
        for oneCatch in self.oneCatches:
            oneCatch.catching.pprint(depth)
            oneCatch.handler.pprint(depth)
        if self._else is not None:
            print(' ' * depth, 'else', sep='')
            self._else.pprint(depth)
        if self._finally is not None:
            print(' ' * depth, 'finally', sep='')
            self._finally.pprint(depth)

class FunctionDefinition:
    def __init__(self):
        self._def : CmdTree = None
        self.body : Sequence = None
    
    def parse(self, cmdsParser, first_cmd : CmdTree = None):
        self._def = first_cmd
        indent_level = first_cmd.indent_level
        self.body = Sequence()
        cmd = self.body.parse(
            cmdsParser, min_indent = indent_level + 1, 
        )
        if cmd.indent_level > indent_level:
            errorIndent(cmd, WRONG)
        return cmd
    
    def pprint(self, depth = 0):
        self._def.pprint(depth)
        self.body.pprint(depth)

class ClassDefinition:
    def __init__(self):
        self._class : CmdTree = None
        self.body : Sequence = None
    
    def parse(self, cmdsParser, first_cmd : CmdTree = None):
        self._class = first_cmd
        indent_level = first_cmd.indent_level
        self.body = Sequence()
        cmd = self.body.parse(
            cmdsParser, min_indent = indent_level + 1, 
        )
        if cmd.indent_level > indent_level:
            errorIndent(cmd, WRONG)
        return cmd

    def pprint(self, depth = 0):
        self._class.pprint(depth)
        self.body.pprint(depth)

if __name__ == '__main__':
    from lexer import Lexer, LookAheadIO
    with open('test.minipy', 'r') as f:
        lexer = Lexer(LookAheadIO(f))
        root = Sequence()
        root.parse(CmdsParser(lexer))
        root.pprint()
