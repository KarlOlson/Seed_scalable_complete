from .Connection import Connection
from .FiveTuple import FiveTuple

from scapy.all import *


class ConnectionTracker:
    def __init__(self):
        # self.connections = set()
        self.connections = {}


    def add_connection(self, m_pkt):
        connection = Connection(m_pkt.packet())
        print("adding connection: ")
        print(connection)
        if connection:
            self.connections[connection.five_tuple] = connection
        else:
            print("Error failed to add connection: " + str(connection))

    def get_connection(self, connection):
        return self.connections[connection.five_tuple]

    def connection_exists(self, m_pkt):
        print("does connection exist??")
        five_tuple = FiveTuple.from_pkt(m_pkt.packet())
        return five_tuple in self.connections

    def update_connection(self, m_pkt):
        five_tuple = FiveTuple.from_pkt(m_pkt.packet())
        connection = self.connections[five_tuple] # get the connection associated with the 5-tuple
        connection.packet_update(m_pkt)
        # if connection.is_modified():
        #     print("connection modified. need to update packet seq numbers")
        #     self.update_seq_numbers(m_pkt)
        self.connections[five_tuple] = connection

    # def update_seq_numbers(self, m_pkt):



    def drop_packet(self, pkt):
        ret = self.connection_exists(pkt)
        if ret:
            self.drop_packet_in_active_connection(pkt)
        elif ret == False:
            self.drop_packet_in_new_connection(pkt)
        else:
            print("ERROR. dropping packet in unknown state")

    def drop_packet_in_active_connection(self, pkt):
        print("dropping packet in active connection")


    def drop_packet_in_new_connection(self, pkt):
        print("dropping packet in new connection")


