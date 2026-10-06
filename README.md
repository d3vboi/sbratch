# Small Basic Blocks

A Scratch-style, drag-and-drop block editor that writes **Small Basic** code for you.
Python (Flask) backend, plain HTML/CSS/JS frontend (no build step, no CDN).

## Run

```bash
pip install -r requirements.txt
python app.py                      # http://127.0.0.1:5000
# production / many users:
gunicorn -w 4 --threads 4 -b 0.0.0.0:8000 app:app
python tests/test_generator.py     # or: pytest tests
```

## Using it

* Drag blocks from the palette under **when program starts**. Drop a block on the palette to delete it.
* Drag a block in a stack to move it and everything below it. Right-click a block to duplicate or delete just that block.
* Plug value blocks (variables, `+`, `Text.Append`, ...) into the round/hex sockets, or just type a value into a socket.
* **Make a variable** in the Variables category; variable dropdowns also offer "New variable...".
* The code pane updates live, with errors (red) and warnings (orange); click a message to jump to the block.
* Undo/redo (Ctrl+Z / Ctrl+Y), autosave in your browser, Export/Import as JSON, **Copy** or **Download .sb**.

## Multi-user design

The server is **stateless**: every user's workspace lives in their own browser (localStorage) and is POSTed to
`/api/generate` when it changes. There is no shared mutable state, so any number of users can work at once.
Requests are size-limited (1 MB), nesting/node counts are capped, and the generator only *walks* the JSON - nothing is
evaluated. Generated code only uses Small Basic objects on an allow-list (TextWindow, Text, Math, Array, Clock,
Program, Stack); no File, Network, Desktop, subroutines, Goto, or events.

## Layout

```
app.py                       Flask routes (/, /api/blocks, /api/generate, /api/examples)
sbblocks/
  lang.py                    identifiers, reserved words, string/number literal helpers
  registry.py                category() / define() and the part helpers (inp, dropdown, slot, ...)
  generator.py               workspace JSON -> Small Basic code + diagnostics
  examples.py                example programs
  definitions/               ONE FILE PER CATEGORY: control, variables, operators, lists,
                             textwindow, text, math_, stack, clock, program
static/                      index.html, style.css, app.js (renders whatever the catalog says)
tests/test_generator.py
```

## Adding things

**A new block** - add a `define()` call to a file in `sbblocks/definitions/`:

```python
define("tw_blink", "textwindow", "statement", "blink text {times} times",
       specs={"times": inp("number", "3")},
       code=("For {$i} = 1 To {times}\n"
             "    TextWindow.WriteLine(\"*\")\n"
             "    Program.Delay(500)\n"
             "EndFor"))
```

* `kind`: `statement`, `value` (gives a result; `shape="bool"` for true/false), or `hat` (stack start).
* `pattern`: words are labels, `{name}` are parts described in `specs`.
* Parts: `inp(inline, default)` socket (`None` = must be filled by a block, `"any"`, `"number"`, `"text"`),
  `dropdown([...])`, `text()`, `number()`, `variable(writes=False)`, `slot()` (nested blocks), `many(count, min, max)`.
* `code`: template (or a function taking a context `c` with `c.input()`, `c.field()`, `c.items()`, `c.slot()`,
  `c.temp()`, `c.problem()`). `{x}` = input/field, `{x|op}` = input as an operator operand (keeps parentheses),
  `{$tmp}` = unique temp variable, `{slot}` alone on a line = indented nested statements.
* For plain `Object.Member(args)` blocks use `call(...)` / `prop(...)` from `definitions/_helpers.py`.

**A new category** - create `sbblocks/definitions/mycat.py` starting with `category("mycat", "My Category", "#hex", order)`,
add `define()` calls, and import it in `definitions/__init__.py`. The frontend picks it up automatically.

## Notes

* `Array.RemoveItem` is generated with the list *name* as text (`Array.RemoveItem("fruits", 2)`) as Small Basic's
  documentation describes; check it in your Small Basic version if removal misbehaves.
* Small Basic has no `Not`, `For Each`, `Break`: the *not* block compares with `False`, *for each* loops over
  `Array.GetAllIndices`, and loop temp variables get unique names that never clash with yours.
* Not included (yet): GraphicsWindow, Turtle, Mouse/Keyboard, Controls, File, Network, Timer/Event, Sub/Goto.
