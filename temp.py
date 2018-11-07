#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Mikhail Kyosev <mialygk@gmail.com>
# License: BSD - 2-caluse

from __future__ import print_function
from collections import OrderedDict
import re
import glob
import time
import os
import datetime
import functools

class Readings:
	def __init__(self):
		self.start_time = int(time.time())
		self.delta_t = {}

	def run(self):
		current = {}

		try:
			while True:
				now = int(time.time()) - int(self.start_time)
				self.save_data(current, self.fetch_data())
				print("\033[0m\033[2J\033[0;0H")
				self.output(current, "C")
				print("Running from: {0:10}".format(str(datetime.timedelta(seconds = now))))
				print("Press CTRL + C to exit...")
				time.sleep(1)
		except KeyboardInterrupt:
			pass

	def fetch_data(self):
		readings = {}

		sensors = sorted(glob.glob("/sys/class/hwmon/hwmon*/"))
		for sensor in sensors:
			name = self.__readfile(sensor + "name")
			readings[name] = {}
			temps = sorted(glob.glob(sensor + "temp*_input"))
			for temp in temps:
				t = int(int(self.__readfile(temp)) / 1000)
				index = re.match(r'temp([0-9]+)_input', os.path.basename(temp)).group(1)
				try:
					label = self.__readfile(sensor + "temp" + index + "_label")
				except:
					label = "Item #" + index

				readings[name][label] = {
					'type': 'temp',
					'value': t
				}

			fans = sorted(glob.glob(sensor + "fan*_input"))
			for fan in fans:
				t = int(self.__readfile(fan))
				index = re.match(r'fan([0-9]+)_input', os.path.basename(fan)).group(1)
				try:
					label = self.__readfile(sensor + "fan" + index + "_label")
				except:
					label = "Fan #" + index

				readings[name][label] = {
					'type': "rotary",
					'value': t
				}

			voltage = sorted(glob.glob(sensor + "in*_input"))
			for volt in voltage:
				t = int(self.__readfile(volt))
				index = re.match(r'in([0-9]+)_input', os.path.basename(volt)).group(1)
				try:
					label = self.__readfile(sensor + "in" + index + "_label")
				except:
					label = "Voltage #" + index

				readings[name][label] = {
					'type': 'voltage',
					'value': t / 1000.0
				}

		try:
			readings.setdefault("nvidia", {})
			readings["nvidia"]["Core"] = {
				'type': 'temp',
				'value': self.nvidia_temp()
			}
		except:
			pass

		try:
			readings.setdefault("nvidia", {})
			readings['nvidia']['Fan'] = {
				'type': 'rotary',
				'value': self.nvidia_fan()
			}
		except:
			pass

		if not len(readings["nvidia"].keys()):
			del(readings["nvidia"])

		return readings

	def save_data(self, current, new):
		for s in new:
			if not s in current:
				current[s] = {}
			for i in new[s]:
				val = new[s][i]['value']
				typ = new[s][i]['type']

				reading = i + "_" + s
				if not reading in self.delta_t:
					self.delta_t[reading] = {}
				if not val in self.delta_t[reading]:
					self.delta_t[reading][val] = 1
				else:
					self.delta_t[reading][val] += 1

				if not i in current[s]:
					current[s][i] = [
						('cur', val),
						('min', val),
						('max', val),
						('avg', val),
						('type', typ)
					]
				else:
					current[s][i] = [
						('cur', val),
						('min', val if val < current[s][i][1][1] else current[s][i][1][1]),
						('max', val if val > current[s][i][2][1] else current[s][i][2][1]),
						('avg', self.__avg_delta(reading)),
						('type', typ)
					]
		return current

	def output(self, readings, scale = 'C'):
		# sort sensors
		rkeys = readings.keys()
		rkeys = sorted(rkeys)
		rkeys = sorted(rkeys, key=len, reverse=True)
		fmt_string = u"{0:>25s}{1:>13s}{2:>13s}{3:>13s}{4:>15s}"
		for s in rkeys:
			print(fmt_string.format(u"Sensor '" + s + u"'", "Current", "Min", "Max", "Avg"))
			print("-" * 80)
			# sort labels
			keys = sorted(readings[s].items(), key=functools.cmp_to_key(self.__sort_temp))
			keys = enumerate(OrderedDict(keys).keys())

			last_type = 'temp'
			for index, i in keys:
				typ = readings[s][i][4][1]
				if typ == 'temp':
					cur = self.degree(readings[s][i][0][1], scale)
					min = self.degree(readings[s][i][1][1], scale)
					max = self.degree(readings[s][i][2][1], scale)
					avg = self.degree(readings[s][i][3][1], scale, digits=1)
				elif typ == "rotary":
					cur = self.rpm(readings[s][i][0][1])
					min = self.rpm(readings[s][i][1][1])
					max = self.rpm(readings[s][i][2][1])
					avg = self.rpm(readings[s][i][3][1], digits=1)
				elif typ == 'voltage':
					cur = self.voltage(readings[s][i][0][1])
					min = self.voltage(readings[s][i][1][1])
					max = self.voltage(readings[s][i][2][1])
					avg = self.voltage(readings[s][i][3][1])
				else:
					continue
				if index and last_type != typ:
					print('\n', end='')
				print(fmt_string.format(i, cur, min, max, avg))
				last_type = typ
			print('\n', end='')

	def degree(self, temp, scale='C', digits=0):
		sign = u'\N{DEGREE SIGN}'
		if scale == 'K':
			temp = temp + 273.15
			sign = ""
		elif scale == 'F':
			temp = temp * 9/5.0 + 32
		else:
			scale = "C"

		return self.rounding(temp, digits) + ' ' + sign + scale

	def rpm(self, value, digits=0):
		return self.rounding(value, digits) + ' rpm'

	def voltage(self, value, digits=2):
		sign = '+'
		if value < 0:
			sign = '-'
		return sign + self.rounding(value, digits) + ' V'

	def rounding(self, value, digits=0):
		fmt = u"{0:." + str(digits) + "f}"
		return (fmt.format(round(value + 0.0, digits)))

	def nvidia_temp(self):
		try:
			temp = os.popen("nvidia-settings -q gpucoretemp -t").readline().strip()
			return int(temp)
		except:
			try:
				temp = os.popen("nvidia-smi -q -d TEMPERATURE").read().strip()
				temp = int(re.search(r': ([0-9]+) C', temp, re.M | re.I).group(1))
				return temp
			except:
				raise Exception("Invalid reading")

	def nvidia_fan(self):
		try:
			val = os.popen("nvidia-settings -q GPUCurrentFanSpeed -t").readline().strip()
			return int(val)
		except:
			try:
				val = os.popen("nvidia-smi -a | grep -i Fan\ Speed").read().strip()
				val = int(re.search(r': ([0-9]+) \%', val, re.M | re.I).group(1))
				return val
			except:
				raise Exception("Invalid reading")

	def __readfile(self, filename):
		with open(filename, 'r') as f:
			return f.readline().strip()

	def __avg_delta(self, name):
		total = 0
		count = 0
		for key, value in self.delta_t[name].items():
			count += value
			total += key * value
		return total / (count + 0.0)

	def __sort_temp(self, a, b):
		if a[1][4][1] != b[1][4][1]:
			return len(a[1][4][1]) - len(b[1][4][1])

		# asc sort by names
		if len(a[0]) == len(b[0]):
			return -1 if a[0] < b[0] else 1 if a[0] > b[0] else 0

		# desc sort by length
		return len(b[0]) - len(a[0])

if __name__ == "__main__":
	app = Readings()
	app.run()

