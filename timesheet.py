import settings
import operator
from utils import split, first
from realtime import Time
from mapping import driving_time


class TimesheetItem:
    item_type = ''

    def __init__(self, job):
        self.job = job

    def output(self):
        return [self.item_type, self.start_time.to_time(), self.job.pickup.place, self.job.destination.place, self.finish_time.to_time(), self.total_time.to_time(), None, None, self.total_time.to_time()]

    @property
    def total_time(self):
        return self.finish_time - self.start_time

    @property
    def start_time(self):
        return self.job.pickup.time

    @property
    def finish_time(self):
        return self.job.destination.time


class JobItem(TimesheetItem):
    item_type = 'Job'
    

class FromDepotItem(JobItem):
    item_type = 'Start'

    @property
    def start_time(self):
        return self.job.signon_time

    @property
    def finish_time(self):
        return self.job.start_time

    def output(self):
        return [self.item_type, self.start_time.to_time(), 'Depot', self.job.pickup.place, self.finish_time.to_time(), self.total_time.to_time(), None, None, self.total_time.to_time()]


class ToDepotItem(JobItem):
    item_type = 'Finish'

    @property
    def start_time(self):
        return self.job.finish_time

    @property
    def finish_time(self):
        return self.job.signoff_time

    def output(self):
        return [self.item_type, self.start_time.to_time(), self.job.destination.place, 'Depot', self.finish_time.to_time(), self.total_time.to_time(), None, None, self.total_time.to_time()]


class LegItem(TimesheetItem):
    def __init__(self, prev_job, next_job):
        self.prev_job = prev_job
        self.next_job = next_job

    @property
    def start_time(self):
        return self.prev_job.finish_time

    @property
    def finish_time(self):
        return self.next_job.start_time


class BreakItem(LegItem):
    item_type = 'Break'
    paid = Time(0)
    unpaid = Time(0)
    split_shift = False

    def __init__(self, prev_job, next_job):
        super().__init__(prev_job, next_job)
        self.paid = self.total_time

    def output(self):
        return [self.item_type, self.start_time.to_time(), '-', '-', self.finish_time.to_time(), None, 
            self.paid.to_time() if self.paid.seconds else None, 
            self.unpaid.to_time() if self.unpaid.seconds else None, 
            self.paid.to_time() if self.paid.seconds else None]


class SplitShiftItem(BreakItem):
    item_type = 'Split shift'
    split_shift = True

    def __init__(self, prev_job, next_job):
        super().__init__(prev_job, next_job)
        self.paid = Time(0)
        self.unpaid = self.total_time


class PositioningItem(LegItem):
    item_type = 'Repositioning'

    def __init__(self, prev_job, next_job):
        super().__init__(prev_job, next_job)
        self.time = driving_time(prev_job.destination, next_job.pickup) 

    @property
    def is_material(self):
        return self.time > settings.REPOSITIONING_THRESHOLD

    @property
    def time_with_tolerance(self):
        return self.time * settings.REPOSITIONING_TOLERANCE

    @property
    def finish_time(self):
        return self.prev_job.finish_time + self.time_with_tolerance

    def output(self):
        return [self.item_type, self.start_time.to_time(), self.prev_job.destination.place, 
            self.next_job.pickup.place, self.finish_time.to_time(), self.total_time.to_time(), 
            None, None, self.total_time.to_time()]


class Alert:
    def __init__(self, target):
        self.target = target

    @property
    def start_time(self):
        return self.target.finish_time

    @property
    def finish_time(self):
        return self.target.finish_time

    @property
    def total_time(self):
        return Time(0)


class ExceedFatigueMgmtAlert(Alert):
    def __init__(self, target, duration):
        super().__init__(target)
        self.duration = duration

    def output(self):
        return ['Alert', None, 'Maximum non-break period exceeded', None, None, self.duration.to_time(), None, None, None]


class OverProvisioningAlert(Alert):
    def __init__(self, target, duration):
        super().__init__(target)
        self.duration = duration

    def output(self):
        return ['Alert', None, 'Over-provisioning', None, None, self.duration.to_time(), None, None, None]


