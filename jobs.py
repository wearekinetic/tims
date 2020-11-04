import operator
import datetime
import functools

import xlrd

import utils
import settings
import mapping

from realtime import Time
from driver import Driver

from exceptions import ParserException, GeocodingException, TimeException


class Job:
    def __init__(self, pickup, destination, signon_time, signoff_time):
        self.pickup = pickup
        self.destination = destination
        self.signon_time = signon_time
        self.signoff_time = signoff_time

    @property
    def start_time(self):
        return self.pickup.time

    @property
    def finish_time(self):
        return self.destination.time


    

@utils.error(ParserException)
def load_jobs(path: str) -> list:
    # read from xlsx spreadsheet
    workbook = xlrd.open_workbook(path)
    sheet = workbook.sheet_by_index(0)

    jobs = []

    for index in range(2, sheet.nrows):
        row = sheet.row_values(index)
        driver_code, driver_name, signon_time, start_time, pickup_place, dest_place, _, finish_time, signoff_time, _, pickup_lat, pickup_long, dest_lat, dest_long, *_ = row
        
        # header rows
        if driver_code.startswith('Coach Manager') or driver_code.startswith('Driver') or driver_code.startswith('Record Count') or driver_code.startswith('WHERE ('):
            continue

        # empy jobs
        if not driver_code.strip():
            continue

        # job sign on and signoff times
        try:
            signon_time = Time(signon_time)
        except ValueError:
            raise ParserException('Cannot convert sign on time', row, index + 1)

        try:
            signoff_time = Time(signoff_time)
        except ValueError:
            raise ParserException('Cannot convert sign off time', row, index + 1)

        # pickup
        try:
            start_time = Time(start_time)
        except ValueError:
            raise ParserException('Cannot convert start time', row, index + 1)

        pickup_location = mapping.Location(pickup_place.strip(), start_time, mapping.GPS(pickup_lat, pickup_long))

        # destination
        try:
            finish_time = Time(finish_time)
        except ValueError:
            raise ParserException('Cannot convert finish time', row, index + 1)

        dest_location = mapping.Location(dest_place.strip(), finish_time, mapping.GPS(dest_lat, dest_long))

        # check for weird times
        if finish_time < start_time:
            raise TimeException('Finish time cannot be before start time', row, index + 1)

        # job
        driver = Driver.get_driver(driver_code, driver_name)
        job = Job(pickup_location, dest_location, signon_time, signoff_time)
        driver.add_job(job)
        jobs.append(job)

    return jobs
   

