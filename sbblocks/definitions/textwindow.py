from ..registry import category, define, inp, dropdown
from ._helpers import call

category("textwindow", "TextWindow", "#2F8FDD", 50)

COLORS = ["Black", "Blue", "Cyan", "Gray", "Green", "Magenta", "Red", "White", "Yellow",
          "DarkBlue", "DarkCyan", "DarkGray", "DarkGreen", "DarkMagenta", "DarkRed", "DarkYellow"]

call("tw_writeline", "textwindow", "TextWindow.WriteLine {value}", "TextWindow.WriteLine", ["value"],
     kind="statement", specs={"value": inp("any", "Hello, World!")})
call("tw_write", "textwindow", "TextWindow.Write {value}", "TextWindow.Write", ["value"],
     kind="statement", specs={"value": inp("any", "Hello")})
call("tw_read", "textwindow", "TextWindow.Read", "TextWindow.Read", [],
     tooltip="Waits for the user to type a line of text")
call("tw_readnumber", "textwindow", "TextWindow.ReadNumber", "TextWindow.ReadNumber", [],
     tooltip="Waits for the user to type a number")
call("tw_clear", "textwindow", "TextWindow.Clear", "TextWindow.Clear", [], kind="statement")
call("tw_show", "textwindow", "TextWindow.Show", "TextWindow.Show", [], kind="statement")
call("tw_hide", "textwindow", "TextWindow.Hide", "TextWindow.Hide", [], kind="statement")
call("tw_pause", "textwindow", "TextWindow.Pause", "TextWindow.Pause", [], kind="statement",
     tooltip='Shows "Press any key to continue..." and waits')
call("tw_pause_if_visible", "textwindow", "TextWindow.PauseIfVisible", "TextWindow.PauseIfVisible", [],
     kind="statement")
call("tw_pause_silent", "textwindow", "TextWindow.PauseWithoutMessage", "TextWindow.PauseWithoutMessage", [],
     kind="statement")

define("tw_fg", "textwindow", "statement", "TextWindow.ForegroundColor = {color}",
       specs={"color": dropdown(COLORS, "Yellow")}, code='TextWindow.ForegroundColor = "{color}"')
define("tw_bg", "textwindow", "statement", "TextWindow.BackgroundColor = {color}",
       specs={"color": dropdown(COLORS, "Black")}, code='TextWindow.BackgroundColor = "{color}"')
define("tw_title", "textwindow", "statement", "TextWindow.Title = {value}",
       specs={"value": inp("any", "My Program")}, code="TextWindow.Title = {value}")
define("tw_cursor", "textwindow", "statement", "move cursor to column {x} row {y}",
       specs={"x": inp("number", "1"), "y": inp("number", "1")},
       code="TextWindow.CursorLeft = {x}\nTextWindow.CursorTop = {y}",
       tooltip="TextWindow.CursorLeft / TextWindow.CursorTop")
define("tw_position", "textwindow", "statement", "move window to left {x} top {y}",
       specs={"x": inp("number", "100"), "y": inp("number", "100")},
       code="TextWindow.Left = {x}\nTextWindow.Top = {y}",
       tooltip="TextWindow.Left / TextWindow.Top")
define("tw_get", "textwindow", "value", "TextWindow.{prop}",
       specs={"prop": dropdown(["CursorLeft", "CursorTop", "Left", "Top", "Title",
                                "ForegroundColor", "BackgroundColor"])},
       code="TextWindow.{prop}", tooltip="Read a TextWindow property")
