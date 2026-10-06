# just a clock helper
from ..registry import category
from ._helpers import prop

category("clock", "Clock", "#C9803A", 90)

for _p in ["Date", "Time", "Year", "Month", "Day", "Hour", "Minute", "Second",
           "Millisecond", "ElapsedMilliseconds", "WeekDay"]:
    prop("clock_" + _p.lower(), "clock", "Clock." + _p, "Clock." + _p)
