import pathlib

path = pathlib.Path(r"c:\Users\mahen\Downloads\smart investment advisor\smart investment advisor\main.py")
lines = path.read_text(encoding="utf-8").splitlines()
out=[]
commenting=False
for line in lines:
    if not commenting and line.strip() == '}' :
        # start comment block
        commenting=True
        out.append('# ' + line + '  # removed stray brace and start duplicate comment')
        continue
    if commenting and line.strip().startswith('with about_tab:'):
        commenting=False
        out.append(line)
        continue
    if commenting:
        out.append('# ' + line)
    else:
        out.append(line)
path.write_text("\n".join(out), encoding='utf-8')
print('commented duplicate block')