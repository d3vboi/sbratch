# lists = SB arrays, list block takes a variable from the dropdown
from ._helpers import call
from ..registry import category, define, inp, many, variable

category("lists", "Lists", "#D65CD6", 40)


def _make_list(c):
    name = c.field("list")
    lines = [f'{name} = ""']
    for i, v in enumerate(c.items("items"), start=1):
        lines.append(f"{name}[{i}] = {v}")
    return lines


define("list_make", "lists", "statement", "set {list} to a list of {items}",
       specs={"list": variable(writes=True), "items": many(3, 1, 20, "any", "")},
       code=_make_list, tooltip='list = "" then list[1] = ..., list[2] = ...')

define("list_clear", "lists", "statement", "clear list {list}",
       specs={"list": variable(writes=True)}, code='{list} = ""')

define("list_set", "lists", "statement", "set {list} [ {index} ] to {value}",
       specs={"list": variable(writes=True), "index": inp("any", "1"), "value": inp("any", "")},
       code="{list}[{index}] = {value}", tooltip="Indexes can be numbers or text")

define("list_get", "lists", "value", "{list} [ {index} ]",
       specs={"list": variable(), "index": inp("any", "1")},
       code="{list}[{index}]")

define("list2_set", "lists", "statement", "set {list} [ {row} ] [ {col} ] to {value}",
       specs={"list": variable(writes=True), "row": inp("any", "1"), "col": inp("any", "1"), "value": inp("any", "")},
       code="{list}[{row}][{col}] = {value}", tooltip="A list of lists (2D array)")

define("list2_get", "lists", "value", "{list} [ {row} ] [ {col} ]",
       specs={"list": variable(), "row": inp("any", "1"), "col": inp("any", "1")},
       code="{list}[{row}][{col}]")

define("list_add", "lists", "statement", "add {value} to end of {list}",
       specs={"value": inp("any", ""), "list": variable(writes=True)},
       code="{list}[Array.GetItemCount({list}) + 1] = {value}")

define("list_remove", "lists", "statement", "remove item {index} from {list}",
       specs={"index": inp("any", "1"), "list": variable(writes=True)},
       code='Array.RemoveItem("{list}", {index})',
       tooltip="Array.RemoveItem takes the array's NAME as text")

call("list_count", "lists", "number of items in {list}", "Array.GetItemCount", ["list"],
     specs={"list": variable()})
call("list_has_index", "lists", "{list} has index {index}", "Array.ContainsIndex", ["list", "index"],
     shape="bool", specs={"list": variable(), "index": inp("any", "1")})
call("list_has_value", "lists", "{list} has value {value}", "Array.ContainsValue", ["list", "value"],
     shape="bool", specs={"list": variable(), "value": inp("any", "")})
call("list_indices", "lists", "all indices of {list}", "Array.GetAllIndices", ["list"],
     specs={"list": variable()})
call("list_is_array", "lists", "{list} is a list", "Array.IsArray", ["list"],
     shape="bool", specs={"list": variable()})
