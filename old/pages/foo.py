integrals_dic={'curve_1': {'span_5': 3.02, 'span_10': 8.17, 'span_20': 19.11, 'span_50': 55.15, 'span_100': 128.78, 'avg': 42.846, 'min': 3.02, 'max': 128.78}, 'curve_2': {'span_5': 2.83, 'span_10': 7.29, 'span_20': 16.89, 'span_50': 35.85, 'span_100': 35.85, 'avg': 19.742, 'min': 2.83, 'max': 35.85}, 'curve_3': {'span_5': 3.08, 'span_10': 8.27, 'span_20': 18.92, 'span_50': 52.14, 'span_100': 113.3, 'avg': 39.141999999999996, 'min': 3.08, 'max': 113.3}, 'agg': {'span_5': 0, 'span_10': 0, 'span_20': 0, 'span_50': 0, 
'span_100': 0, 'avg': 0, 'min': 0, 'max': 0}}

_=list(integrals_dic.keys()) [0]
agg_dic={k:0 for k in integrals_dic[_] .keys()}

import json 
import numpy as np 
import pandas as pd 
print(json.dumps(integrals_dic,indent=4))

# populate agg_dic with means 




print(df)