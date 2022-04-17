import os
import pandas as pd
import numpy as np
from datetime import date
from cotat.cotat import main

RESOURCES_PATH = os.path.join(os.path.dirname(__file__), 'resources')

def test_cotat():
    nodes = pd.read_csv(os.path.join(RESOURCES_PATH, 'nodes.csv'), index_col=0).replace({np.nan: None})
    nodes['date'] = pd.to_datetime(nodes['date']).apply(lambda x: x.date())
    nodes = nodes.replace({pd.NaT: None})
    edges = pd.read_csv(os.path.join(RESOURCES_PATH, 'edges.csv'), index_col=0)
    start = date(2021, 12, 1)
    end = date(2021, 12, 5)
    main('test.html', nodes, edges, start, end)
