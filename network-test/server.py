#!/bin/python3
# -*- coding: utf-8 -*-

# modified from: https://github.com/amjadsde/Speed-Test

import socket, argparse, sys

has_raw_input=True
try:
    raw_input
except NameError:
    has_raw_input=False
if sys.version_info[0]==2 and has_raw_input:
    input=raw_input


# BUFSIZE = 1048576 # bytes # TODO transfer buffer size on the first message
BUFSIZE = 4096 # bytes
DEFAULT_PORT=None

def server(ip_address,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip_address, int(port)))
    s.listen(1)
    print ('Server ready on {}:{}...'.format(ip_address,port))
    while True:
        conn, (client_ip, remoteport) = s.accept()
        while True:
            data = conn.recv(BUFSIZE)
            if not data:
                break
            del data
        conn.close()
        print ('Done with', client_ip, 'on port', remoteport)

def get_args():
    parser = argparse.ArgumentParser(description='Arguments', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-a','--ip-address',required=False,action='store',default='0.0.0.0',help='The IP address to bind the server')
    parser.add_argument('-p','--port',required=False,action='store',default=DEFAULT_PORT,help='The port that the server will be listening to')
    args=parser.parse_args()
    return args

def main():
    args = get_args()
    if args.port is None:
        args.port=port = input("Port: ")
    server(args.ip_address,args.port)

if __name__ == "__main__":
    main()