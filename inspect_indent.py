import pathlib
path=pathlib.Path('c:/Users/mahen/Downloads/smart investment advisor/smart investment advisor/main.py')
lines=path.read_text().splitlines()
for i in range(720,750):
    print(i+1, repr(lines[i]))
