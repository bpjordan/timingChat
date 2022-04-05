#!/usr/bin/env python

import socket, sys
from time import sleep
from random import randint

debug = 0


# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.bind(("", port))

#     s.listen(0)

#     try:
#         while True:
#             print("Server listening...")
#             c, addr = s.accept()

#             with c:
#                 print(f"Connected to {addr}")

#                 msg = "Some message ...\n"

#                 # overt message
#                 for i in msg:
#                     c.send(i.encode())
#                     sleep(0.025)

#                 c.send("EOF".encode())
#                 print("Message sent...")
#     except KeyboardInterrupt:
#         print("Closing socket")

def covertSendMsg(c: socket.socket, msg: str, coverFile, delim: float, one: float):
    try:
        overtMsg = coverFile.readline().strip('\n') + ' '
    except EOFError:
        print("Ran out of text in cover file")

    if delim is None:
        binaryStr = ''.join(format(ord(l), '07b') for l in msg) + '0000000'
    else:
        binaryStr = ' ' + ' '.join(format(ord(l), '07b') for l in msg) + ' 0000000'


    if debug > 1:
        print(f"{binaryStr=}")

    runs = randint(1,3)

    overtDex = 0
    for i in range(runs):
        msgDex = 0
        for bit in binaryStr:
            if overtDex+1 >= len(overtMsg):
                try:
                    overtMsg = coverFile.readline().strip('\n') + ' '
                except EOFError:
                    print("Could not finish message, Ran out of text in cover file", file=sys.stderr)
                    c.send("EOF".encode())
                    return
                overtDex = 0

            c.send(overtMsg[overtDex].encode())
            if delim is not None and bit == ' ':
                sleep(delim)
            elif bit == '1':
                sleep(one)
            else:
                sleep(0.025)
            overtDex += 1
    c.send("EOF".encode())

def runServer(port: int, coverFile: str, delim: int, one: int, msg=None):
    with open(coverFile, "r") as f:

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", port))

            s.listen(0)

            while True:
                try:
                    print("Awaiting Connections...")
                    c, addr = s.accept()
                    print(f"Connected to host {addr[0]}:{addr[1]}")

                    with c:
                        if msg is None:
                            while True:
                                try:
                                    msg = input("> ")
                                except EOFError:
                                    print('\rConnection closed')
                                    break
                                covertSendMsg(c, msg, f, delim, one)
                        else:
                            covertSendMsg(c, msg, f, delim, one)
                except KeyboardInterrupt:
                    print("\rGoodbye")
                    break
                except (BrokenPipeError, TimeoutError, socket.timeout, ConnectionResetError) as e:
                    print(f'\rLost connection to client ({e})')



def main():
    import getopt

    port = 1337
    coverFile = "const.txt"
    timingProfiles = {"fast": (0.2,0.05),\
                      "balanced": (0.3,0.1),\
                      "reliable": (0.5, 0.2)}
    delim, one = timingProfiles["balanced"]
    useDelim = False
    message = None

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "hp:c:t:dm:v", ["help", "port=", "coverFile=", "timing=", "delimitBytes", "message="])
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
        elif opt in ['-m', '--message']:
            message = arg
        elif opt == '-v':
            global debug
            debug += 1

    runServer(port, coverFile, delim if useDelim else None, one, message)


if __name__ == '__main__':
    for i in range(5):
        try:
            main()
            break
        except OSError as e:
            if e.errno == 98:
                print(f"Port in use, trying again ({e})")
                sleep(3)
            else:
                raise e
