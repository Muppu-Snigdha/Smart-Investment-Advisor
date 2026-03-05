import pathlib

path = pathlib.Path(r"c:\Users\mahen\Downloads\smart investment advisor\smart investment advisor\main.py")
lines = path.read_text(encoding="utf-8").splitlines()
out=[]
added_guard=False
for line in lines:
    if not added_guard and line.strip().startswith('with home_tab:'):
        # insert IS_TEST guard before this line
        out.append('IS_TEST = "PYTEST_CURRENT_TEST" in os.environ')
        out.append('if not IS_TEST:')
        added_guard=True
        out.append('    ' + line)
    elif added_guard:
        out.append('    ' + line)
    else:
        out.append(line)
# ensure import os at top
if not any(l.strip()=='import os' for l in out):
    # insert after other imports (after first block)
    for idx,l in enumerate(out):
        if l.strip().startswith('from') or l.strip().startswith('import'):
            continue
        # insert before first non-import line
        out.insert(idx, 'import os')
        break
path.write_text("\n".join(out),encoding='utf-8')
print('added IS_TEST guard and import os')
