'''
A script is a miniPy syntax tree ("MST").  
A cmd (can be multiline) is parsed into a cmd tree.  
A sequence of cmd trees are parsed into an MST.  
'''

class CmdTree(list):
    def __init__(self) -> None:
        self.indent_level = None
    
    def push(self, lexem) -> bool:
        ...

def CmdParser(lexer):
  cmdTree = CmdTree()
  for lexem in lexer:
    finished = cmdTree.push(lexem)
    if finished:
      yield cmdTree
      cmdTree = CmdTree()
