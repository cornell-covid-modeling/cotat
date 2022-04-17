# general imports
import pkgutil
import networkx as nx
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Tuple, Dict

# bokeh imports
from bokeh.plotting import figure, output_file, save
from bokeh.models.widgets.markups import Div
from bokeh.models.widgets.tables import TableColumn, DataTable
from bokeh.models.renderers import GlyphRenderer
from bokeh.layouts import row, gridplot, GridBox
from bokeh.plotting import from_networkx
from bokeh.models import (HoverTool, TapTool, ColumnDataSource, LabelSet, TextInput, Div,
                          Button, CustomJS, Circle, MultiLine, Panel, Tabs)

# =============================
# CONSTANTS
# =============================

POSITIVE_COLOR = "#DC0000"
NEGATIVE_COLOR = "#65ADFF"
NODE_ALPHA_DEFAULT = 1
NODE_SIZE_DEFAULT = 9
NODE_ALPHA_SELECTED= 1
NODE_SIZE_SELECTED = 16
NODE_ALPHA_UNSELECTED = 0.4
NODE_SIZE_UNSELECTED = 9

EDGE_ALPHA_CONTACT = 1
EDGE_ALPHA_DUMMY = 0.2
EDGE_DASH_CONTACT = []
EDGE_DASH_DUMMY = [5,5]
EDGE_WEIGHT_CONTACT = 1
EDGE_WEIGHT_DUMMY = 0.05

BUTTON_JS = pkgutil.get_data(__name__, "resources/button.js") \
                   .decode().format(**globals())
SEARCH_JS = pkgutil.get_data(__name__, "resources/search.js") \
                   .decode().format(**globals())
INSTRUCTIONS_HTML = pkgutil.get_data(__name__, "resources/instructions.html") \
                           .decode().format(**globals())

# =============================


def contact_graph(nodes: pd.DataFrame, edges: pd.DataFrame,
                  membership_cols: List[str] = None) -> nx.Graph:
    """Return a graph representing the contact tracing data.

    Edges are given an "edge_type" attribute which is "contact" for contact
    tracing data. For each membership column, edges are added between nodes
    that are members of the same group. The "edge_type" of these edges is the
    name of the membership column (E.g. membership column is "club" and nodes
    both belonging to "Club A" have an edge between them). Edges with
    "edge_type" set to "contact" have attribute "dummy" set to 0; otherwise, 1.

    Args:
        nodes (pd.DataFrame): Each row is node with column for every attribute.
        edges (pd.DataFrame): Dataframe with "source" and "target" columns.
        membership_cols (List[str]): List of columns recognized as memberships.

    Returns:
        nx.Graph: Contact tracing graph.
    """
    nodes = nodes.copy()
    edges = edges.copy()

    # edge attributes
    edges["dummy"] = 0
    edges["edge_type"] = "contact"
    G = nx.from_pandas_edgelist(edges, edge_attr=["dummy", "edge_type"])

    # node attributes
    nodes = nodes.reset_index().rename(columns={'index': 'id'})
    G.add_nodes_from(nodes["id"])
    node_attr = nodes.set_index("id").to_dict("index")
    nx.set_node_attributes(G, node_attr)

    # add membership dummy edges
    for membership_col in membership_cols:
        groups = nodes[membership_col].value_counts().to_dict()
        for group, n in groups.items():
            if group != "" and n > 1:
                members = list(nodes[nodes[membership_col] == group].index)
                for i in range(len(members)):
                    for j in range(len(members)):
                        if i < j and not G.has_edge(members[i], members[j]):
                            G.add_edge(members[i], members[j], dummy=1,
                                       edge_type=membership_col)

    return G


def main(date_str, nodes, edges, start, end):

    def node_positions(G):
        """Generate node posititions."""
        pos = nx.spring_layout(G, k=0.13, weight='weight', seed=1, iterations=150)