class Adjustment(Alert):
    pass


class MinimumShiftAdjustment(Adjustment):
    def __init__(self, target, duration):
        super().__init__(target)
        self.duration = duration

    @property
    def total_time(self):
        return Time(self.duration)

    def output(self):
        return ['Adjustment', None, 'Minimum shift duration', None, None, None, None, None, self.duration.to_time()]


class Shift:
    def __init__(self, items, split=False):
        self.items = items
        self.split = split

        self.check_minimums()
        self.check_max_working_time()
        self.check_over_provisioning()

    def check_max_working_time(self):
        idx = 0
        min_idx = 0
        items = self.items[:]            
        time_worked = Time(0)

        while(items):
            item = items.pop(0)
            idx += 1
            if isinstance(item, BreakItem): 
                time_worked = Time(0)
                min_idx = idx
            else:
                time_worked += item.total_time
                if time_worked > settings.MAX_TIME_BEFORE_BREAK:
                    # greedy grab all jobs until the next break
                    if items and not isinstance(item, BreakItem):
                        continue
                    alert = ExceedFatigueMgmtAlert(item, time_worked)
                    self.items.insert(idx, alert)
                    for item in self.items[min_idx:idx + 1]:
                        item.colour = settings.BREAK_ALERT_COLOUR
                    return  
    
    def check_over_provisioning(self):
        idx = 1
        items = self.items[:]
        prev = items.pop(0)

        while items:
            next = items.pop(0)
            if prev.finish_time - next.start_time > settings.OVERPROVISIONING_THREHOLD:
                alert = OverProvisioningAlert(prev, prev.finish_time - next.start_time)
                alert.colour = settings.OVERPROVISIONING_ALERT_COLOUR
                self.items.insert(idx, alert)
                # update start time of next job to finish time of last job so total hours are correctly calculates
                next.job.pickup.time = prev.finish_time
                prev.colour = next.colour = settings.OVERPROVISIONING_ALERT_COLOUR
                idx += 1

            prev = next
            idx += 1
  
    def check_minimums(self):
        if self.is_minimum:
            adjustment = MinimumShiftAdjustment(self.items[-1], self.adjustment)
            self.items.append(adjustment)

    @property
    def start_time(self):
        return self.items[0].start_time

    @property
    def finish_time(self):
        return self.items[-1].finish_time

    @property
    def total_time(self):
        return self.finish_time - self.start_time

    @property
    def total_paid_breaks(self):
        return Time(sum([item.paid.seconds for item in self.items if isinstance(item, BreakItem)]))

    @property
    def total_unpaid_breaks(self):
        return Time(sum([item.unpaid.seconds for item in self.items if isinstance(item, BreakItem)]))

    @property
    def total_payable_hours(self):
        return self.total_time - self.total_unpaid_breaks

    @property
    def total_worked_hours(self):
        return self.total_payable_hours - self.total_paid_breaks

    @property
    def total_adjustments(self):
        time = Time(sum([item.total_time for item in self.items if isinstance(item, Adjustment)]))
        return time

    @property
    def is_minimum(self):
        return self.total_payable_hours.seconds < settings.MIN_SPLIT_DURATION if split else self.total_payable_hours.seconds < settings.MIN_SHIFT_DURATION

    @property
    def adjustment(self):
        return Time(settings.MIN_SPLIT_DURATION - self.total_payable_hours.seconds if self.split else settings.MIN_SHIFT_DURATION - self.total_payable_hours.seconds)


