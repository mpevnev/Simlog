""" This module contains a wrapper around I/O to the log file """

import entry

class Logfile():
    """ This class provides I/O to the log file """

    def __init__(self, path):
        self.path = path

    def ensure_existence(self):
        """ Create the log file if it doesn't exist """
        if not self.path.exists():
            self.path.touch()

    #--------- writing to the log ---------#

    def prepend(self, e):
        """ Place the entry in the head of the file """
        with self.path.open("wb+") as f:
            old = f.read()
            f.write(e.to_bytes())
            f.write(old)

    def replace(self, new_e):
        """ Replace the entry with the same date and mark as the given one """
        all_entries = self.all_entries()
        with self.path.open("wb") as f:
            for old_e in all_entries:
                if new_e.match(old_e):
                    f.write(new_e.to_bytes())
                else:
                    f.write(old_e.to_bytes())

    #--------- querying entries in bulk ---------#

    def filter_entries(self, predicate):
        """ Return a list of entries such that predicate(entry) is True """
        res = []
        with self.path.open("rb") as f:
            while True:
                try:
                    new = entry.Entry.from_binary_file(f)
                    if predicate(new): res.append(new)
                except entry.EntryReadError:
                    return res

    def all_entries(self):
        """ Return all the entries in the log """
        return self.filter_entries(lambda e: True)

    def matching_entries(self, date, mark):
        """ Return a list of entries with given date and mark """
        return self.filter_entries(lambda e: e.date == date and e.mark == mark)

    #--------- querying entries one by one ---------#

    def find_entry(self, predicate):
        """ Return the newest entry such that predicate(entry) is True """
        with self.path.open("rb") as f:
            while True:
                try:
                    new = entry.Entry.from_binary_file(f)
                    if predicate(new): return new
                except entry.EntryReadError:
                    return None

    def find_specific(self, date, mark=""):
        """
        Return an entry with given date and mark, or None if such an entry does
        not exist.
        """
        return self.find_entry(lambda e: e.date == date and e.mark == mark)
