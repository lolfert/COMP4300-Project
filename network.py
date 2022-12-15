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
from node import *

class Network:

	def __init__(
		self,
		node_count = 5,
		request_frequency = 0.1,
		):

		self.event_queue = PriorityQueue()

		self.nodes = {}
		self.links = {}
		self.message_queue = {}
		self.nodes_created = 0

		self.add_node(Node(location = (3, 2)))
		self.add_node(Node(location = (2, 4)))
		self.add_node(Node(location = (3, 8)))
		self.add_node(Node(location = (4, 6)))
		self.add_node(Node(location = (6, 5)))
		# self.add_node(Node(location = (6, 3)))
		# self.add_node(Node(location = (7, 7)))
		# self.add_node(Node(location = (9, 5)))
	
	def add_node(self, node):

		# Obtain new ID for node
		node.id = self.nodes_created
		self.nodes_created += 1

		# Add node to node list
		self.nodes[node.id] = node

		# Add links with existing nodes
		for other_id, other in self.nodes.items():

			if(node.id != other_id):

				self.links[frozenset([node.id, other_id])] = Link(node, other)
	
	def update_all_nodes(self, time):

		# Process received messages for each node

		for node_id in self.nodes:

			self.update_node(time, node_id)

	def update_node(self, time, node_id):

		# Process received messages for each node

		node = self.nodes[node_id]

		if(self.message_queue.get(node_id) == None):

			self.message_queue[node_id] = []

		node_update = node.update(time)

		self.message_queue[node_id] += node_update.outgoing_messages
		
		# Transmit any resulting messages

		messages = self.message_queue[node_id]

		while len(messages) > 0:

			message = messages.pop()

			event = TransmissionEvent(time = time + 1, sender_id = node_id, recipient_ids = message.recipient_ids, message = message)

			self.add_event(event)

		for neighbor_id in node_update.neighbors_added:

			self.add_event(ConnectionEvent(time = time + 1, node_id = node_id, peer_id = neighbor_id))

		for neighbor_id in node_update.neighbors_lost:

			self.add_event(ConnectionLostEvent(time = time + 1, node_id = node_id, peer_id = neighbor_id))

	def add_event(self, event):
		self.event_queue.put(event)

	def execute(self, max_time_steps):

		all_events = []

		self.update_all_nodes(time = 0)

		while not self.event_queue.empty():


			event = self.event_queue.get()

			all_events.append(event)

			# When the time changes, update the node states

			current_event_time = event.time

			if event.time > max_time_steps:
				break

			if(event.log):
				print(event)

			# Transmission Event Handling

			if isinstance(event, TransmissionEvent):

				transmission = event
				sender = self.nodes[transmission.sender_id]

				# If no recipients were specified, broadcast the message to all nodes

				recipient_ids = transmission.recipient_ids if len(transmission.recipient_ids) > 0 else self.nodes.keys()

				# For each recipient, create a Reception event if the transmission is successful or a Packet Loss event if not

				for recipient_id in recipient_ids:

					if (recipient_id != sender.id):

						recipient = self.nodes[recipient_id]

						link = self.links[frozenset([recipient.id, sender.id])]

						# Check if nodes are within the required distance range for transmission

						if(link.test_distance()):

							# Check if the transmission should be considered successful

							if(link.test_successful_transmission()):

								self.add_event(
									ReceptionEvent(
										time = event.time + 1,
										sender_id = transmission.sender_id,
										recipient_id = recipient.id,
										message = transmission.message
										)
									)

							else:

								self.add_event(PacketLossEvent(event.time + 1, sender.id, recipient.id, transmission.message))

						else:

							print(f'Nodes {link.node_A} and {link.node_B} are not within range.')

			# Reception Handling

			if isinstance(event, ReceptionEvent):

				message = event.message
				recipient = self.nodes[event.recipient_id]
				recipient.receive(message)

			# if isinstance(event, ConnectionEvent):

			self.update_all_nodes(event.time)

			print('\n\n')
			for node in self.nodes.values():
				print(node)
			print('\n\n')

			# sleep(0.5)
		
		return all_events