import pandas as pd
from pathlib import Path

project_root = Path(__file__).resolve().parent
df = pd.read_csv(project_root / 'data' / 'SMI.csv.zip')
print(df.columns)