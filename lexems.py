class Lexem:
    def __init__(self):
        self.line_number = None
    
    def lineNumber(self, x):
        self.line_number = x
        return self
    
    def __repr__(self):
        return f'''<Lexem {
            type(self).__name__
        } @ line {self.line_number}>'''

class EoL(Lexem): pass

class ArguableLexem(Lexem):
    def __init__(self, value):
        super().__init__()
        self.value = value
    
    def __repr__(self):
        return f'''<Lexem {
            type(self).__name__
        }({repr(self.value)}) @ line {self.line_number}>'''
class Identifier(ArguableLexem): pass
class Num(ArguableLexem): pass
class String(ArguableLexem): pass
class Boolean(ArguableLexem): pass
class Indentation(ArguableLexem): pass

class Equal             (Lexem) : pass
class NotEqual          (Lexem) : pass
class LessThanOrEqual   (Lexem) : pass
class GreaterThanOrEqual(Lexem) : pass
class ToPowerOf         (Lexem) : pass
class Plus              (Lexem) : pass
class Minus             (Lexem) : pass
class Times             (Lexem) : pass
class Divide            (Lexem) : pass
class ModDiv            (Lexem) : pass
class LessThen          (Lexem) : pass
class GreaterThen       (Lexem) : pass
class Assign            (Lexem) : pass
class LParen            (Lexem) : pass
class RParen            (Lexem) : pass
class LBracket          (Lexem) : pass
class RBracket          (Lexem) : pass
class LSquareBracket    (Lexem) : pass
class RSquareBracket    (Lexem) : pass
class Column            (Lexem) : pass
class Dot               (Lexem) : pass
class Comma             (Lexem) : pass

class And     (Lexem) : match = 'and'
class Break   (Lexem) : match = 'break'
class Class   (Lexem) : match = 'class'
class Continue(Lexem) : match = 'continue'
class Def     (Lexem) : match = 'def'
class Del     (Lexem) : match = 'del'
class Elif    (Lexem) : match = 'elif'
class Else    (Lexem) : match = 'else'
class Except  (Lexem) : match = 'except'
class Finally (Lexem) : match = 'finally'
class For     (Lexem) : match = 'for'
class If      (Lexem) : match = 'if'
class Import  (Lexem) : match = 'import'
class In      (Lexem) : match = 'in'
class Is      (Lexem) : match = 'is'
class NONE    (Lexem) : match = 'None'
class Not     (Lexem) : match = 'not'
class Or      (Lexem) : match = 'or'
class Pass    (Lexem) : match = 'pass'
class Raise   (Lexem) : match = 'raise'
class Return  (Lexem) : match = 'return'
class Try     (Lexem) : match = 'try'
class While   (Lexem) : match = 'while'
