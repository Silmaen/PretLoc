"""
Defines a Period class to represent a time period with start and end dates.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Period:
    """
    Model representing a time period with a start and end date.
    The maximum resolution is one minute, we do not take seconds into account.
    """

    def __init__(
        self,
        start: datetime = datetime(1970, 1, 1, 0, 0),
        end: datetime = datetime(1970, 1, 1, 0, 0),
    ):
        """
        Initialize a Period instance.
        :param start: Start date of the period
        :param end: End date of the period
        """
        start = start.replace(second=0, microsecond=0)
        end = end.replace(second=0, microsecond=0)
        if start > end:
            start, end = end, start
        self.start_date = start
        self.end_date = end

    def set_start(self, start: datetime):
        """
        Set the start date of the period.
        :param start: New start date
        """
        start = start.replace(second=0, microsecond=0)
        if start > self.end_date:
            self.end_date = start
        self.start_date = start

    def set_end(self, end: datetime):
        """
        Set the end date of the period.
        :param end: New end date
        """
        end = end.replace(second=0, microsecond=0)
        if end < self.start_date:
            self.start_date = end
        self.end_date = end

    def contains(self, date: datetime) -> bool:
        """
        Check if a given date is within the period.
        :param date: Date to check
        :return: True if the date is within the period, False otherwise
        """
        return self.start_date <= date <= self.end_date

    def overlaps(self, other: "Period") -> bool:
        """
        Check if this period overlaps with another period.
        :param other: Another Period instance
        :return: True if the periods overlap, False otherwise
        """
        return self.start_date <= other.end_date and other.start_date <= self.end_date

    def duration_days(self) -> int:
        """
        Calculate the duration of the period in days.
        :return: Duration in days
        """
        return (self.end_date - self.start_date).days

    def duration_minutes(self) -> int:
        """
        Calculate the duration of the period in minutes.
        :return: Duration in minutes
        """
        delta = self.end_date - self.start_date
        return delta.days * 1440 + delta.seconds // 60

    def __str__(self) -> str:
        """
        String representation of the Period instance including hours and minutes.
        :return: String in the format "YYYY-MM-DD HH:MM to YYYY-MM-DD HH:MM"
        """
        return f"{self.start_date.strftime('%Y-%m-%d %H:%M')} to {self.end_date.strftime('%Y-%m-%d %H:%M')}"

    def __repr__(self) -> str:
        """
        Official string representation of the Period instance.
        :return: String in the format "Period(start=YYYY-MM-DD HH:MM, end=YYYY-MM-DD HH:MM)"
        """
        return f"Period(start={self.start_date.strftime('%Y-%m-%d %H:%M')}, end={self.end_date.strftime('%Y-%m-%d %H:%M')})"

    def __eq__(self, other: "Period") -> bool:
        """
        Check if two Period instances are equal.
        :param other: Another Period instance
        :return: True if both periods have the same start and end dates, False otherwise
        """
        return self.start_date == other.start_date and self.end_date == other.end_date
