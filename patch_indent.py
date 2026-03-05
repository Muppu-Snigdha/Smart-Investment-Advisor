import pathlib

path = pathlib.Path(r'c:\Users\mahen\Downloads\smart investment advisor\smart investment advisor\main.py')
lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()

start, end = 588, 669
for i in range(start-1, end):
    # only indent if not already indented 4 spaces
    if not lines[i].startswith('    '):
        lines[i] = '    ' + lines[i]

path.write_text("\n".join(lines), encoding='utf-8')
print(f"Indented lines {start}-{end} in main.py")
