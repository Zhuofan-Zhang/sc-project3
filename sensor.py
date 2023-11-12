#!/usr/bin/env python3

import random


class Sensor:
    # Map sensor types to random value generator functions
    generators = {
        # common sensors
        'temperature': lambda: random.randint(0, 30),
        'light': lambda: random.randint(0, 30),
        # device sensors
        'humidity': lambda: random.randint(0, 90),
        'radiation': lambda: random.randint(0, 30),
        'co2': lambda: random.randint(0, 30),
        'smoke': lambda: random.randint(0, 30),
        'light_switch': lambda: random.choice([True, False]),
        'motion': lambda: random.choice([True, False]),
        # washing machine sensors
        'washer': lambda: random.choice(['on', 'off']),
        'rpm': lambda: random.randint(0, 90),
        'duration': lambda: random.randint(0, 90),
        'lock': lambda: random.choice([True, False]),
        'load': lambda: random.randint(0, 90),
        'electricity_usage': lambda: random.randint(0, 90),
        'water_usage': lambda: random.randint(0, 90),

    }
