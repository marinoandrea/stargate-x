from distutils.core import setup


setup(
  name='reactome-graph',
  packages=['reactome_graph'],
  version='1.0',
  description=(
    '''
    The package is a python implementation of a bipartite directed multigraph
    extracted from the Reactome database.
    Its underlying implementation uses `networkx`.
    '''
  ),
  author='Andrea Marino',
  author_email='am.marinoandrea@gmail.com',
  url='https://github.com/marinoandrea/reactome-graph',
  download_url='https://github.com/marinoandrea/reactome-graph/tarball/1.0.4',
  keywords=['reactome', 'pathway', 'pathways', 'graph', 'bipartite'],
  include_package_data=True,
  install_requires=['networkx', 'neo4j', 'numpy', 'scipy'],
  package_data={
    'reactome_graph.data': 'reactome_graph/data/*.pickle',
    'reactome_graph.queries': 'reactome_graph/queries/*.cypher',
  }
)
