from ..registry import category, define, inp, slot, variable, text
# all the "control" blocks (anything that contains other code blocks)
category("control", "Control", "#ffab19", 10)

define("start", "control", "hat", "when program starts", "",
    tooltip="Your program starts here. Everything attached below becomes the generated code.")

define("if", "control", "statement", "if {cond} then {body}",
    specs={"cond": inp(None), "body": slot()},
    code="If {cond} Then\n{body}\nEndIf",
    tooltip="If ... Then ... EndIf")

define("if_else", "control", "statement", "if {cond} then {then} else {otherwise}",
    specs={"cond": inp(None), "then": slot(), "otherwise": slot()},
    code="If {cond} Then\n{then}\nElse\n{otherwise}\nEndIf",
    tooltip="If ... Then ... Else ... EndIf")

define("if_elseif", "control", "statement", "if {c1} then {b1} else if {c2} then {b2} else {b3}",
    specs={"c1": inp(None), "b1": slot(), "c2": inp(None), "b2": slot(), "b3": slot()},
    code="If {c1} Then\n{b1}\nElseIf {c2} Then\n{b2}\nElse\n{b3}\nEndIf",
    tooltip="If ... ElseIf ... Else ... EndIf")

define("while", "control", "statement", "repeat while {cond} {body}",
    specs={"cond": inp(None), "body": slot()},
    code="While {cond}\n{body}\nEndWhile",
    tooltip="While ... EndWhile")

define("for", "control", "statement", "for {var} from {start} to {end} {body}",
    specs={"var": variable(writes=True), "start": inp("number", "1"), "end": inp("number", "10"), "body": slot()},
    code="For {var} = {start} To {end}\n{body}\nEndFor",
    tooltip="For ... = ... To ... EndFor")

define("for_step", "control", "statement", "for {var} from {start} to {end} step {step} {body}",
    specs={"var": variable(writes=True), "start": inp("number", "10"), "end": inp("number", "0"),
        "step": inp("number", "-2"), "body": slot()},
    code="For {var} = {start} To {end} Step {step}\n{body}\nEndFor",
    tooltip="For ... = ... To ... Step ... EndFor")

define("repeat", "control", "statement", "repeat {count} times {body}",
    specs={"count": inp("number", "10"), "body": slot()},
    code="For {$loopIndex} = 1 To {count}\n{body}\nEndFor",
    tooltip="A For loop with a hidden counter variable")

define("forever", "control", "statement", "repeat forever {body}",
    specs={"body": slot()},
    code="While \"True\"\n{body}\nEndWhile",
    tooltip="Loops until the program ends (use Program.End)")

define("foreach", "control", "statement", "for each {item} in list {list} {body}",
    specs={"item": variable(writes=True), "list": variable(), "body": slot()},
    code=("{$indices} = Array.GetAllIndices({list})\n"
        "For {$loopIndex} = 1 To Array.GetItemCount({$indices})\n"
        "    {item} = {list}[{$indices}[{$loopIndex}]]\n"
        "{body}\n"
        "EndFor"),
    tooltip="Small Basic has no For Each, so this loops over Array.GetAllIndices")

define("comment", "control", "statement", "comment {text}",
    specs={"text": text("explain what happens here")},
    code="' {text|comment}",
    tooltip="A note that Small Basic ignores")
