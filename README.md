Temp
-----

![Example](https://i.imgur.com/Hbnegqb.png)

A script for showing sensor readings in more human-friendly format. It shows
current, min, max and average values. Should work with Python 2.7 to 3.5 and
possible - above 3.5.

**NOTE**: This script is only for **Linux** systems with installed, enabled and
initialized `lm_sensors`!

Known issues:
-------------
 - lack of optimizations of any kind - reading values, internal re-calculations,
 Memory and CPU consumption, etc.
 - HDD temp is not shown at this time
 - Only console version without any options; i.e. stuck on **°C**
 - nVidia GPU proprietary driver readings are supported, but require root access

It's silly script, but it _works_ for me!
