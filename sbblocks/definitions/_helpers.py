# shortcuts for common "Object.Member(args)" blocks
from ..registry import define, inp

def call(type, category, pattern, member, args=(), kind="value", shape="round", specs=None, tooltip=None):
    # block that generates `member(arg1, arg2, ...)`; args are pattern token names
    specs = dict(specs or {})
    for a in args:
        specs.setdefault(a, inp())
    code = "%s(%s)" % (member, ", ".join("{%s}" % a for a in args))
    define(type, category, kind, pattern, code, specs=specs, shape=shape,
           tooltip=tooltip or "%s(%s)" % (member, ", ".join(args)))

def prop(type, category, pattern, member, shape="round", tooltip=None):
    # value block that generates property read like `Clock.Year`
    define(type, category, "value", pattern, member, shape=shape, tooltip=tooltip or member)
