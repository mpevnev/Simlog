""" A module for log entries' representation """

import datetime
import sys

# a number of constants controlling the structure of entries' headers
YEAR_SIZE = 4
MONTH_SIZE = 4
DAY_SIZE = 4
LENGTH_SIZE = 8
MARK_LENGTH_SIZE = 8

YEAR_OFFSET = 0
MONTH_OFFSET = YEAR_OFFSET + YEAR_SIZE
DAY_OFFSET = MONTH_OFFSET + MONTH_SIZE
LENGTH_OFFSET = DAY_OFFSET + DAY_SIZE
MARK_LENGTH_OFFSET = LENGTH_OFFSET + LENGTH_SIZE

HEADER_SIZE = MARK_LENGTH_OFFSET + MARK_LENGTH_SIZE

class Entry():
    """ A representation of a log entry """

    def __init__(self, contents, date, mark):
        self.mark = mark
        self.date = date
        self.contents = contents

    def __lt__(self, other):
        return self.date < other.date

    def __gt__(self, other):
        return self.date > other.date

    def __eq__(self, other):
        return self.date == other.date

    def format(self, no_date=False, no_mark=False, no_end=False):
        """ Format entry for printing """
        res = ""
        if not no_date:
            date = self.date.strftime("%Y %b %d, %A")
            res += f"-- {date} --\n"
        if not no_mark:
            mark = "Not marked" if self.mark == "" else f"Marked: {self.mark}"
            res += f"-- {mark} --\n"
        res += f"{self.contents.strip()}"
        if not no_end:
            res += "\n-- end --\n"
        return res

    def to_bytes(self):
        """ Convert an entry to a bytestring """
        mark_len = len(self.mark)
        cont = bytes(self.contents, "utf-8")
        length = len(cont)
        header = self.date.year.to_bytes(YEAR_SIZE, byteorder=sys.byteorder) \
            + self.date.month.to_bytes(MONTH_SIZE, byteorder=sys.byteorder) \
            + self.date.day.to_bytes(DAY_SIZE, byteorder=sys.byteorder) \
            + length.to_bytes(LENGTH_SIZE, byteorder=sys.byteorder) \
            + mark_len.to_bytes(MARK_LENGTH_SIZE, byteorder=sys.byteorder) \
            + bytes(self.mark, "utf-8")
        return header + cont

    def match(self, other):
        """
        Return whether date and mark of this entry matches those of another
        entry
        """
        return (self.mark == other.mark
                and self.date == other.date)

    def merge(self, other):
        """ Merge two entries """
        left = self.contents.strip()
        right = other.contents.strip()
        self.contents = f"{left}\n{right}"

    def to_text_file(self, filename, no_date=False, no_mark=False, no_end=False):
        """ Dump the entry to a file. """
        with filename.open("w") as f:
            f.write(self.format(no_date, no_mark, no_end))

    @classmethod
    def from_binary_file(cls, from_file):
        """ Load an entry from a binary file """
        header = from_file.read(HEADER_SIZE)
        if len(header) < HEADER_SIZE:
            raise EntryReadError()
        year = (int).from_bytes(header[YEAR_OFFSET : YEAR_OFFSET + YEAR_SIZE],
                sys.byteorder)
        month = (int).from_bytes(header[MONTH_OFFSET : MONTH_OFFSET + MONTH_SIZE],
                sys.byteorder)
        day = (int).from_bytes(header[DAY_OFFSET : DAY_OFFSET + DAY_SIZE],
                sys.byteorder)
        length = (int).from_bytes(header[LENGTH_OFFSET : LENGTH_OFFSET + LENGTH_SIZE],
                sys.byteorder)
        mark_len = (int).from_bytes(header[
            MARK_LENGTH_OFFSET : MARK_LENGTH_OFFSET + MARK_LENGTH_SIZE],
            sys.byteorder)
        rest = from_file.read(length + mark_len)
        mark = rest[:mark_len].decode("utf-8")
        contents = rest[mark_len:mark_len + length].decode("utf-8")
        return Entry(contents, datetime.date(year, month, day), mark)

    @classmethod
    def from_text_file(cls, filepath, date, mark):
        """
        Load an entry from a text file.

        'filepath' must be a pathlib's Path.
        """
        with filepath.open("r") as f:
            cont = f.read()
            return Entry(cont, date, mark)

class EntryReadError(Exception):
    """
    An error of this type will be raised when an entry read from a binary file
    is malformed.
    """
    pass
