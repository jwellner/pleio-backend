from django.utils import timezone
from django.utils.timezone import timedelta


def first_same_weekday(weekday, timestamp):
    first = timestamp - timedelta(days=(timestamp.day - 1))
    wd_first = first.weekday()
    if weekday > wd_first:
        return first + timedelta(days=(weekday - wd_first))
    if weekday < wd_first:
        return first + timedelta(days=(weekday + 7 - wd_first))
    return first


class RangeCalculatorBase:
    def __init__(self, event):
        self.event = event

    @property
    def interval(self):
        return self.event.range_settings.get('interval')

    @property
    def start_time(self):
        return self.event.range_starttime

    def next(self) -> timezone.datetime:
        raise NotImplementedError()


class RangeCalculator(RangeCalculatorBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calculator = None
        for calculator in [DailyRange,
                           DayOfTheWeekRange,
                           DayOfTheMonthRange,
                           WeekdaydOfTheMonthRange]:
            if calculator.key == self.type:
                self.calculator = calculator(self.event)

    @property
    def type(self):
        return self.event.range_settings.get('type')

    def next(self):
        return self.calculator.next()


class DailyRange(RangeCalculatorBase):
    key = 'daily'

    def next(self):
        return self.start_time + timedelta(days=self.interval)


class DayOfTheWeekRange(RangeCalculatorBase):
    key = 'dayOfTheWeek'

    def next(self):
        return self.start_time + timedelta(weeks=self.interval)


class DayOfTheMonthRange(RangeCalculatorBase):
    key = 'dayOfTheMonth'

    @staticmethod
    def next_month(reference):
        result = reference - timedelta(days=(reference.day - 1))
        result += timedelta(days=40)
        result -= timedelta(days=(result.day - 1))
        return result

    def next(self):
        next_starttime = self.cycle(self.start_time)
        interval = self.interval
        while interval > 1:
            next_starttime = self.cycle(next_starttime)
            interval -= 1
        return next_starttime

    def cycle(self, reference):
        result = self.next_month(reference) + timedelta(days=(self.start_time.day - 1))

        # Last day of the month.
        if result.day != reference.day:
            result = self.next_month(reference)
            return self.next_month(result) - timedelta(days=1)

        return result


class WeekdaydOfTheMonthRange(DayOfTheMonthRange):
    key = 'weekdayOfTheMonth'

    def cycle(self, reference):
        reference_first_weekday = first_same_weekday(reference.weekday(), reference)
        days_offset = reference.day - reference_first_weekday.day

        next_month = self.next_month(reference)
        next_first_same_weekday = first_same_weekday(reference.weekday(), next_month)

        return next_month + timedelta(days=(next_first_same_weekday.day - 1 + days_offset))
