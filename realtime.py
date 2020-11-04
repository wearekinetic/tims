import datetime

SECONDS_IN_DAY = 86400
SECONDS_IN_HOUR = 3600
SECONDS_IN_MINUTE = 60


def datetime_to_seconds(dt):
    return dt.hour * SECONDS_IN_HOUR + dt.minute * SECONDS_IN_MINUTE


class Time:

    def __init__(self, time=0, overflow=False):
        if type(time) is str:
            time = datetime.datetime.strptime(time, '%H:%M')
        
        if isinstance(time, datetime.datetime):
            self.seconds = datetime_to_seconds(time)

        elif isinstance(time, Time):
            self.seconds = time.seconds

        else:
            self.seconds = time

        hours, minutes, seconds = self.struct()
        if int(seconds) > 0:
            minutes += 1
            self.seconds = hours * SECONDS_IN_HOUR + minutes * SECONDS_IN_MINUTE

    def __bool__(self):
        return self.seconds != 0

    def __add__(self, other):
        seconds = self.seconds + other.seconds
        return Time(seconds)

    def __radd__(self, other):
        seconds = self.seconds + other
        return Time(seconds)

    def __sub__(self, other):
        return Time(self.seconds - other.seconds)

    def __mul__(self, other):
        return Time(self.seconds * other)

    def __gt__(self, other):
        return self.seconds > other

    def __ge__(self, other):
        return self.seconds > other

    def __lt__(self, other):
        return self.seconds < other

    def __lte__(self, other):
        return self.seconds < other

    def __str__(self):
        hours, minutes, _ = self.struct()
        return f'{hours:0>2d}:{minutes:0>2d}'

    def struct(self):
        hours = self.seconds // 3600
        minutes = (self.seconds % SECONDS_IN_HOUR) // SECONDS_IN_MINUTE
        seconds = self.seconds % SECONDS_IN_HOUR % SECONDS_IN_MINUTE
        return hours, minutes, seconds

    def to_time(self):
        hours, minutes, seconds = self.struct()
        try:
            return datetime.time(int(hours), int(minutes), 0)
        except ValueError:
            return '!!NEG!!'

    def to_datetime(self):
        hours, minutes, seconds = self.struct()
        return datetime.datetime(1900, 1, 1, int(hours), int(minutes), int(seconds))
