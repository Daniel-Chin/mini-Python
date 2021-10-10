from runtime import Thing, UserType, ThingTemplate

def _type(x : Thing):
    if x.type is UserType:
        return x.type.userClass
    else:
        # builtin type
        y = Thing()
        y.type = ThingTemplate
        y.builtin_repr = lambda: f'<builtin class "{x.type.__name__}">'
        return y
