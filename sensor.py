#!/usr/bin/env python3

import random


class Sensor:
    # Map sensor types to random value generator functions
    generators = {'speed': lambda: random.randint(40, 90),
                  'proximity': lambda: random.randint(1, 50),
                  'pressure': lambda: random.randint(20, 40),
                  'heartrate': lambda: random.randint(40, 120)}
