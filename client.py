from socket import *
import time
import threading
import sys
from threading import Lock
import os
my_lock = Lock()

def time_interval():
    global sendingRate, averageRTT, nackFlag, ackCnt, base_time

    init_time = base_time

    while True:
        tmp = time.time()
        if tmp - base_time >= 2:
            with my_lock:
                print("time: {0:0.2f}".format(tmp - init_time))
                print("   - Average RTT: {0:0.2f} sec".format(averageRTT))
                print("   - Sending Rate: {0:0.2f} pps".format(sendingRate))

                base_time = base_time + 2.0 # update base time (to count 2 sec)
                nackFlag = True
                ackCnt = 0


def listener():
    global sendingRate, sendingInterval, averageRTT, pktSndTime, nackFlag, ackCnt
    #print("flag1")
    while True:
        #print("flag2")
        msg, rcv_address = sndSocket.recvfrom(2048)
        tmp = time.time()
        msg = msg.decode().split(' ')   # msg[0]: ACK/NACK, msg[1]: seq#
        #print(msg,"msgmsgmsgmsgmsgmsg")
        with my_lock:
            if msg[0] == "NACK":
                if nackFlag:    # first NACK in 2 sec window
                    nackFlag = False
                    sendingRate /= 2.0
                    sendingInterval = 1.0 / sendingRate

            else:   # msg[0] == "ACK"
                ackCnt += 1
                sendingRate = sendingRate + 1.0 / sendingRate
                sendingInterval = 1.0 / sendingRate

                # update average RTT
                if averageRTT == 0:
                    averageRTT = (tmp - pktSndTime[int(msg[1])])
                else:
                    averageRTT = 0.875 * averageRTT + 0.125 * (tmp - pktSndTime[int(msg[1])])

        del pktSndTime[int(msg[1])]
#########################################################

from sys import stdin, stdout
from lt import decode
from lt import encode
import socket
from core import *
import pickle
import zlib
import json
#data = 'some input string' * 500

#client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#client_socket.bind(('127.0.0.1', 0))
server_address = ("127.0.0.1", 8080)

#client_socket.sendto(data.encode('utf-8'), server_address)


#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import math
import argparse
import numpy as np
import core
from encoder import encode
from decoder import decode

def blocks_read(file, filesize):
    """ Read the given file by blocks of `core.PACKET_SIZE` and use np.frombuffer() improvement.

    Byt default, we store each octet into a np.uint8 array space, but it is also possible
    to store up to 8 octets together in a np.uint64 array space.  
    
    This process is not saving memory but it helps reduce dimensionnality, especially for the 
    XOR operation in the encoding. Example:
    * np.frombuffer(b'\x01\x02', dtype=np.uint8) => array([1, 2], dtype=uint8)
    * np.frombuffer(b'\x01\x02', dtype=np.uint16) => array([513], dtype=uint16)
    """

    blocks_n = math.ceil(filesize / core.PACKET_SIZE)
    blocks = []

    # Read data by blocks of size core.PACKET_SIZE
    for i in range(blocks_n):
            
        data = bytearray(file.read(core.PACKET_SIZE))

        if not data:
            raise "stop"

        # The last read bytes needs a right padding to be XORed in the future
        if len(data) != core.PACKET_SIZE:
            data = data + bytearray(core.PACKET_SIZE - len(data))
            assert i == blocks_n-1, "Packet #{} has a not handled size of {} bytes".format(i, len(blocks[i]))

        # Paquets are condensed in the right array type
        blocks.append(np.frombuffer(data, dtype=core.NUMPY_TYPE))
    print(type(blocks))
    return blocks


#########################################################
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Robust implementation of LT Codes encoding/decoding process.")
    parser.add_argument("filename", help="file path of the file to split in blocks")
    parser.add_argument("-r", "--redundancy", help="the wanted redundancy.", default=2.0, type=float)
    parser.add_argument("--systematic", help="ensure that the k first drops are exactaly the k first blocks (systematic LT Codes)", action="store_true")
    parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("--x86", help="avoid using np.uint64 for x86-32bits systems", action="store_true")
    args = parser.parse_args()

    core.NUMPY_TYPE = np.uint32 if args.x86 else core.NUMPY_TYPE
    core.SYSTEMATIC = True if args.systematic else core.SYSTEMATIC 
    core.VERBOSE = True if args.verbose else core.VERBOSE    

    with open(args.filename, "rb") as file:

        print("Redundancy: {}".format(args.redundancy))
        print("Systematic: {}".format(core.SYSTEMATIC))

        filesize = os.path.getsize(args.filename)
        print("Filesize: {} bytes".format(filesize))

        # Splitting the file in blocks & compute drops
        file_blocks = blocks_read(file, filesize)
        file_blocks_n = len(file_blocks)
        drops_quantity = int(file_blocks_n * args.redundancy)

        print("Blocks: {}".format(file_blocks_n))
        print("Drops: {}\n".format(drops_quantity))

        # Generating symbols (or drops) from the blocks
        file_symbols = []
        
        #______________________network strat_____________________________
        receiver = ('127.0.0.1', 12000)
        #sendingRate = eval(input("Enter initial sending rate (pps): "))
        sendingRate = 100        #set the sending rate manually 

        sendingInterval = 1.0 / sendingRate
        seqNum = 0
        averageRTT = 0
        nackFlag = True
        ackCnt = 0
        pktSndTime = {}

        sndSocket = socket.socket(AF_INET, SOCK_DGRAM)
        sndSocket.bind(('127.0.0.1', 0))

        t_listener = threading.Thread(target=listener, args=())
        t_time = threading.Thread(target=time_interval, args=())

        snd_time = 0
        base_time = time.time()

        t_listener.start()
        t_time.start()
        
        #_________________________network closed__________________________
        
        #encoding sendto
        print("File_blocks above, symbols down")
        for curr_symbol in encode(file_blocks, drops_quantity=drops_quantity):

            tmp = time.time()
            with my_lock:
                if tmp - snd_time >= sendingInterval:
                    sendMsg = str(seqNum)
                    while sys.getsizeof(sendMsg) < 1000:
                        sendMsg += "@"
                    before_symbol = pickle.dumps([seqNum, curr_symbol])
                    com_bytes = zlib.compress(before_symbol)
                    sndSocket.sendto(com_bytes, server_address)
                    #print(sndSocket.getsockname())

                    pktSndTime[seqNum] = tmp

                    seqNum += 1
                    snd_time = tmp

                #before_symbol = pickle.dumps([seqNum, curr_symbol])
                #com_bytes = zlib.compress(before_symbol)  # 编码为UTF-8格式的字节进行压缩
                #client_socket.sendto(com_bytes, server_address)
        os._exit(0)
