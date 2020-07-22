import neo4j
from hashlib import md5


class Neo4jClient(object):

    def __init__(self, uri='bolt://localhost:7687'):
        self.connection = neo4j.GraphDatabase.driver(uri)
        self._cache = {'queries': {}, 'ids': {}}

    def make_query(self, query, **params) -> neo4j.Result:
        query_hash = md5(query.encode('utf-8'))
        if (result := self._cache['queries'].get(query_hash, False)):
            return result
        with self.connection.session() as sess:
            result = [*sess.run(query, **params)]
            self._cache['queries'][query_hash] = result
            return result

    def get(self, st_id: str) -> dict:
        if (result := self._cache['ids'].get(st_id, False)):
            return result
        q = 'match (n {{stId: $st_id}}) return n;'
        with self.connection.session() as sess:
            result = dict(sess.run(q, st_id=st_id))
            self._cache['ids'][st_id] = result
            return result

    def close(self):
        self.connection.close()
