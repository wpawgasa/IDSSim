#!/usr/bin/python

import sys, getopt
import numpy as np

def generateTD(argv):
    rows = 0
    cols = 0
    paths = 0
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv,"hr:c:p:m:o:",["rows=","cols=","paths=","method=","ofile="])
    except getopt.GetoptError:
        print('generateTDData.py -r <rows> -c <cols> -p <paths> -m <method> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('generateTDData.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-r", "--rows"):
            rows = int(arg)
        elif opt in ("-c", "--cols"):
            cols = int(arg)
        elif opt in ("-p", "--paths"):
            paths = int(arg)
        elif opt in ("-m", "--method"):
            method = int(arg)
        elif opt in ("-o", "--ofile"):
            outputfile = arg

    if method == 1:
        randomGenerate(rows,cols,paths,outputfile)
    else:
        simpleGenerate(rows,cols,paths,outputfile)


def randomGenerate(rows,cols,paths,outputfile):
    segments = np.ones((rows,cols))
    print('Region dimension (%i,%i)' % (segments.shape[0], segments.shape[1]))
    ridx = np.arange(rows)
    cidx = np.arange(cols)
    for p in range(paths):
        # print(p)
        entry_ridx = np.random.randint(0,rows-1,1)
        print(entry_ridx)
        cur_ridx = entry_ridx
        cur_cidx = 0
        prev_ridx = entry_ridx
        prev_cidx = 0
        segments[entry_ridx, 0] = np.random.random_sample()
        while cur_cidx < cols-1:
            if cur_ridx == 0 and cur_cidx == 0:
                r_choices = [0,1]
                c_choices = [0,1]
                r_choice = np.random.choice(r_choices,1,p=[0.5,0.5])
                c_choice = np.random.choice(c_choices,1,p=[0.2,0.8])
            elif cur_ridx == 0 and cur_cidx>0:
                r_choices = [0,1]
                c_choices = [-1,0,1]
                r_choice = np.random.choice(r_choices,1,p=[0.5,0.5])
                c_choice = np.random.choice(c_choices,1,p=[0.1,0.1,0.8])
            elif cur_ridx == rows-1 and (cols - 1 > cur_cidx > 0):
                r_choices = [0,-1]
                c_choices = [-1,0,1]
                r_choice = np.random.choice(r_choices,1,p=[0.5,0.5])
                c_choice = np.random.choice(c_choices,1,p=[0.1,0.1,0.8])
            elif cur_ridx == rows-1 and cur_cidx==0:
                r_choices = [0,-1]
                c_choices = [0,1]
                r_choice = np.random.choice(r_choices,1,p=[0.5,0.5])
                c_choice = np.random.choice(c_choices,1,p=[0.2,0.8])
            elif (rows - 1 > cur_ridx > 0) and cur_cidx==0:
                r_choices = [-1, 0,1]
                c_choices = [0,1]
                r_choice = np.random.choice(r_choices,1,p=[0.3,0.4,0.3])
                c_choice = np.random.choice(c_choices,1,p=[0.2,0.8])
            else:
                r_choices = [-1, 0, 1]
                c_choices = [-1, 0, 1]
                r_choice = np.random.choice(r_choices, 1, p=[0.3, 0.4, 0.3])
                c_choice = np.random.choice(c_choices, 1, p=[0.1, 0.1, 0.8])

            if ((cur_ridx + r_choice is not cur_ridx) or (cur_cidx + c_choice is not cur_cidx)) and (
                    (cur_ridx + r_choice is not prev_ridx) or (cur_cidx + c_choice is not prev_cidx)):
                prev_ridx = cur_ridx
                prev_cidx = cur_cidx
                cur_ridx = cur_ridx + r_choice
                cur_cidx = cur_cidx + c_choice
                if segments[cur_ridx, cur_cidx] == 1:
                    segments[cur_ridx, cur_cidx] = np.random.random_sample()

    for vp in np.linspace(5,cols-5,num=int(cols/5)-1):
        cur_c = int(vp)
        for r in range(rows):
            c = cur_c + np.random.randint(-1, 1, 1)
            while c < 0 or c > cols-1:
                c = cur_c + np.random.randint(-1, 1, 1)
            # print(c)
            cur_c = c
            if segments[r, c] == 1:
                segments[r, c] = np.random.random_sample()

    print(segments)
    np.savetxt(outputfile,segments,delimiter=",")


def simpleGenerate(rows,cols,paths,outputfile):
    segments = np.ones((rows,cols))
    print('Region dimension (%i,%i)' % (segments.shape[0], segments.shape[1]))
    ridx = np.arange(rows)
    cidx = np.arange(cols)
    for p in np.linspace(np.round(rows/paths),rows-np.round(rows/paths),num=paths-1):
        # print(p)
        entry_ridx = int(p)
        print(entry_ridx)
        cur_ridx = entry_ridx
        cur_cidx = 0
        prev_ridx = entry_ridx
        prev_cidx = 0
        segments[entry_ridx, 0] = np.random.random_sample()
        while cur_cidx < cols-1:
            cur_ridx = cur_ridx
            cur_cidx = cur_cidx + 1
            if segments[cur_ridx, cur_cidx] == 1:
                segments[cur_ridx, cur_cidx] = np.random.random_sample()

    for vp in np.linspace(5,cols-5,num=int(cols/5)-1):
        cur_c = int(vp)
        for r in range(rows):
            c = cur_c
            if segments[r, c] == 1:
                segments[r, c] = np.random.random_sample()

    print(segments)
    np.savetxt(outputfile,segments,delimiter=",")



if __name__ == "__main__":
    generateTD(sys.argv[1:])
