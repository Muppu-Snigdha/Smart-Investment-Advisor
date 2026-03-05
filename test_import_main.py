print('starting import test')
import importlib.util, sys
from pathlib import Path

path = Path(r'c:\Users\mahen\Downloads\smart investment advisor\smart investment advisor\main.py')
spec = importlib.util.spec_from_file_location('main_mod', str(path))
main_mod = importlib.util.module_from_spec(spec)
sys.modules['main_mod'] = main_mod
try:
    spec.loader.exec_module(main_mod)
    print('imported main without error')
except Exception as e:
    print('error importing main:', type(e).__name__, e)
    raise
