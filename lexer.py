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
    ('<' , LessThan          ), 
    ('>' , GreaterThan       ), 
    ('=' , Assign            ), 
    ('(' , LParen            ), 
    (')' , RParen            ), 
    ('{' , LBracket          ), 
    ('}' , RBracket          ), 
    ('[' , LSquareBracket    ), 
    (']' , RSquareBracket    ), 
    (':' , Column            ), 
    ('.' , Dot               ), 
    (',' , Comma             ), 
)

KEYWORDS = {
    'and'     : And     , 
    'break'   : Break   , 
    'class'   : Class   , 
    'continue': Continue, 
    'def'     : Def     , 
    'del'     : Del     , 
    'elif'    : Elif    , 
    'else'    : Else    , 
    'except'  : Except  , 
    'finally' : Finally , 
    'for'     : For     , 
    'if'      : If      , 
    'import'  : Import  , 
    'from'    : From    , 
    'in'      : In      , 
    'of'      : Of      , 
    'is'      : Is      , 
    'None'    : NONE    , 
    'not'     : Not     , 
    'or'      : Or      , 
    'pass'    : Pass    , 
    'raise'   : Raise   , 
    'return'  : Return  , 
    'try'     : Try     , 
    'while'   : While   , 
}

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
        self.line_no = 1
    
    def read(self, n_char, commit = True):
        buffer_requested = min(len(self.buffer), n_char)
        result = ''.join(self.buffer[:buffer_requested])
        self.buffer = self.buffer[buffer_requested:]
        need_more = n_char - buffer_requested
        if need_more:
            result += self.file.read(need_more)
        if commit:
            self.line_no += result.count('\n')
        return result
    
    def lookAhead(self, n_char):
        result = self.read(n_char, commit = False)
        self.buffer = [*result] + self.buffer
        return result
    
    def readline(self):
        while True:
            char = self.read(1)
            if char == '':
                raise EOFError
            elif char == '\n':
                return

def Lexer(f):
    lAIO = LookAheadIO(f)
    indent_using = []
    indentation = expectIndentation(lAIO, indent_using)
    yield indentation.lineNumber(1)
    while True:
        prev_line_no = lAIO.line_no
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
            yield EoL().lineNumber(prev_line_no)
            indentation = expectIndentation(lAIO, indent_using)
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
            elif word == 'False':
                yield Boolean(False).lineNumber(lAIO.line_no)
            else:
                try:
                    yield KEYWORDS[word]().lineNumber(lAIO.line_no)
                except KeyError:
                    yield Identifier(word).lineNumber(lAIO.line_no)
        elif char in NUM_BODY:
            n = expectNum(lAIO, char)
            if n == '.':
                yield Dot().lineNumber(lAIO.line_no)
            else:
                yield Num(n).lineNumber(lAIO.line_no)
        else:
            for symbol, Lexem in SYMBOLS_PRIORITY:
                need_more = len(symbol) - 1
                read = char + lAIO.lookAhead(need_more)
                if read == symbol:
                    lAIO.read(need_more)
                    yield Lexem().lineNumber(lAIO.line_no)
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
    return Indentation(acc)

def expectChar(lAIO : LookAheadIO):
    char = lAIO.read(1)
    if char == '\\':
        char_1 = lAIO.read(1)
        try:
            return {
                '\\': '\\', 'n': '\n', 't': '\t', 'r': '\r', 
                '\'': '\'', '"': '"', 
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
            elif not escaped and char == '\n':
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
        if str_num == '.':
            return '.'
        else:
            return float(str_num)
    else:
        raise SyntaxError('More than one "." in a number')

if __name__ == '__main__':
    # Self-lexing test
    with open(__file__, 'r') as f:
        lexer = Lexer(f)
        for lexem in lexer:
            print(lexem)
