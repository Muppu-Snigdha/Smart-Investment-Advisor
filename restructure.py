import pathlib

path = pathlib.Path(r"c:\Users\mahen\Downloads\smart investment advisor\smart investment advisor\main.py")
lines = path.read_text(encoding="utf-8").splitlines()
out_lines = []
inside = False
for idx, line in enumerate(lines):
    stripped = line.lstrip()
    if not inside and stripped.startswith('with home_tab:'):
        inside = True
        print(f"entering home section at line {idx+1}")
        out_lines.append(line)
        continue
    if inside and stripped.startswith('with about_tab:'):
        inside = False
        print(f"exiting home section at line {idx+1}")
        out_lines.append(line)
        continue
    if inside:
        out_lines.append('    ' + line)
        print(f"indented line {idx+1}: {line.strip()}")
    else:
        out_lines.append(line)

path.write_text("\n".join(out_lines), encoding="utf-8")
print("rewritten file")
