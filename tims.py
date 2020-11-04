import jobs
import driver
import export
import settings
import timesheet

jobs.load_jobs('d:\\jobs2.xls')

timesheets = [timesheet.Timesheet(driver) for driver in driver.Driver.all_drivers()]

export.export('d:\\output2.xlsx', timesheets)


