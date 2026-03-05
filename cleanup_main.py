import pathlib

path = pathlib.Path(r"c:\Users\mahen\Downloads\smart investment advisor\smart investment advisor\main.py")
lines = path.read_text().splitlines()

idx = None
for i, l in enumerate(lines):
    if "YAHOO LINK BOX" in l:
        idx = i
        break

print('--- DEBUG LINES AROUND PATTERN ---')
for j in range(max(0, idx-3), min(len(lines), idx+6)):
    print(j+1, repr(lines[j]))

if idx is not None:
    new = lines[:idx]
    path.write_text("\n".join(new))
    print(f"Truncated main.py at line {idx+1}")
else:
    print("Pattern not found, nothing changed")
