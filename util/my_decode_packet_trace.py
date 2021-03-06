#!/usr/bin/env python

# Copyright (c) 2013-2014 ARM Limited
# All rights reserved
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Andreas Hansson

# This script is used to dump protobuf packet traces to ASCII
# format. It assumes that protoc has been executed and already
# generated the Python package for the packet messages. This can
# be done manually using:
# protoc --python_out=. --proto_path=src/proto src/proto/packet.proto
#
# The ASCII trace format uses one line per request on the format cmd,
# addr, size, tick,flags. For example:
# r,128,64,4000,0
# w,232123,64,500000,0

import protolib
import sys

# Import the packet proto definitions. If they are not found, attempt
# to generate them automatically. This assumes that the script is
# executed from the gem5 root.
try:
    import packet_pb2
except:
    print "Did not find packet proto definitions, attempting to generate"
    from subprocess import call
    error = call(['protoc', '--python_out=util', '--proto_path=src/proto',
                  'src/proto/packet.proto'])
    if not error:
        print "Generated packet proto definitions"

        try:
            import google.protobuf
        except:
            print "Please install Python protobuf module"
            exit(-1)

        import packet_pb2
    else:
        print "Failed to import packet proto definitions"
        exit(-1)

def main():
    if len(sys.argv) != 6:
        print "Usage: ", sys.argv[0], " <protobuf input> <ASCII output> <starting_tick> <ending_tick> <max_packets>"
        exit(-1)

    print "Command line arguments:", sys.argv

    # Open the file in read mode
    proto_in = protolib.openFileRd(sys.argv[1])

    try:
        ascii_out = open(sys.argv[2], 'w')
    except IOError:
        print "Failed to open ", sys.argv[2], " for writing"
        exit(-1)

    # Read the magic number in 4-byte Little Endian
    magic_number = proto_in.read(4)

    if magic_number != "gem5":
        print "Unrecognized file", sys.argv[1]
        exit(-1)

    print "Parsing packet header"

    # Add the packet header
    header = packet_pb2.PacketHeader()
    protolib.decodeMessage(proto_in, header)

    print "Object id:", header.obj_id
    print "Tick frequency:", header.tick_freq
    starting_tick = long(sys.argv[3])
    ending_tick = long(sys.argv[4])
    max_packets = long(sys.argv[5])

    print "Parsing packets from simulation tick: ", str(starting_tick), " to ", str(ending_tick), " max packets = ", max_packets

    num_packets = 0
    packet = packet_pb2.Packet()
    currtick = 0;

    # Decode the packet messages until we hit the end of the file
    while protolib.decodeMessage(proto_in, packet) and currtick < starting_tick:
        currtick = long(packet.tick)

    if currtick >= starting_tick and currtick < ending_tick:
        print "Found first packet of interest at tick ", str(currtick)
        
        while protolib.decodeMessage(proto_in, packet) and currtick < ending_tick and num_packets < max_packets:
            num_packets += 1
            currtick = long(packet.tick)

            # ReadReq is 1 and WriteReq is 4 in src/mem/packet.hh Command enum
            #cmd = 'r' if packet.cmd == 1 else ('w' if packet.cmd == 4 else 'u') # MWG commented out
            cmd = packet.cmd # MWG
            if packet.HasField('pkt_id'):
                ascii_out.write('%s,' % (packet.pkt_id))
            if packet.HasField('flags'):
                if packet.HasField('has_data'):
                    addr = long(packet.addr)
                    size = long(packet.size)
                    flags = long(packet.flags)

                    ascii_out.write('%s,%016X,%016X,%016X,%s,' % (cmd, addr, size, flags, packet.tick)) 
                    if packet.has_data == 1: 
                        ascii_out.write('1,')
                        ascii_out.write('%016X,%016X,%016X,%016X,%016X,%016X,%016X,%016X\n' % (packet.data0,
                                        packet.data1,
                                        packet.data2,
                                        packet.data3,
                                        packet.data4,
                                        packet.data5,
                                        packet.data6,
                                        packet.data7))
                    else: 
                        ascii_out.write('0,')
                        ascii_out.write('0,0,0,0,0,0,0,0\n')
                else: 
                    display("uh oh, this should not have happened")
                    exit(1)
            else:
                display("uh oh, this should not have happened")
                exit(1)
            if num_packets % 10000 == 0:
                print "Packet ", num_packets

        print "Found last packet of interest at tick ", str(currtick)
        print "Parsed packets:", num_packets

    else:
        print "No packets found in tick range of interest: [", starting_tick, ",", ending_tick, ")"
    
    # We're done
    ascii_out.close()
    proto_in.close()

if __name__ == "__main__":
    main()
