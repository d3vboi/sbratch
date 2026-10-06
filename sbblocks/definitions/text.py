from ..registry import category, inp
from ._helpers import call

category("text", "Text", "#7A5CD6", 60)


def s(default="hello"):
    return inp("any", default)


call("text_join", "text", "join {a} and {b}", "Text.Append", ["a", "b"],
     specs={"a": s("Hello, "), "b": s("world")},
     tooltip="Text.Append(a, b) - joins text without doing maths on numbers")
call("text_length", "text", "length of {text}", "Text.GetLength", ["text"], specs={"text": s()})
call("text_substring", "text", "Text.GetSubText {text} from {start} length {length}", "Text.GetSubText",
     ["text", "start", "length"], specs={"text": s(), "start": inp("number", "1"), "length": inp("number", "3")})
call("text_substring_end", "text", "Text.GetSubTextToEnd {text} from {start}", "Text.GetSubTextToEnd",
     ["text", "start"], specs={"text": s(), "start": inp("number", "2")})
call("text_contains", "text", "{text} contains {sub}", "Text.IsSubText", ["text", "sub"], shape="bool",
     specs={"text": s(), "sub": s("ell")})
call("text_starts", "text", "{text} starts with {sub}", "Text.StartsWith", ["text", "sub"], shape="bool",
     specs={"text": s(), "sub": s("he")})
call("text_ends", "text", "{text} ends with {sub}", "Text.EndsWith", ["text", "sub"], shape="bool",
     specs={"text": s(), "sub": s("lo")})
call("text_index_of", "text", "position of {sub} in {text}", "Text.GetIndexOf", ["text", "sub"],
     specs={"text": s(), "sub": s("l")}, tooltip="1-based position, 0 if not found")
call("text_lower", "text", "lower case {text}", "Text.ConvertToLowerCase", ["text"], specs={"text": s("HELLO")})
call("text_upper", "text", "upper case {text}", "Text.ConvertToUpperCase", ["text"], specs={"text": s()})
call("text_char", "text", "character with code {code}", "Text.GetCharacter", ["code"],
     specs={"code": inp("number", "65")})
call("text_char_code", "text", "code of character {char}", "Text.GetCharacterCode", ["char"],
     specs={"char": s("A")})
