from reactome_graph.utils.cache import cached

import neo4j


class Neo4jClient(object):

    def __init__(self, uri='bolt://localhost:7687'):
        self.connection = neo4j.GraphDatabase.driver(uri)

    @cached
    def make_query(self, query: str, **params) -> neo4j.Result:
        with self.connection.session() as sess:
            return [*sess.run(query, **params)]

    @cached
    def get(self, st_id: str) -> dict:
        q = 'match (n {{stId: $st_id}}) return n;'
        with self.connection.session() as sess:
            return dict(sess.run(q, st_id=st_id))

    def close(self):
        self.connection.close()
