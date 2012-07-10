import sys

old_path = sys.path[:]
safe_path = list(filter(lambda x: x.startswith(sys.prefix), sys.path))

def _safe_import(modname):
    sys.path = safe_path
    try:
        module = __import__(modname)
    except ImportError:
        module = None
    sys.path = old_path
    return module

def doc_from_str(objstr):
    ns = objstr.split('.')
    try:
        obj = __builtins__[ns[0]]
    except KeyError:
        obj = _safe_import(ns[0])
    if obj is None:
        return None
    for scope in ns[1:]:
        try:
            obj = getattr(obj, scope)
        except AttributeError:
            return None
    return getattr(obj, '__doc__')
    

