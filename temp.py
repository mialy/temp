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
				label = self.__readfile(sensor + "temp" + index + "_label")
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
		return current

	def output(self, readings, scale = 'C'):
		# sort sensors
		rkeys = readings.keys()
		rkeys = sorted(rkeys)
		rkeys = sorted(rkeys, key=len, reverse=True)
		for s in rkeys:
			print(u"{0:>25s}\t{1:>8s}\t{2:>8s}\t{3:>8s}"
				.format(u"Sensor '" + s + u"'", "Cur", "Min", "Max"));
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
				print(u"{0:>25s}\t{1:>8s}\t{2:>8s}\t{3:>8s}"
					.format(i, cur, min, max))
			print("\n")

	def degree(self, temp, scale = 'C'):
		sign = u'\N{DEGREE SIGN}'
		if scale == 'K':
			temp = temp + 273.15
			sign = ""
		elif scale == 'F':
			temp = temp * 9/5.0 + 32
		else:
			scale = "C"
		return str(temp) + " " + sign + scale

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

if __name__ == "__main__":
	app = Readings()
	app.run()

