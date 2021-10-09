a = []
b = []

class C:
    def __contains__(self, _):
        return a
class D:
    def __contains__(self, _):
        return range(9)

c = C()
d = D()
for b in c in d:
    pass
