import json

from network import Network

network = Network()

events = network.execute(max_time_steps = 100)

with open('output.json', 'w') as file:
	content = json.dumps(events, default=lambda o: o.__dict__, indent = 4)
	file.write(content)