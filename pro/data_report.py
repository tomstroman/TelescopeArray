# data_report.py
# Thomas Stroman, University of Utah 2018-01-07
# A program to report on the possibility, existence, availability, and status of data
# on a night-by-night basis from the Telescope Array experiment from the perspective
# of a specific data storage server ("tadserv") and compute cluster ("sithlord").

# The "source of truth" for *possibility* of data is the lunar calendar: if the moon
# is above the horizon, no data can be taken. In a more specific sense, the number of
# moonless nighttime hours (between the end of astronomical twilight after dusk and the
# beginning of astronomical twilight before dawn) is calculated for each day on the
# Telescope Array wiki, and for each date in the past, we also have records of any
# attempt to collect data. So the wiki is the source of truth for possibility.

# The source of truth for *existence* of data is its presence on any disk in tadserv.
# The raw data, straight from the telescopes, is stored there, but with no guarantee of
# high availability; sometimes a system containing a subset of the data is down for maintenance.
# So the *availability* of the data is more fluid, potentially varying from one report to another.

# The *status* of data indicates whether it has undergone the basic processing to promote it to
# the DST framework used by all the analysis code.

def data_report():
    pass

if __name__ == '__main__':
    data_report()
