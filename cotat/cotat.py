# general imports
import pkgutil
import networkx as nx
import pandas as pd
import numpy as np
import datetime
from typing import List

# bokeh imports
from bokeh.plotting import figure, output_file, save
from bokeh.layouts import row, gridplot
from bokeh.plotting import from_networkx
from bokeh.models import (HoverTool, ColumnDataSource, LabelSet, TextInput,
                          Div, Button, CustomJS, Circle, MultiLine,
                          Panel, Tabs)

# =============================
# CONSTANTS
# =============================

GRAPH_PLOT_HEIGHT = 700
GRAPH_PLOT_WIDTH = 1500
INSTRUCTIONS_PLOT_HEIGHT = 50
INSTRUCTIONS_PLOT_WIDTH = 1500

POSITIVE_COLOR = "#DC0000"
NEGATIVE_COLOR = "#65ADFF"
NODE_ALPHA_DEFAULT = 1
NODE_SIZE_DEFAULT = 9
NODE_ALPHA_SELECTED = 1
NODE_SIZE_SELECTED = 16
NODE_ALPHA_UNSELECTED = 0.4
NODE_SIZE_UNSELECTED = 9

EDGE_ALPHA_CONTACT = 1
EDGE_ALPHA_DUMMY = 0.2
EDGE_DASH_CONTACT = []
EDGE_DASH_DUMMY = [5,5]
EDGE_WEIGHT_CONTACT = 1
EDGE_WEIGHT_DUMMY = 0.05
EDGE_LINE_WIDTH = 3

LABEL_OFFSET = 3
LABEL_TEXT_SIZE = "12px"

BUTTON_JS = pkgutil.get_data(__name__, "resources/button.js") \
                   .decode().format(**globals())
SEARCH_JS = pkgutil.get_data(__name__, "resources/search.js") \
                   .decode().format(**globals())
INSTRUCTIONS_HTML = pkgutil.get_data(__name__, "resources/instructions.html") \
                           .decode().format(**globals())

# =============================


def _contact_graph(nodes: pd.DataFrame, edges: pd.DataFrame,
                   membership_cols: List[str] = []) -> nx.Graph:
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


def _blank_plot(name, plot_height, plot_width):
    """Create a blank plot with default configurations set."""
    plot = figure(title=name,
                  plot_width=plot_width,
                  plot_height=plot_height,
                  tools="pan, wheel_zoom, box_zoom, reset")
    plot.toolbar.logo = None
    plot.xgrid.grid_line_color = None
    plot.ygrid.grid_line_color = None
    plot.xaxis.visible = False
    plot.yaxis.visible = False
    plot.background_fill_color = None
    plot.border_fill_color = None
    plot.outline_line_color = None
    return plot


def _graph_renderer(G):
    """Return a graph renderer for graph G."""
    graph_renderer = from_networkx(G, nx.get_node_attributes(G, "pos"))
    graph_renderer.node_renderer.glyph = Circle(size="size",
                                                fill_color="color",
                                                fill_alpha="alpha",
                                                line_alpha="alpha")
    graph_renderer.edge_renderer.glyph = MultiLine(line_width=EDGE_LINE_WIDTH,
                                                   line_alpha="alpha",
                                                   line_dash="dash")
    return graph_renderer


def _case_labels(G):
    """Return LabelSet object with case number labels for given nodes."""
    case_dict = nx.get_node_attributes(G, "case")
    case_dict = {k:v for k,v in case_dict.items() if not pd.isnull(v)}
    ids, case = zip(*case_dict.items())
    pos_dict = nx.get_node_attributes(G, "pos")
    pos = [pos_dict[id] for id in ids]
    x, y = list(zip(*pos))
    case_labels = ColumnDataSource(data={"x": x, "y": y, "case": case})
    return LabelSet(x="x", y="y", text="case",
                    x_offset=LABEL_OFFSET, y_offset=LABEL_OFFSET,
                    text_font_size=LABEL_TEXT_SIZE,
                    source=case_labels, render_mode="canvas")


def _hover_labels(G, graph_renderer, attributes):
    """Add hover labels to plot."""
    tooltips = [(attr, f"@{attr}") for attr in attributes]
    return HoverTool(tooltips=tooltips,
                     renderers=[graph_renderer.node_renderer])


