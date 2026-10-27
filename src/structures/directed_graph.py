from .hash_map import HashMap
from .hash_set import HashSet


class DirectedGraph:
    def __init__(self):
        self.outgoing = HashMap()
        self.incoming = HashMap()
        self.edge_count = 0

    def add_vertex(self, vertex):
        if not self.outgoing.contains(vertex):
            self.outgoing.put(vertex, HashSet())
            self.incoming.put(vertex, HashSet())

    def add_edge(self, source, destination):
        self.add_vertex(source)
        self.add_vertex(destination)

        destinations = self.outgoing.get(source)
        sources = self.incoming.get(destination)

        if not destinations.contains(destination):
            destinations.add(destination)
            sources.add(source)
            self.edge_count += 1

    def has_edge(self, source, destination):
        if not self.outgoing.contains(source):
            return False
        return self.outgoing.get(source).contains(destination)

    def neighbors(self, vertex):
        if not self.outgoing.contains(vertex):
            raise KeyError(vertex)
        return self.outgoing.get(vertex).values()

    def sources(self, vertex):
        if not self.incoming.contains(vertex):
            raise KeyError(vertex)
        return self.incoming.get(vertex).values()

    def vertices(self):
        return self.outgoing.keys()

    def vertex_count(self):
        return self.outgoing.size()
