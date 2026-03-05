import pathlib
path = pathlib.Path(r'c:\Users\mahen\Downloads\smart investment advisor\smart investment advisor\main.py')
lines = path.read_text().splitlines()
# remove lines that consist solely of ")"
new = [l for l in lines if l.strip() != ")"]
if len(new) != len(lines):
    path.write_text("\n".join(new) + "\n")
    print('removed stray closing-parenthesis lines')
else:
    print('no stray lines found')
