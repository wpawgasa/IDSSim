#!/usr/bin/python

import sys, getopt
import numpy as np
from numpy import genfromtxt
from dijkstra import Vertex, Graph, Dijkstra


def generateST(argv):
    tdfile = ''
    obfile = ''
    trespassers = 0
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv,"ha:b:o:n:",["tdfile=","obfile=","ofile=","number="])
    except getopt.GetoptError:
        print('generateSTData.py -a <tdfile> -b <obfile> -o <outputfile> -n <number>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('generateSTData.py -a <tdfile> -b <obfile> -o <outputfile> -n <number>')
            sys.exit()
        elif opt in ("-a", "--tdfile"):
            tdfile = arg
        elif opt in ("-b", "--obfile"):
            obfile = arg
        elif opt in ("-n", "--number"):
            trespassers = int(arg)
        elif opt in ("-o", "--ofile"):
            outputfile = arg

    tdsegments = genfromtxt(tdfile, delimiter=',')
    obsegments = genfromtxt(obfile, delimiter=',')
    stsegments = np.zeros((tdsegments.shape[0]+1,obsegments.shape[1]))
    # print(obsegments[:,0])
    # print(segments)
    # construct graph
    g = Graph()
    for x in range(tdsegments.shape[0]):
        for y in range(tdsegments.shape[1]):
            if tdsegments[x,y] < 1.0:
                g.add_vertex('a_('+str(x)+','+str(y)+')',x,y)

    vertice_keys = g.get_vertices()
    for key in vertice_keys:
        vertex = g.get_vertex(key)
        # print(vertex)
        v_i = vertex.get_i()
        v_j = vertex.get_j()
        if (v_i-1 >= 0 and v_j-1 >= 0) and tdsegments[v_i-1,v_j-1] < 1:
            next_vertex = g.get_vertex('a_('+str(v_i-1)+','+str(v_j-1)+')')
            cost = tdsegments[v_i-1,v_j-1] + (1 - obsegments[v_i-1,v_j-1])
            g.add_edge(vertex.get_id(),next_vertex.get_id(),cost)
        if v_i-1 >= 0 and tdsegments[v_i-1,v_j] < 1:
            next_vertex = g.get_vertex('a_(' + str(v_i - 1) + ',' + str(v_j) + ')')
            cost = tdsegments[v_i - 1, v_j] + (1 - obsegments[v_i - 1, v_j])
            g.add_edge(vertex.get_id(), next_vertex.get_id(), cost)
        if (v_i-1 >= 0 and v_j+1 <= tdsegments.shape[1]-1) and tdsegments[v_i-1,v_j+1] < 1:
            next_vertex = g.get_vertex('a_('+str(v_i-1)+','+str(v_j+1)+')')
            cost = tdsegments[v_i-1,v_j+1] + (1 - obsegments[v_i-1,v_j+1])
            g.add_edge(vertex.get_id(),next_vertex.get_id(),cost)
        if (v_j+1 <= tdsegments.shape[1]-1) and tdsegments[v_i,v_j+1] < 1:
            next_vertex = g.get_vertex('a_('+str(v_i)+','+str(v_j+1)+')')
            cost = tdsegments[v_i,v_j+1] + (1 - obsegments[v_i,v_j+1])
            g.add_edge(vertex.get_id(),next_vertex.get_id(),cost)
        if (v_i+1 <= tdsegments.shape[0]-1 and v_j+1 <= tdsegments.shape[1]-1) and tdsegments[v_i+1,v_j+1] < 1:
            next_vertex = g.get_vertex('a_('+str(v_i+1)+','+str(v_j+1)+')')
            cost = tdsegments[v_i+1,v_j+1] + (1 - obsegments[v_i+1,v_j+1])
            g.add_edge(vertex.get_id(),next_vertex.get_id(),cost)
        if (v_i+1 <= tdsegments.shape[0]-1) and tdsegments[v_i+1,v_j] < 1:
            next_vertex = g.get_vertex('a_('+str(v_i+1)+','+str(v_j)+')')
            cost = tdsegments[v_i+1,v_j] + (1 - obsegments[v_i+1,v_j])
            g.add_edge(vertex.get_id(),next_vertex.get_id(),cost)
        if (v_i+1 <= tdsegments.shape[0]-1 and v_j-1 >=0) and tdsegments[v_i+1,v_j-1] < 1:
            next_vertex = g.get_vertex('a_('+str(v_i+1)+','+str(v_j-1)+')')
            cost = tdsegments[v_i+1,v_j-1] + (1 - obsegments[v_i+1,v_j-1])
            g.add_edge(vertex.get_id(),next_vertex.get_id(),cost)
        if (v_j-1 >= 0) and tdsegments[v_i,v_j-1] < 1:
            next_vertex = g.get_vertex('a_('+str(v_i)+','+str(v_j-1)+')')
            cost = tdsegments[v_i,v_j-1] + (1 - obsegments[v_i,v_j-1])
            g.add_edge(vertex.get_id(),next_vertex.get_id(),cost)

    entries = np.where(tdsegments[:, 0] < 1)
    exits = np.where(tdsegments[:, tdsegments.shape[1]-1] < 1)

    # print(vertice_keys)
    # vertice_keys = g.get_vertices()
    # for key in vertice_keys:
    #     vertex = g.get_vertex(key)
    #     print(vertex)
    for v in g:
        for w in v.get_connections():
            vid = v.get_id()
            wid = w.get_id()
            print('( %s , %s, %f)' % (vid, wid, v.get_weight(w)))

    for x in range(trespassers):
        entry = np.random.choice(entries[0],1)
        exit = np.random.choice(exits[0],1)
        dijk = Dijkstra(g)
        print("Entry %s" % str(entry[0]))
        traversed_g = dijk.traversing('a_(' + str(entry[0]) + ',0)','a_(' + str(exit[0]) + ',' + str(tdsegments.shape[1] - 1) + ')')
        end_vertex = traversed_g.get_vertex('a_(' + str(exit[0]) + ',' + str(tdsegments.shape[1] - 1) + ')')
        print(end_vertex)
        path = [end_vertex]
        dijk.shortest(end_vertex,path)
        print("Shortest Path")
        for s in path[::-1]:
            print(s.get_id())
            stsegments[s.get_i()+1,s.get_j()] = stsegments[s.get_i()+1,s.get_j()]+1

    stsegments[0, :] = trespassers

    np.savetxt(outputfile, stsegments, delimiter=",")


if __name__ == "__main__":
    generateST(sys.argv[1:])
