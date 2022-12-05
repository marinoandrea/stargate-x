from distutils.core import setup

VERSION = '1.1.0'

setup(
    name='stargate-x',
    packages=['stargate_x'],
    version=VERSION,
    description=(
        '''
        The package is a python implementation of a bipartite directed
        multigraph extracted from the Reactome database.
        Its underlying implementation uses `networkx`.
        '''
    ),
    author='Andrea Marino',
    author_email='am.marinoandrea@gmail.com',
    url='https://github.com/marinoandrea/stargate-x',
    download_url=(
        f'https://github.com/marinoandrea/stargate-x/tarball/{VERSION}'
    ),
    keywords=['reactome', 'pathway', 'pathways', 'graph', 'bipartite'],
    install_requires=['networkx', 'neo4j'],
    include_package_data=True,
    package_data={
        'stargate_x': [
            'data/*.pickle',
            'queries/*.cypher'
        ],
    }
)
