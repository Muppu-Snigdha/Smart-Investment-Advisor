import pathlib, subprocess, os
repo=pathlib.Path(r"c:\Users\mahen\Downloads\smart investment advisor\smart investment advisor")
os.chdir(repo)
orig = subprocess.check_output(["git","show","HEAD:main.py"]).decode('utf-8')
path = repo / "main.py"
path.write_text(orig, encoding='utf-8')
print('wrote HEAD content to main.py')
print('first 20 lines of restored file:')
print('\n'.join(orig.splitlines()[:20]))
