import numpy as np
import pandas as pd

# Utilities
def nest(d: dict) -> dict:
    result = {}
    for key, value in d.items():
        target = result
        for k in key[:-1]:  # traverse all keys but the last
            target = target.setdefault(k, {})
        target[key[-1]] = value
    return result

def df_to_nested_dict(df: pd.DataFrame) -> dict:
    d = df.to_dict(orient='index')
    return {k: nest(v) for k, v in d.items()}