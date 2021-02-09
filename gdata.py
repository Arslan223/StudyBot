import json


def load():
	with open("data.json", "r") as f:
		return json.load(f)


def update(obj):
	with open("data.json", "w") as f:
		json.dump(obj, f)
