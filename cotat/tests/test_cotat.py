import os
import pandas as pd
import numpy as np
from cotat.cotat import main

RESOURCES_PATH = os.path.join(os.path.dirname(__file__), 'resources')

def test_cotat():
    nodes = pd.read_csv(os.path.join(RESOURCES_PATH, 'nodes.csv'), index_col=0).replace({np.nan: None})
    nodes['date'] = pd.to_datetime(nodes['date']).apply(lambda x: x.date())
    nodes = nodes.replace({pd.NaT: None})
    edges = pd.read_csv(os.path.join(RESOURCES_PATH, 'edges.csv'), index_col=0)
    main('test.html', nodes, edges)
