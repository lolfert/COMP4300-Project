from abc import ABC, abstractmethod
from queue import PriorityQueue
from typing import List
from dataclasses import dataclass
from math import sqrt
from random import random
from numpy import clip
from time import sleep

from messages import *
from events import *

HELLO_INTERVAL = 1
CONNECTION_TIMEOUT = 4

ROUTE_DISCOVERY_TIMEOUT = 1
ROUTE_EXPIRATION_PERIOD = 3
REVERSE_ROUTE_EXPIRATION_PERIOD = 3
MAXIMUM_RETRANSMISSIONS = 10
ACTIVE_TIMEOUT_PERIOD = 1

TRANSMISSION_DISTANCE_LOW = 3
TRANSMISSION_DISTANCE_HIGH = 4

class Node:

	def __init__(self, location):

		self.id = -1
		self.location = location

		self.neighbors = {}
		self.routing_table = {}

		self.request_id = 0			# Incremented whenever a new RREQ is created by a node.
		self.sequence_number = 0

		self.last_hello = None
		self.handlers = [
			HelloHandler(self),
			RequestHandler(self),
			ResponseHandler(self),
			ErrorHandler(self)
		]

		self.messages_in = []
		self.messages_out = []

	def send(self, message):
		self.messages_out.append(message)
	
	def receive(self, message):
		self.messages_in.append(message)

	def update(self, time):
		
		# Maintain peer connections

		outgoing_messages, neighbors_added, neighbors_lost = self.update_neighbor_records(time)	

		# Handle any received messages

		while len(self.messages_in) > 0:
			message = self.messages_in.pop()
			for handler in self.handlers:
				results = handler.handle(time, message)
				if (results != None):
					outgoing_messages.append(results)
		
		return NodeUpdate(outgoing_messages = outgoing_messages, neighbors_added = neighbors_added, neighbors_lost = neighbors_lost)
	
	def update_neighbor_records(self, time):

		outgoing_messages = []
		neighbors_added = []
		neighbors_lost = []

		for message in self.messages_in:

			sender_record = self.neighbors.get(message.sender_id)

			if(sender_record == None):

				neighbors_added.append(message.sender_id)
				sender_record = NeighborRecord(node_id = message.sender_id, last_seen = time, last_hello = -1)
				self.neighbors[message.sender_id] = sender_record

		# Remove neighbors whose connections have timed-out

		for nid, nr in self.neighbors.items():

			if time > nr.last_seen + CONNECTION_TIMEOUT:
				
				neighbors_lost.append(nid)
		
		for nid in neighbors_lost:

				self.neighbors.pop(nid)

		hello_message = HELLO(sender_id = self.id)
		shouldSendHello = False

		# Broadcast Hello message if there are no active neighbors connections

		if len(self.neighbors) == 0 and (self.last_hello == None or time > self.last_hello + HELLO_INTERVAL):

			shouldSendHello = True
			hello_message.recipient_ids = []

		# Multicast Hello message to any neighbors that have not been seen or contacted recently

		else: 

			for (nid, nr) in self.neighbors.items():

				if(time > max(nr.last_hello, nr.last_seen) + HELLO_INTERVAL):

					shouldSendHello = True
					hello_message.recipient_ids.append(nid)
					nr.last_hello = time

		if shouldSendHello:

			outgoing_messages.append(hello_message)
			self.last_hello = time
		
		return (outgoing_messages, neighbors_added, neighbors_lost)
	
	def __str__(self):
		return f'Node #{self.id}: [ location: {self.location}, neighbors: {[nid for nid in self.neighbors]}, last_hello: {self.last_hello} ]'

@dataclass
class Link:

	node_A: Node
	node_B: Node

	def test_distance(self):
		return self.get_length() <= TRANSMISSION_DISTANCE_HIGH

	def test_successful_transmission(self):
		"""
		This method returns a boolean indicating whether a transmission over the link should succeed.
		The outcome is probabilistic and based on a strength assigned to the link.
		The measure of strength here only considers distance and ranges from [0, 1] according to where distance lies relative to the interval [TRANSMISSION_DISTANCE_LOW, TRANSMISSION_DISTANCE_HIGH].
		"""
		distance = self.get_length()
		strength = 1 - (clip(distance, TRANSMISSION_DISTANCE_LOW, TRANSMISSION_DISTANCE_HIGH) - TRANSMISSION_DISTANCE_LOW) / (TRANSMISSION_DISTANCE_HIGH - TRANSMISSION_DISTANCE_LOW)
		success = random() < strength
		# print(f'[LINK TEST | {self.node_A.id} <-> {self.node_B.id}] P_A: {loc_A}, P_B: {loc_B}, D: {distance}, S: {strength}, Outcome: {success}')
		return success

	def get_length(self):
		loc_A = self.node_A.location
		loc_B = self.node_B.location
		return sqrt((loc_A[0] - loc_B[0]) ** 2 + (loc_A[1] - loc_B[1]) ** 2)

