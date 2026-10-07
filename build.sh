pyinstaller -F --hidden-import=flask --add-data "examples:examples" --add-data "static:static" --add-data "sbratch:sbratch" --add-data "tests:tests" app.py
