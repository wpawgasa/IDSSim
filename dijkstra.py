import sys
import heapq

class Vertex:
    def __init__(self, node, i, j):
        self.id = node
        self.i = i
        self.j = j
        self.adjacent = {}
        # Set distance to infinity for all nodes
        self.distance = sys.maxsize
        # Mark all nodes unvisited
        self.visited = False
        # Predecessor
        self.previous = None

    def add_neighbor(self, neighbor, weight=0):
        self.adjacent[neighbor] = weight

    def get_connections(self):
        return self.adjacent.keys()

    def get_id(self):
        return self.id

    def get_i(self):
        return self.i

    def get_j(self):
        return self.j

    def get_weight(self, neighbor):
        return self.adjacent[neighbor]

    def set_distance(self, dist):
        self.distance = dist

    def get_distance(self):
        return self.distance

    def set_previous(self, prev):
        self.previous = prev

    def set_visited(self):
        self.visited = True

    def __str__(self):
        return str(self.id) + ' adjacent: ' + str([x.id for x in self.adjacent])


class Graph:
    def __init__(self):
        self.vert_dict = {}
        self.num_vertices = 0

    def __iter__(self):
        return iter(self.vert_dict.values())

    def add_vertex(self, node, i, j):
        self.num_vertices = self.num_vertices + 1
        new_vertex = Vertex(node, i, j)
        self.vert_dict[node] = new_vertex
        return new_vertex

    def get_vertex(self, n):
        if n in self.vert_dict:
            return self.vert_dict[n]
        else:
            return None

    def add_edge(self, frm, to, cost = 0):
        if frm not in self.vert_dict:
            self.add_vertex(frm)
        if to not in self.vert_dict:
            self.add_vertex(to)

        self.vert_dict[frm].add_neighbor(self.vert_dict[to], cost)
        self.vert_dict[to].add_neighbor(self.vert_dict[frm], cost)

    def get_vertices(self):
        return self.vert_dict.keys()

    def set_previous(self, current):
        self.previous = current

    def get_previous(self, current):
        return self.previous


class Dijkstra:
    def __init__(self, graph):
        self.aGraph = graph

    def get_g(self):
        return self.aGraph

    def shortest(self, v, path):
        ''' make shortest path from v.previous'''
        if v.previous:
            path.append(v.previous)
            self.shortest(v.previous, path)
        return

    def traversing(self,start,target):
        print("Dijkstra's shortest path")
        # Set the distance for the start node to zero
        start_vertex = self.aGraph.get_vertex(start)
        target_vertex = self.aGraph.get_vertex(target)
        start_vertex.set_distance(0)

        # Put tuple pair into the priority queue
        unvisited_queue = [(v.get_distance(), v.get_id(), v) for v in self.aGraph]
        heapq.heapify(unvisited_queue)

        while len(unvisited_queue):
            # Pops a vertex with the smallest distance
            uv = heapq.heappop(unvisited_queue)
            current = uv[2]
            current.set_visited()
            if current.get_id() != target:
                # print(current.get_distance())
                # for next in v.adjacent:
                for next in current.adjacent:
                    # if visited, skip
                    if next.visited:
                        continue
                    new_dist = current.get_distance() + current.get_weight(next)

                    if new_dist < next.get_distance():
                        next.set_distance(new_dist)
                        next.set_previous(current)
                        # print('updated : current = %s next = %s new_dist = %f'
                        #       % (current.get_id(), next.get_id(), next.get_distance()))
                    else:
                        print('not updated : current = %s next = %s new_dist = %f'
                              % (current.get_id(), next.get_id(), next.get_distance()))
            else:
                print(current.get_distance())
            # Rebuild heap
            # 1. Pop every item
            while len(unvisited_queue):
                heapq.heappop(unvisited_queue)
            # 2. Put all vertices not visited into the queue
            unvisited_queue = [(v.get_distance(), v.get_id(), v) for v in self.aGraph if not v.visited]
            heapq.heapify(unvisited_queue)

        return self.aGraph