#         pos = nx.random_layout(G)
        xs = {k: v[0] for k,v in pos.items()}
        ys = {k: v[1] for k,v in pos.items()}
        nodes['x'] = nodes['id'].apply(lambda x: xs[x])
        nodes['y'] = nodes['id'].apply(lambda x: ys[x])
        return pos


    def blank_tab_plot(name, plot_width=1500, plot_height=700):
        """Create a blank for a tab."""
        plot = figure(title=name,
                  plot_width=plot_width,
                  plot_height=plot_height,
                  tools="pan,wheel_zoom,box_zoom,reset")
        plot.toolbar.logo = None
        plot.xgrid.grid_line_color = None
        plot.ygrid.grid_line_color = None
        plot.xaxis.visible = False
        plot.yaxis.visible = False
        plot.background_fill_color = None
        plot.border_fill_color = None
        plot.outline_line_color = None
        return plot


    def create_graph_renderer(G, pos):
        """Return a graph renderer for graph G with node positions pos."""
        graph_renderer = from_networkx(G, pos)
        graph_renderer.node_renderer.glyph = Circle(size="size",
                                                    fill_color='color',
                                                    fill_alpha='alpha',
                                                    line_alpha='alpha')
        graph_renderer.edge_renderer.glyph = MultiLine(line_width=3,
                                                       line_alpha='alpha',
                                                       line_dash='dash')

        return graph_renderer


    def add_case_labels(plot):
        """Add case labels to plot."""
        cases = nodes[~nodes['case'].isna()][['x','y','case']]
        cases['case'] = cases['case'].astype(int).astype(str)
        case_labels = ColumnDataSource(data=cases)
        labels = LabelSet(x='x', y='y', text='case',
                          x_offset=3, y_offset=3,
                          text_font_size='12px',
                          source=case_labels, render_mode='canvas')
        plot.add_layout(labels)


    def add_hover_labels(plot, graph_renderer):
        """Add hover labels to plot."""
        tooltips = [(attr, f"@{attr}") for attr in nodes.columns[1:]]
        node_hover = HoverTool(tooltips=tooltips,
                              renderers=[graph_renderer.node_renderer])

        plot.tools.append(node_hover)


    def create_plot(title, tab_name, G, pos):
        p = blank_tab_plot('%s:  %s' % (title, tab_name))
        graph_renderer = create_graph_renderer(G, pos)
        p.renderers.append(graph_renderer)
        add_case_labels(p)
        add_hover_labels(p, graph_renderer)

        node_source = graph_renderer.node_renderer.data_source

        button_code = BUTTON_JS
        text_code = SEARCH_JS

        button = Button(label="Reset", button_type="default")
        button.js_on_click(CustomJS(args={'source': node_source}, code=button_code))
        text_input = TextInput(value="case_number", title="Search Case:")
        text_input.js_on_change("value", CustomJS(args={'source': node_source}, code=text_code))

        instructions = blank_tab_plot("", plot_width=1500, plot_height=50)
        instructions.title.text_font_size = '0pt'
        instructions.toolbar_location=None
        instructions.min_border_top=0

        text = INSTRUCTIONS_HTML
        instructions = Div(text=text)

        plot = gridplot([[p], [row(text_input, button, sizing_mode='stretch_both')], [instructions]],
                        toolbar_options={'logo': None})

        return Panel(child=plot, title=tab_name)

    # TODO: factor this out as a helper method
    # limit nodes
    limit = False
    limit_all = False
    if limit:
        group_name = 'employee'
        group_of_interest = 1
        node_indices = list(nodes[nodes[group_name] == group_of_interest].index)

        if limit_all:
            edges = edges[(edges['source'].isin(node_indices)) & (edges['target'].isin(node_indices))]
        else:
            edges = edges[(edges['source'].isin(node_indices)) | (edges['target'].isin(node_indices))]
            adjacent = set(edges['source']).union(set(edges['target']))
            node_indices = set(node_indices).union(set(adjacent))

        nodes = nodes.iloc[list(node_indices)]

    groups = ["group_1", "group_2", "group_3"]
    G = contact_graph(nodes, edges, membership_cols=groups)

    # TODO: remove this later
    nodes = nodes.reset_index().rename(columns={'index': 'id'})

    # set node color of positive cases
    nx.set_node_attributes(G, values=9, name='size')

    offset = 14  # days (2 weeks)
    alphas = list(np.linspace(0.5, 1, (end - start).days + offset + 1))
    node_alpha = {}
    node_color = {}
    for id, date in nx.get_node_attributes(G, "date").items():
        # blue if tested positive before 2 weeks of [start] or after [end]
        if pd.isnull(date) or date > end or (start - date).days > offset:
            node_alpha[id] = 1
            node_color[id] = NEGATIVE_COLOR
        # red if tested positive within 2 weeks of [start] and before [end]
        else:
            node_alpha[id] = alphas[(date - start).days + offset]
            node_color[id] = POSITIVE_COLOR
    nx.set_node_attributes(G, values=node_alpha, name='alpha')
    nx.set_node_attributes(G, values=node_color, name='color')

    # set edge properties of dummy vs. actual edges
    dummy_attribute = nx.get_edge_attributes(G, 'dummy').items()
    edge_alpha = {k:{0:EDGE_ALPHA_CONTACT, 1:EDGE_ALPHA_DUMMY}[v] for k,v in dummy_attribute}
    nx.set_edge_attributes(G, values=edge_alpha, name='alpha')
    edge_dash = {k:{0:EDGE_DASH_CONTACT, 1:EDGE_DASH_DUMMY}[v] for k,v in dummy_attribute}
    nx.set_edge_attributes(G, values=edge_dash, name='dash')
    edge_weight = {k:{0:EDGE_WEIGHT_CONTACT, 1:EDGE_WEIGHT_DUMMY}[v] for k,v in dummy_attribute}
    nx.set_edge_attributes(G, values=edge_weight, name='weight')

    # create plot
    title = 'Contact Tracing Visualization'  # TODO: better title

    pos = node_positions(G)

    edge_alpha = {k:{0:EDGE_ALPHA_CONTACT, 1:EDGE_ALPHA_DUMMY}[v] for k,v in dummy_attribute}
    nx.set_edge_attributes(G, values=edge_alpha, name='alpha')

    tab1 = create_plot(title, 'All', G, pos)

    edge_alpha = {k:{0:EDGE_ALPHA_CONTACT, 1:0}[v] for k,v in dummy_attribute}
    nx.set_edge_attributes(G, values=edge_alpha, name='alpha')

    tab2 = create_plot(title, 'Contact Traces', G, pos)

    edge_alpha = {k:{0:0, 1:EDGE_ALPHA_DUMMY}[v] for k,v in dummy_attribute}
    nx.set_edge_attributes(G, values=edge_alpha, name='alpha')

    tab3 = create_plot(title, 'Groups', G, pos)

    tabs = [tab1, tab2, tab3]

    for group in groups:
        edge_alpha = {k:(EDGE_ALPHA_DUMMY if v == group else 0) for k,v in nx.get_edge_attributes(G, 'edge_type').items()}
        nx.set_edge_attributes(G, values=edge_alpha, name='alpha')

        tabs.append(create_plot(title, group, G, pos))

    plot = Tabs(tabs=tabs)

    # export
    output_file(date_str, title=date_str)
    save(plot)
