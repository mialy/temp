#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Mikhail Kyosev <mialygk@gmail.com>
# License: BSD - 2-caluse

import re
import glob
import time
import os
import datetime

class Readings:
	def __init__(self):
		self.sensors = {}
		self.start_time = int(time.time())
		self.delta_t = {}

	def run(self):
		current = {}

		try:
			while True:
				now = int(time.time()) - int(self.start_time)
				self.save_data(current, self.fetch_data())
				print("\033[0m\033[2J\033[0;0H")
				print("Running from: {0:10}\n".format(str(datetime.timedelta(seconds = now))))
				self.output(current, "C")
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
					label = "UNKNOWN Item"

				readings[name][label] = t
		t = self.nvidia_temp()
		if t:
			readings["nvidia"] = {}
			readings["nvidia"]["GPU"] = t
		return readings

	def save_data(self, current, new):
		for s in new:

			if not s in current:
				current[s] = {}
			for i in new[s]:
				t = new[s][i]

				reading = i + "_" + s
				if not reading in self.delta_t:
					self.delta_t[reading] = {}
				if not t in self.delta_t[reading]:
					self.delta_t[reading][t] = 1
				else:
					self.delta_t[reading][t] += 1

				if not i in current[s]:
					current[s][i] = {}
					current[s][i]['min'] = t
					current[s][i]['max'] = t
					current[s][i]['cur'] = t
				if current[s][i]['min'] > t:
					current[s][i]['min'] = t
				if current[s][i]['max'] < t:
					current[s][i]['max'] = t
				current[s][i]['cur'] = t
				current[s][i]['avg'] = self.__avg_delta(reading)
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
			keys = readings[s].keys()
			keys = sorted(keys)
			keys = sorted(keys, key=len, reverse=True)
			for i in keys:
				t = readings[s][i]
				cur = self.degree(readings[s][i]['cur'], scale)
				min = self.degree(readings[s][i]['min'], scale)
				max = self.degree(readings[s][i]['max'], scale)
				avg = self.degree(readings[s][i]['avg'], scale, digits=1)
				print(fmt_string.format(i, cur, min, max, avg))
			print("\n")

	def degree(self, temp, scale = 'C', digits = 0):
		sign = u'\N{DEGREE SIGN}'
		if scale == 'K':
			temp = temp + 273.15
			sign = ""
		elif scale == 'F':
			temp = temp * 9/5.0 + 32
		else:
			scale = "C"

		fmt = u"{0:." + str(digits) + "f}"
		return (fmt.format(round(temp + 0.0, digits))) + " " + sign + scale

	def nvidia_temp(self):
		temp = os.popen("nvidia-settings -q gpucoretemp -t").readline().strip()
		try:
			return int(temp)
		except:
			try:
				temp = os.popen("nvidia-smi -q -d TEMPERATURE").read().strip()
				temp = int(re.search(r': ([0-9]+) C', temp, re.M | re.I).group(1))
				return temp
			except:
				return 0

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

if __name__ == "__main__":
	app = Readings()
	app.run()

