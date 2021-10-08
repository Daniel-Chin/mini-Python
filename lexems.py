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
        }({self.value}) @ line {self.line_number}>'''

class Identifier  (ArguableLexem): pass
class Num         (ArguableLexem): pass
class String      (ArguableLexem): pass
class Boolean     (ArguableLexem): pass
class Indentation (ArguableLexem): pass

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
class LessThan          (Lexem) : pass
class GreaterThan       (Lexem) : pass
class Assign            (Lexem) : pass
class LParen            (Lexem) : pass
class RParen            (Lexem) : MATCH = LParen
class LBracket          (Lexem) : pass
class RBracket          (Lexem) : MATCH = LBracket
class LSquareBracket    (Lexem) : pass
class RSquareBracket    (Lexem) : MATCH = LSquareBracket
class Column            (Lexem) : pass
class Dot               (Lexem) : pass
class Comma             (Lexem) : pass

class And     (Lexem) : pass
class Break   (Lexem) : pass
class Class   (Lexem) : pass
class Continue(Lexem) : pass
class Def     (Lexem) : pass
class Del     (Lexem) : pass
class Elif    (Lexem) : pass
class Else    (Lexem) : pass
class Except  (Lexem) : pass
class Finally (Lexem) : pass
class For     (Lexem) : pass
class If      (Lexem) : pass
class Import  (Lexem) : pass
class In      (Lexem) : pass
class Is      (Lexem) : pass
class NONE    (Lexem) : pass
class Not     (Lexem) : pass
class Or      (Lexem) : pass
class Pass    (Lexem) : pass
class Raise   (Lexem) : pass
class Return  (Lexem) : pass
class Try     (Lexem) : pass
class While   (Lexem) : pass
