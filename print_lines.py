import pathlib
path=pathlib.Path(r'c:\Users\mahen\Downloads\smart investment advisor\smart investment advisor\main.py')
# read with explicit encoding to handle any special characters
lines=path.read_text(encoding='utf-8', errors='ignore').splitlines()
for i,line in enumerate(lines, start=1):
    if 580 <= i <= 677:
        print(f"{i:4}: {line}")
