from socket import *
import time
import threading
from threading import Lock

my_lock = Lock()


def message_rcv(seq_num, address):
    global minimumRTT, bottleneckQueueSize, queue, rcvSocket

    #seq_num = seq_num.decode()
    #tmp = seq_num.split('@', 1)
    #seq_num = tmp[0]
    #seq_num = str(seq_num)
    flag = False

    tmp = time.time()
    while True:
        if time.time() - tmp >= minimumRTT / 2.0:
            break

    with my_lock:
        if len(queue) < bottleneckQueueSize:        # queue has free space > ACK
            queue.append((int(seq_num), address))
        else:                                       # queue is full > NACK
            flag = True

    if flag:
        tmp = time.time()
        while True:
            if time.time() - tmp >= minimumRTT / 2.0:
                break
        rcvSocket.sendto(("NACK " + seq_num).encode(), address)


def dequeue():
    global bottleneckLinkRate, bottleneckQueueSize, queue, rcvSocket, base_time

    while True:
        if time.time() - base_time >= 1.0 / bottleneckLinkRate:
            base_time = time.time()

            with my_lock:
                if len(queue) > 0:
                    (seq_num, address) = queue[0]

                    del queue[0]
                    t_sendACK = threading.Thread(target=send_ack, args=(seq_num, address,))
                    t_sendACK.start()


def send_ack(seq_num, address):
    global minimumRTT, rcvSocket, ackCnt

    tmp = time.time()
    while True:
        if time.time() - tmp >= minimumRTT / 2.0:
            break

    with my_lock:
        ackCnt += 1
    #print(("ACK " + str(seq_num)).encode(), address)
    rcvSocket.sendto(("ACK " + str(seq_num)).encode(), address)


def time_interval():
    global time_base, ackCnt, queue, bottleneckQueueSize

    cnt = 0
    queue_occupancy = 0
    init_time = time_base

    while True:
        tmp = time.time()
        if tmp - time_base >= 0.1:
            with my_lock:
                queue_occupancy += len(queue)
            cnt += 1

            if cnt == 20:
                with my_lock:
                    print("time: {0:0.2f}".format(tmp - init_time))
                    print("   - Receiving rate: {0:0.2f} pps".format(ackCnt / 2.0))
                    #print("   - Average queue occupancy: {0:0.2f}%".format((queue_occupancy / 20.0) / bottleneckQueueSize * 100.0), end="\n\n")
                    # print("{0:0.2f}\t{1:0.2f}\t{2:0.2f}".format((tmp - init_time), (ackCnt / 2.0), \
                    #                                            (queue_occupancy / 20.0)))

                    ackCnt = 0

                cnt = 0
                queue_occupancy = 0

            time_base += 0.1
##################################################################

receiver = ('127.0.0.1', 12000)
minimumRTT = 0.01
bottleneckLinkRate = 100
bottleneckQueueSize = 100
#manually set

rcvSocket = socket(AF_INET, SOCK_DGRAM)
rcvSocket.bind(receiver)

t_dequeue = threading.Thread(target=dequeue, args=())
t_time = threading.Thread(target=time_interval, args=())

queue = []
ackCnt = 0
base_time = time.time()
time_base = base_time


##################################################################


import socket
from lt import decode
import sys
import zlib, pickle

address = ("127.0.0.1", 8080)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(address)



#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import math
import argparse
import numpy as np
import core
from encoder import encode
from decoder import decode


def blocks_write(blocks, file, filesize):
    """ Write the given blocks into a file
    """

    count = 0
    for data in recovered_blocks[:-1]:
        file_copy.write(data)
        count += len(data)

    # Convert back the bytearray to bytes and shrink back 
    last_bytes = bytes(recovered_blocks[-1])
    shrinked_data = last_bytes[:filesize % core.PACKET_SIZE]
    file_copy.write(shrinked_data)

#########################################################
    
if __name__ == "__main__":

        # HERE: Simulating the loss of packets?
    #header_data, client_address_header = server_socket.recvfrom(1111)  #receive header
    file_blocks_n = 153
    filesize = 10000000


    file_symbols = []
    i=0
    
    t_dequeue.start()
    t_time.start()
    #timer launched

    while True:

        receive_data, client_address = server_socket.recvfrom(8080)
        #print(receive_data)

        after_symbol = zlib.decompress(receive_data) 

        file_symbol_single = pickle.loads(after_symbol)
        file_symbol_single_noarray = file_symbol_single[1]
        #print(type(file_symbol_single_noarray))
        msg = str(file_symbol_single[0])
        t_receive = threading.Thread(target=message_rcv, args=(msg, client_address,))
        t_receive.start()
        
        file_symbols.append(file_symbol_single_noarray)
        i=i+1
        #print(len(file_symbols))
        if len(file_symbols)>300:
            break


    try:
        # Recovering the blocks from symbols
        recovered_blocks, recovered_n = decode(file_symbols, blocks_quantity=file_blocks_n)
    except:
        print("not enough symbols to decode")

    if core.VERBOSE:
        print(recovered_blocks)
        #print(type(recovered_blocks), "recv_block_type")
        print("------ Blocks :  \t-----------")
        #print(file_blocks)
        #print(type(file_blocks), "file_block_type")

    if recovered_n != file_blocks_n:
        print("All blocks are not recovered, we cannot proceed the file writing")
        exit()

    filename_copy = "copy"
    # Write down the recovered blocks in a copy 
    with open(filename_copy, "wb") as file_copy:
        blocks_write(recovered_blocks, file_copy, filesize)

    print("Wrote {} bytes in {}".format(os.path.getsize(filename_copy), filename_copy))
    os._exit(0)


