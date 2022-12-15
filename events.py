from dataclasses import dataclass, field
from messages import Message
from typing import List

@dataclass
class Event:

	time: int

	def __eq__(self, other):
		return self.time == other.time

	def __lt__(self, other):
		return self.time < other.time

	def __gt__(self, other):
		return self.time > other.time

@dataclass
class ConnectionEvent(Event):

	node_id: int
	peer_id: int
	log: bool = True
	event_type: str = "Connection"

	def __str__(self):
		return f'(T = {self.time}) - [New Connection] - Node {self.node_id} established connection with node {self.peer_id}.'

@dataclass
class ConnectionLostEvent(Event):

	node_id: int
	peer_id: int
	log: bool = True
	event_type: str = "ConnectionLost"

	def __str__(self):
		return f'(T = {self.time}) - [Connection Lost] - Node {self.node_id} lost connection with node {self.peer_id}.'

@dataclass
class TransmissionEvent(Event):

	sender_id: int
	recipient_ids: List[int]
	message: Message
	log: bool = True
	event_type: str = "Transmission"

	def __str__(self):
		return f'(T = {self.time}) - [Transmission Event | {self.sender_id} )-> {self.recipient_ids if len(self.recipient_ids) > 0 else "ALL"} ] ---> Message: {self.message}'

@dataclass
class ReceptionEvent(Event):

	sender_id: int
	recipient_id: int
	message: Message
	log: bool = True
	event_type: str = "Reception"

	def __str__(self):
		return f'(T = {self.time}) - [Reception Event | {self.sender_id} ->( {self.recipient_id} ] ---> Message: {self.message}'


@dataclass
class PacketLossEvent(Event):

	sender_id: int
	recipient_id: int
	message: Message
	log: bool = True
	event_type: str = "Packet Loss"

	def __str__(self):
		return f'(T = {self.time}) - [Packet Loss Event | {self.sender_id} -X- {self.recipient_id} ] ---> Message: {self.message}'