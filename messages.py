from typing import List
from dataclasses import dataclass, field

@dataclass
class Message:
	sender_id: int = None
	recipient_ids: List[int] = field(default_factory = list)

@dataclass
class RREQ(Message):

	request_id: int = None
	destination_id: int = None
	destination_sequence_numberint: int = None 		# Last destination sequence number known to the originator
	originator_id: int = None
	originator_sequence_number: int = None
	hop_count: int = None

	def __str__(self):
		return f'(RREQ) [ RID: {self.request_id}, DID: {self.destination_id}, DSN: {self.destination_sequence_number}, OID: {self.originator_id}, OSN: {self.originator_sequence_number}, HC: {hop_count} ]'

@dataclass
class RREP(Message):

	destination_id: int = None
	destination_sequence_number: int = None 
	originator_id: int = None
	originator_sequence_number: int = None
	hop_count: int = None
	life_time: int = None

	def __str__(self):
		return f'(RREP) [ DID: {self.destination_id}, DSN: {self.destination_sequence_number}, OID: {self.originator_id}, OSN: {self.originator_sequence_number}, HC: {hop_count} ]'

@dataclass
class RERR(Message):

	hop_count: int = None
	unreachable_destination_id: int = None
	unreachable_destination_sequence_number: int = None
	unreachable_destination_count: int = None

@dataclass
class HELLO(Message):

	def __str__(self):
		return f'(HELLO) [ SID: {self.sender_id} ]'