def _tab(title, tab_name, G, attributes):
    """Return a tab (Panel) showing graph G of nodes"""
    p = _blank_plot(f"{title}: {tab_name}", GRAPH_PLOT_HEIGHT,
                    GRAPH_PLOT_WIDTH)
    graph_renderer = _graph_renderer(G)
    p.renderers.append(graph_renderer)
    p.add_layout(_case_labels(G))
    p.tools.append(_hover_labels(G, graph_renderer, attributes))

    # add custom JS to button and search bar
    node_source = graph_renderer.node_renderer.data_source
    button = Button(label="Reset", button_type="default")
    button.js_on_click(CustomJS(args={"source": node_source}, code=BUTTON_JS))
    text_input = TextInput(value="case_number", title="Search Case:")
    text_input.js_on_change("value", CustomJS(args={"source": node_source},
                                              code=SEARCH_JS))

    # aggregate plot
    plot = gridplot([[p],
                     [row(text_input, button, sizing_mode="stretch_both")],
                     [Div(text=INSTRUCTIONS_HTML)]],
                    toolbar_options={'logo': None})

    return Panel(child=plot, title=tab_name)


def visualization(title: str, file_name: str, nodes: pd.DataFrame,
                  edges: pd.DataFrame, start: datetime.date,
                  end: datetime.date, membership_cols: List[str] = []):
    """Write an HTML visualization of the given contact tracing graph.

    The visualization has the following tabs:
    (1) All: all edges (both contact and membership edges) shown
    (2) Contact Traces: only contact edges are shown
    (3) Membership: only membership edges are shown
    Furthermore, there is a membership tab for every membership column passed.

    Args:
        title (str): Title of the visualization.
        file_name (str): Name of the file to be written.
        G (nx.Graph): NetworkX graph with contact tracing data.
        nodes (pd.DataFrame): Each row is node with column for every attribute.
        edges (pd.DataFrame): Dataframe with "source" and "target" columns.
        start (datetime.date): Start date (show cases outside the 2 weeks \
            leading up to this data as inactive (blue) on the visualization).
        end (datetime.date): End date (show cases after this data as inactive \
            (blue) on the visualization).
        membership_cols (List[str]): List of columns recognized as memberships.
    """
    attributes = nodes.columns

    G = _contact_graph(nodes, edges, membership_cols)

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
    dummy_attribute = nx.get_edge_attributes(G, "dummy").items()

    edge_attributes = [
        (EDGE_ALPHA_CONTACT, EDGE_ALPHA_DUMMY, "alpha"),
        (EDGE_DASH_CONTACT, EDGE_DASH_DUMMY, "dash"),
        (EDGE_WEIGHT_CONTACT, EDGE_WEIGHT_DUMMY, "weight")
    ]

    for contact, dummy, name in edge_attributes:
        alpha = {k:{0:contact, 1:dummy}[v] for k,v in dummy_attribute}
        nx.set_edge_attributes(G, values=alpha, name=name)

    pos = nx.spring_layout(G, k=0.13, weight="weight", seed=1, iterations=150)
    nx.set_node_attributes(G, pos, "pos")

    # all edges
    edge_alpha = {k:{0:EDGE_ALPHA_CONTACT, 1:EDGE_ALPHA_DUMMY}[v]
                  for k,v in dummy_attribute}
    nx.set_edge_attributes(G, values=edge_alpha, name="alpha")
    tab1 = _tab(title, "All", G, attributes)

    # only contact edges
    edge_alpha = {k:{0:EDGE_ALPHA_CONTACT, 1:0}[v] for k,v in dummy_attribute}
    nx.set_edge_attributes(G, values=edge_alpha, name="alpha")
    tab2 = _tab(title, "Contact Traces", G, attributes)

    # only group edges
    edge_alpha = {k:{0:0, 1:EDGE_ALPHA_DUMMY}[v] for k,v in dummy_attribute}
    nx.set_edge_attributes(G, values=edge_alpha, name='alpha')
    tab3 = _tab(title, "Membership", G, attributes)

    tabs = [tab1, tab2, tab3]

    # tab for every membership column
    for membership in membership_cols:
        edge_alpha = {k:(EDGE_ALPHA_DUMMY if v == membership else 0)
                      for k,v in nx.get_edge_attributes(G,'edge_type').items()}
        nx.set_edge_attributes(G, values=edge_alpha, name='alpha')

        tabs.append(_tab(title, membership, G, attributes))

    plot = Tabs(tabs=tabs)

    # export
    output_file(file_name, title=title)
    save(plot)