class Timesheet:

    def __init__(self, driver):
        self.driver = driver
        self.jobs = driver.jobs
        self.items = []
        self.shifts = None
        self.split = None
        self.alert = False

        self.process()

    @property
    def total_time(self):
        return self.shifts[-1].finish_time - self.shifts[0].start_time

    @property
    def total_paid_breaks(self):
        return Time(sum([shift.total_paid_breaks.seconds for shift in self.shifts]))

    @property
    def total_unpaid_breaks(self):
        breaks = Time(sum([shift.total_unpaid_breaks.seconds for shift in self.shifts]))
        if self.split:
            breaks += self.split.total_time
        return breaks

    @property
    def total_payable_hours(self):
        return self.total_time - self.total_unpaid_breaks + self.total_adjustments

    @property
    def total_worked_hours(self):
        return self.total_payable_hours - self.total_paid_breaks

    @property
    def total_adjustments(self):
        time = Time(sum([item.total_adjustments for item in self.shifts]))
        return time

    def process(self):
        breaks = []
        split_shift = False
        prev_job = self.jobs.pop(0)

        if prev_job.pickup.place != 'Depot':
            self.items.append(FromDepotItem(prev_job))

        self.items.append(JobItem(prev_job))

        while self.jobs:
            next_job = self.jobs.pop(0)

            # split shift
            if next_job.signon_time - prev_job.signoff_time > settings.SPLIT_SHIFT_THRESHOLD:
                to_depot = ToDepotItem(prev_job)
                from_depot = FromDepotItem(next_job)
                split_shift = SplitShiftItem(to_depot, from_depot)
                self.items.append(to_depot)
                self.items.append(split_shift)
                self.items.append(from_depot)
                breaks.append(split_shift)
                split_shift = True

            else:
                # repositioning
                if prev_job.destination != next_job.pickup:
                    item = PositioningItem(prev_job, next_job)
                    if item.is_material:
                        self.items.append(item)

                # break
                last_item = self.items[-1]
                if last_item.finish_time < next_job.start_time:
                    break_ = BreakItem(last_item, next_job)
                    self.items.append(break_)
                    breaks.append(break_)

            self.items.append(JobItem(next_job))
            prev_job = next_job

        if prev_job.pickup.place != 'Depot':
            self.items.append(ToDepotItem(prev_job))

        # appply EBA
        breaks = list(reversed(sorted(breaks, key=operator.attrgetter('total_time'))))
        if breaks:
            # if split shift - all other breaks are paid
            if split_shift:
                breaks.pop(0)
                for break_ in breaks:
                    break_.paid = break_.total_time
                    break_.unpaid = Time(0)
            
            else:
                breaks = list(filter(lambda item: item.total_time >= settings.MIN_BREAK_TIME, breaks))
                blocks = []
                for break_ in breaks:
                    blocks.extend(self.break_blocks(break_))
                # sort the blocks by size and take top BREAK_COUNT blocks to be unpaid
                blocks = sorted(blocks, key=operator.itemgetter(1))
                unpaid_blocks = blocks[-settings.BREAK_COUNT:]
                for break_, block in unpaid_blocks:
                    break_.unpaid += Time(block)
                    break_.paid -= Time(block)

        # generate shifts
        split_shift_finder = lambda item: isinstance(item, SplitShiftItem) and item.unpaid and not item.paid
        shifts = split(self.items, split_shift_finder)
        self.shifts = [Shift(item, len(shifts) > 1) for item in shifts]
        
        if len(shifts) > 1:
            self.split = first(self.items, split_shift_finder)

        # check minimum total shift time
        elif self.total_payable_hours < settings.MIN_SHIFT_DURATION:
            time = Time(settings.MIN_SHIFT_DURATION - self.total_payable_hours.seconds)
            adjustment = MinimumShiftAdjustment(self.shifts[0].items[-1], time)
            self.shifts[0].items.append(adjustment)


    def break_blocks(self, break_):
        # what this does -
        # it greedy grabs as many MAX_TIME blocks as possible then 
        # adds whatever block size is left above the MIN_TIME
        time = break_.total_time.seconds
        block_count = time // settings.MAX_BREAK_TIME
        blocks = [settings.MAX_BREAK_TIME] * int(block_count)
        remainder = time % settings.MAX_BREAK_TIME
        if remainder > settings.MIN_BREAK_TIME:
            blocks.append(int(remainder))
        return [[break_, block] for block in blocks]