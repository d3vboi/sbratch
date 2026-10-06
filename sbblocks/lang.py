# SB language helpers: identifiers, literals, etc...
import re

# variable names: start with a letter, then letters / digits / underscores.
IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
NUMBER = re.compile(r"^-?(\d+(\.\d+)?|\.\d+)$")

# names a user variable may not take (keywords + built-in objects). lowercase.
RESERVED = {
    # keywords
    "if", "then", "else", "elseif", "endif", "for", "to", "step", "endfor",
    "while", "endwhile", "goto", "sub", "endsub", "and", "or", "true", "false",
    # builtin objects (a variable with the same name breaks member calls)
    "array", "clock", "controls", "desktop", "dictionary", "file", "flickr",
    "graphicswindow", "imagelist", "keyboard", "math", "mouse", "network",
    "program", "shapes", "sound", "stack", "text", "textwindow", "timer",
    "turtle", "event", "color",
}

_SPECIAL_CHARS = {'"': 34, "\n": 10, "\r": 13}


def sb_string(s: str) -> str:
    """return SB expression making string `s`.

    SB string literals can't contain a double quote or newline, those
    are spliced in with Text.GetCharacter(code)
    """
    pieces = []
    for tok in re.split(r'(["\n\r])', s):
        if tok == "":
            continue
        if tok in _SPECIAL_CHARS:
            pieces.append(f"Text.GetCharacter({_SPECIAL_CHARS[tok]})")
        else:
            pieces.append(f'"{tok}"')
    if not pieces:
        return '""'
    acc = pieces[0]
    for p in pieces[1:]:
        acc = f"Text.Append({acc}, {p})"
    return acc


def _outer_pair(e: str) -> bool:
    # true if first '(' of e is matched by last ')'.
    depth = 0
    in_str = False
    for i, ch in enumerate(e):
        if ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return i == len(e) - 1
    return False


def strip_outer(e: str) -> str:
    # remove redundant parentheses wrapping expression
    e = e.strip()
    while e.startswith("(") and e.endswith(")") and _outer_pair(e):
        e = e[1:-1].strip()
    return e


def operand(e: str) -> str:
    # prepare an expression for use as an operand of a binary operator
    e = e.strip()
    return f"({e})" if e.startswith("-") else e
