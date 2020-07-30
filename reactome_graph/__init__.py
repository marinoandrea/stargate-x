ENTITY, EVENT = 0, 1
EDGES_QUERY = 'reactome_graph/queries/edges.cypher'
PATHWAYS_QUERY = 'reactome_graph/queries/pathways.cypher'

from reactome_graph.graph_builder import GraphBuilder  # noqa: F401, E402
from reactome_graph.analysis import *  # noqa: F401, E402, F403
