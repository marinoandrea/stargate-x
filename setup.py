from distutils.core import setup

setup(
    name='reactome-graph',
    packages=[
        'reactome_graph',
        'reactome_graph.utils'
    ],
    version='2.0.0',
    description=(
        '''
        The package is a python implementation of a bipartite directed
        multigraph extracted from the Reactome database.
        Its underlying implementation uses `networkx`.
        '''
    ),
    author='Andrea Marino',
    author_email='am.marinoandrea@gmail.com',
    url='https://github.com/marinoandrea/reactome-graph',
    download_url=(
        'https://github.com/marinoandrea/reactome-graph/tarball/1.0.7'
    ),
    keywords=['reactome', 'pathway', 'pathways', 'graph', 'bipartite'],
    install_requires=['networkx', 'neo4j'],
    include_package_data=True,
    package_data={
        'reactome_graph': [
            'data/*.pickle',
            'queries/*.cypher'
        ],
    }
)
