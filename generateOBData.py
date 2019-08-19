#!/usr/bin/python

import sys, getopt
import numpy as np
from numpy import genfromtxt

def generateOB(argv):
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print('generateOBData.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('generateOBData.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg

    segments = genfromtxt(inputfile, delimiter=',')
    # print(segments)
    for x in range(segments.shape[0]):
        for y in range(segments.shape[1]):
            if segments[x,y] < 1:
                segments[x, y] = np.random.random_sample()

    np.savetxt(outputfile, segments, delimiter=",")


if __name__ == "__main__":
    generateOB(sys.argv[1:])