class MessageHandler(ABC):

	def __init__(self, node):
		self.node = node

	def handle(self, time, message):
		if(self.does_apply(message)):
			self.apply(time, message)

	@abstractmethod
	def does_apply(self, message):
		# Returns true if handler is applicable to message
		pass

	@abstractmethod
	def apply(self, time, message):
		pass

class HelloHandler(MessageHandler):

	def does_apply(self, message):
		return isinstance(message, HELLO)

	def apply(self, time, message):
		neighbor_record = self.node.neighbors.get(message.sender_id)
		if(neighbor_record == None):
			neighbor_record = NeighborRecord(node_id = message.sender_id, last_seen = time, last_hello = time)

class RequestHandler(MessageHandler):

	def does_apply(self, message):

		return isinstance(message, RREQ)

	def apply(self, message):

		self.node.routing_table[message.originator_id] = update_route_to_originator(message)

		# By default, forward the request to all other neighbors

		request_id = message.request_id,
		recipient_ids = [node for node in self.node.neighbors if node != message.sender_id]
		destination_id = message.destination_id,
		destination_sequence_number = message.destination_sequence_number,
		originator_id = message.originator_id,
		originator_sequence_number = message.originator_id,
		hop_count = message.hop_count + 1
		
		# If this node is the requested destination node, unicast a response to the sender

		if(self.id == message.destination_id):

			destination_sequence_number += 1
			recipient_ids = [message.sender_id]

			reply = RREP(
				request_id = message.request_id,
				recipient_ids = recipient_ids,
				destination_id = message.destination_id,
				destination_sequence_number = dsn,
				originator_id = message.originator_id,
				originator_sequence_number = message.originator_id,
				hop_count = message.hop_count + 1
			)

			# TODO: Add next_hop to originator to route table

		else:

			# Otherwise, if a cached route exists for the destination, and is up-to-date, forward the request along the route

			if(destination_table_entry != None and destination_table_entry.sequence_number >= message.destination_sequence_number):
				destination_sequence_number = destination_table_entry.destination_sequence_number
				recipient_ids = [destination_table_entry.next_hop]

			reply = RREQ(
				request_id = message.request_id,
				recipient_ids = recipient_ids,
				destination_id = message.destination_id,
				destination_sequence_number = dsn,
				originator_id = message.originator_id,
				originator_sequence_number = message.originator_id,
				hop_count = message.hop_count + 1
			)

		return reply

	def update_route_to_originator(self, message):

		to_originator_route = self.node.routing_table.get(message.originator_id)

		shouldReplaceBackwardsRoute = any(
			to_originator_route == None,
			message.originator_sequence_number > to_originator_route.sequence_number,
			message.hop_count < to_originator_route.hop_count
		)

		if(shouldReplaceBackwardsRoute):

			to_originator_route =  Route(
				destination_id = message.originator.id,
				destination_sequence_number = message.originator_sequence_number,
				valid_sequence_number = True,
				hop_count = message.hop_count + 1,
				next_hop = message.sender_id
			)

		return to_originator_route


class ResponseHandler(MessageHandler):

	def does_apply(self, message):

		return isinstance(message, RREP)

	def apply(self, message):

		destination_table_entry = self.node.routing_table.get(message.destination.id)

		if(message.destination_id == self.node.id):

			reply = RREP()

		if(destination_table_entry == None):

			destination_table_entry = Route(
				destination_id = message.destination_id,
				destination_sequence_number = message.destination_sequence_number,
				valid_sequence_number = True,
				hop_count = message.hop_count + 1,
				originator_id = message.originator_id,
				originator_sequence_number = message.originator_sequence_number
			)

			self.node.routing_table[message.destination_id] = destination_table_entry

		else:

			if(destination_table_entry.destination_sequence_number <= message.destination_sequence_number):

				destination_table_entry.destination_sequence_number = message.destination_sequence_number

	def update_route_to_destination(self, message):

		to_destination_route = self.node.routing_table.get(message.destination_id)

		shouldReplaceForwardsRoute = any(
			to_destination_route == None,
			message.destination_sequence_number > to_destination_route.sequence_number,
			message.hop_count < to_destination_route.hop_count
		)

		if(shouldReplaceForwardsRoute):

			to_destination_route =  Route(
				destination_id = message.destination_id,
				destination_sequence_number = message.destination_sequence_number,
				valid_sequence_number = True,
				hop_count = message.hop_count + 1,
				next_hop = message.sender_id
			)

		return to_destination_route



class ErrorHandler(MessageHandler):

	def does_apply(self, message):
		return isinstance(message, RERR)

	def apply(self, message):
		pass

@dataclass
class NodeUpdate:
	outgoing_messages: List[Message]
	neighbors_added: List[int]
	neighbors_lost: List[int]

@dataclass
class NeighborRecord:
	node_id: int
	last_seen: int
	last_hello: int

@dataclass
class Route:
	
	destination_id: int
	destination_sequence_number: int
	valid_sequence_number: bool
	hop_count: int
	next_hop: int
	precursors: List[int]
	lifetime: int