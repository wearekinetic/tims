import operator
import datetime

import utils
import settings
from realtime import SECONDS_IN_HOUR
from mapping import Location, driving_time


class Driver:

    _drivers = {}

    @classmethod
    def get_driver(cls, code, name):
        if code not in cls._drivers:
            cls._drivers[code] = Driver(code, name)
        return cls._drivers[code]

    @classmethod
    def all_drivers(cls) -> list:
        return cls._drivers.values()

    def __init__(self, code, name) -> None:
        self.code = code
        self.name = name
        self.jobs = []
        self.other = []

    def add_job(self, job) -> None:
        self.jobs.append(job)
