#!/usr/bin/env python

import socket, sys
from time import perf_counter
from statistics import mode

DEBUG = 0

def interpretBinary(binStr: str, hasSpaces: bool = False):
    passes = ['']

    currPass = 0

    if ' ' in binStr:
        words = binStr.split(' ')
    else:
        words = [binStr[i:i+7] for i in range(0, len(binStr), 7)]

    if DEBUG > 1:
        print("Binary words recieved: " + str(words))

    for word in words:
        if word == '':
            continue
        char = chr(int(word, 2))

        if char.isprintable():
            passes[currPass] += char
        elif char == '\000': #Null byte means we hit the end of a pass
            passes.append('')
            currPass += 1
        else:
            passes[currPass] += '\000'

    if len(passes) == 1:
        return passes[0]

    if DEBUG > 0:
        print("\nPasses recieved:")
        print("\n".join(p.replace('\000', '*') for p in passes))

    finalStr = ''

    for i in range(max(len(p) for p in passes)):
        poss = []
        for p in passes:
            if i < len(p) and p[i] != '\000':
                poss.append(p[i])

        if len(poss) == 0:
            finalStr += '*'
        else:
            finalStr += mode(poss)

    return finalStr

def runClient(ip, port, allowDelimiters, delim, one):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        s.connect((ip, port))

        data = s.recv(4096).decode()
        while data != "":
            if DEBUG > 0:
                print("\nRecieving cover text:")

            covert_bin = ""

            while(data.rstrip("\n")) not in ["EOF", ""]:
                if DEBUG > 0:
                    sys.stdout.write(data)
                    sys.stdout.flush()

                t0 = perf_counter()
                data = s.recv(4096).decode()
                t1 = perf_counter()

                delta = round(t1 - t0, 3)

                if DEBUG > 2:
                    sys.stdout.write(f" {delta}\n")
                    sys.stdout.flush()

                if allowDelimiters and delta >= delim:
                    covert_bin += " "
                elif delta >= one:
                    covert_bin += "1"
                else:
                    covert_bin += "0"

                if data == "":
                    print("Connection closed unexpectedly", file=sys.stderr)
                    break

            if DEBUG > 0:
                print()
            print(interpretBinary(covert_bin))
            data = s.recv(4096).decode()
    if DEBUG > 0:
        print("Connection to server closed")


def main():
    import getopt

    ip = "127.0.0.1"
    port = 1337
    allowDelimiters = False

    timingProfiles = {"fast": (0.2,0.05),\
                      "balanced": (0.3,0.1),\
                      "reliable": (0.5, 0.2)}
    delim, one = timingProfiles["balanced"]

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "hH:p:c:t:dm:v", ["help", "host=", "port=", "coverFile=", "timing=", "acceptDelimiters"])
    except getopt.GetoptError as msg:
        print(msg, file=sys.stderr)
        print(usageString, file=sys.stderr)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ['-h', '--help']:
            print(usageString)
            sys.exit()
        elif opt in ['-p', '--port']:
            port = int(arg)
        elif opt in ['-c', '--coverFile']:
            coverFile = arg
        elif opt in ['-t', '--timing']:
            try:
                delim, one = timingProfiles[arg.lower()]
            except KeyError:
                print("Timing profile not recognized. Valid options are fast, balanced, or reliable", file=sys.stderr)
                print(usageString, file=sys.stderr)
                sys.exit(2)
        elif opt in ['-d', '--delimitBytes']:
            useDelim = True
        elif opt in ['-H', '--host']:
            ip = arg
        elif opt == '-v':
            global debug
            debug += 1

    runClient(ip, port, allowDelimiters, delim, one)

if __name__ == '__main__':
    main()
