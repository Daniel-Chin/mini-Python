from io import TextIOWrapper
from string import ascii_letters, digits
from lexems import *

IDENTIFIER_START = set([*ascii_letters, '_'])
IDENTIFIER_BODY = set.union(IDENTIFIER_START, digits)
NUM_BODY = set([*digits, '.'])

SYMBOLS_PRIORITY = (
    ('==', Equal             ), 
    ('!=', NotEqual          ), 
    ('<=', LessThanOrEqual   ), 
    ('>=', GreaterThanOrEqual), 
    ('**', ToPowerOf         ), 
    ('+' , Plus              ), 
    ('-' , Minus             ), 
    ('*' , Times             ), 
    ('/' , Divide            ), 
    ('%' , ModDiv            ), 
    ('<' , LessThen          ), 
    ('>' , GreaterThen       ), 
    ('=' , Assign            ), 
    ('(' , LParen            ), 
    (')' , RParen            ), 
    ('[' , LSquareBracket    ), 
    (']' , RSquareBracket    ), 
    (':' , Column            ), 
    ('.' , Dot               ), 
    (',' , Comma             ), 
)

KEYWORDS = [
    And     , 
    Break   , 
    Class   , 
    Continue, 
    Def     , 
    Del     , 
    Elif    , 
    Else    , 
    Except  , 
    Finally , 
    For     , 
    If      , 
    Import  , 
    In      , 
    Is      , 
    NONE    , 
    Not     , 
    Or      , 
    Pass    , 
    Raise   , 
    Return  , 
    Try     , 
    While   , 
]

class CarriageReturnDetected(Exception): 
    '''
    This language does not allow the exiestence of  
    carriage return (CR, i.e. chr(13)).  
    '''
class LexingNoMatch(Exception): pass
class MixedTabsAndSpacesError(Exception): pass
class ParseStringFailed(Exception): pass

class LookAheadIO:
    def __init__(self, file):
        self.file : TextIOWrapper = file
        self.buffer = []
        self.line_no = 0
    
    def read(self, n_char):
        buffer_requested = min(len(self.buffer), n_char)
        result = ''.join(self.buffer[:buffer_requested])
        self.buffer = self.buffer[buffer_requested:]
        need_more = n_char - buffer_requested
        if need_more:
            result += self.file.read(need_more)
        self.line_no += result.count('\n')
        return result
    
    def lookAhead(self, n_char):
        result = self.read(n_char)
        self.buffer = [*result] + self.buffer
        return result
    
    def readline(self):
        while True:
            char = self.read(1)
            if char == '':
                raise EOFError
            elif char == '\n':
                return

def Lexer(lAIO : LookAheadIO):
    indent_using = []
    indentation = expectIndentation(lAIO, indent_using)
    if indentation is not None:
        yield indentation.lineNumber(lAIO.line_no)
    while True:
        char = lAIO.read(1)
        if char == '':
            return
        elif char in (' ', '\t'):
            pass
        elif char == '#':
            try:
                lAIO.readline()
            except EOFError:
                # it is ok to end a file on an unfinished comment
                pass    
        elif char == '\n':
            yield EoL().lineNumber(lAIO.line_no)
            indentation = expectIndentation(lAIO, indent_using)
            if indentation is not None:
                yield indentation.lineNumber(lAIO.line_no)
        elif char == '\r':
            raise CarriageReturnDetected
        elif char in ("'", '"'):
            s = expectString(lAIO, char)
            yield String(s).lineNumber(lAIO.line_no)
        elif char in IDENTIFIER_START:
            word = expectWord(lAIO, char)
            if word == 'True':
                yield Boolean(True).lineNumber(lAIO.line_no)
            if word == 'False':
                yield Boolean(False).lineNumber(lAIO.line_no)
            for Keyword in KEYWORDS:
                if Keyword.match == word:
                    yield Keyword().lineNumber(lAIO.line_no)
                    break
            else:
                yield Identifier(word).lineNumber(lAIO.line_no)
        elif char in NUM_BODY:
            n = expectNum(lAIO, char)
            yield Num(n).lineNumber(lAIO.line_no)
        else:
            for symbol, lexem in SYMBOLS_PRIORITY:
                need_more = len(symbol) - 1
                read = char + lAIO.lookAhead(need_more)
                if read == symbol:
                    lAIO.read(need_more)
                    yield lexem().lineNumber(lAIO.line_no)
                    break
            else:
                raise LexingNoMatch(repr(
                    char + ''.join(lAIO.buffer)
                ))

def expectIndentation(lAIO : LookAheadIO, indent_using : list):
    acc = 0
    while lAIO.lookAhead(1) in (' ', '\t'):
        char = lAIO.read(1)
        acc += 1
        if indent_using:
            if indent_using[0] != char:
                raise MixedTabsAndSpacesError
        else:
            indent_using.append(char)
    if acc:
        return Indentation(acc)

def expectChar(lAIO : LookAheadIO):
    char = lAIO.read(1)
    if char == '\\':
        char_1 = lAIO.read(1)
        try:
            return {
                '\\': '\\', 'n': '\n', 't': '\t', 'r': '\r', 
            }[char_1], True
        except KeyError:
            if char_1 == '':
                raise EOFError(
                    'String backslash escaping interrupted by EOF.'
                )
            raise ParseStringFailed(
                f'Backslash followed by "{char_1}"'
            )
    else:
        return char, False

def expectString(lAIO : LookAheadIO, first_char):
    buffer = []
    if lAIO.lookAhead(2) == first_char * 2:
        # ''' / """
        lAIO.read(2)
        while True:
            char, escaped = expectChar(lAIO)
            if char == '':
                raise EOFError(
                    f'EOF reached when parsing a string starting with {first_char * 3}'
                )
            elif not escaped and char == first_char:
                if lAIO.lookAhead(2) == first_char * 2:
                    lAIO.read(2)
                    break
                else:
                    buffer.append(first_char)
            else:
                buffer.append(char)
    else:
        while True:
            char, escaped = expectChar(lAIO)
            if char == '':
                raise EOFError(
                    f'EOF reached when parsing a string starting with {first_char}'
                )
            elif not escaped and char == first_char:
                break
            elif char == '\n':
                raise ParseStringFailed(
                    'Line ended when parsing a single-line string'
                )
            else:
                buffer.append(char)
    return ''.join(buffer)

def expectWord(lAIO : LookAheadIO, first_char):
    buffer = [first_char]
    while True:
        char = lAIO.lookAhead(1)
        if char in IDENTIFIER_BODY:
            lAIO.read(1)
            buffer.append(char)
        else:
            break
    return ''.join(buffer)

def expectNum(lAIO : LookAheadIO, first_char):
    buffer = [first_char]
    while True:
        char = lAIO.lookAhead(1)
        if char in NUM_BODY:
            lAIO.read(1)
            buffer.append(char)
        else:
            break
    str_num = ''.join(buffer)
    n_dots = str_num.count('.')
    if n_dots == 0:
        return int(str_num)
    elif n_dots == 1:
        return float(str_num)
    else:
        raise SyntaxError('More than one "." in a number')
