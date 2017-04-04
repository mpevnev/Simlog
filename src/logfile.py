""" This module contains a wrapper around I/O to the log file """

import entry

class Logfile():
    """
    This class provides I/O operations on the log file

    All the methods that take 'before' and 'after' optional arguments will
    operate only on entries made before or after their respective argument
    values.
    """

    def __init__(self, path):
        self.path = path

    def ensure_existence(self):
        """ Create the log file if it doesn't exist """
        if not self.path.exists():
            self.path.touch()

    #--------- writing to the log ---------#

    def prepend(self, e):
        """ Place the entry in the head of the file """
        with self.path.open("rb+") as f:
            old = f.read()
            f.seek(0)
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

    def insert_by_date(self, new_e):
        """ Insert the new entry in between old ones """
        leave, shift = self.span(lambda e: e > new_e)
        with self.path.open("wb") as f:
            for old_e in leave:
                f.write(old_e.to_bytes())
            f.write(new_e.to_bytes())
            for old_e in shift:
                f.write(old_e.to_bytes())

    #--------- removing entries from the log ---------#

    def remove(self, date, mark):
        """ Remove specific entry from the log """
        all_entries = self.all_entries()
        with self.path.open("wb") as f:
            for e in all_entries:
                if not (e.date == date and e.mark == mark):
                    f.write(e.to_bytes())

    def remove_several(self, predicate, before=None, after=None):
        """ Remove all entries such that predicate(entry) is True """
        all_entries = self.all_entries()
        with self.path.open("wb") as f:
            for e in all_entries:
                if not (predicate(e) and before_after(e, before, after)):
                    f.write(e.to_bytes())

    #--------- querying entries in bulk ---------#

    def filter_entries(self, predicate, before=None, after=None):
        """ Return a list of entries such that predicate(entry) is True """
        res = []
        with self.path.open("rb") as f:
            while True:
                try:
                    new = entry.Entry.from_binary_file(f)
                    if predicate(new) and before_after(new, before, after):
                        res.append(new)
                except entry.EntryReadError:
                    return res

    def all_entries(self, before=None, after=None):
        """ Return all the entries in the log """
        return self.filter_entries(lambda e: True, before, after)

    def matching_entries(self, date, mark, before=None, after=None):
        """ Return a list of entries with given date and mark """
        return self.filter_entries(lambda e: e.date == date and e.mark == mark,
                before, after)

    def span(self, predicate):
        """
        Split the log in two lists. First will contain the entries from the
        latest to the first for which predicate(entry) is False, the second
        will contain the rest.

        It is analogous to the 'span' function from Haskell's Prelude.
        """
        i = 0
        all_entries = self.all_entries()
        for e in all_entries:
            if predicate(e):
                i += 1
            else:
                break
        return all_entries[:i], all_entries[i:]

    def grep(self, regex, before=None, after=None):
        """ Return all entries matching given regex """
        res = []
        for e in self.all_entries():
            if not before_after(e, before, after): continue
            lines = e.contents.splitlines()
            single_line = " ".join(lines)
            if regex.match(single_line):
                res.append(e)
            else:
                for line in lines:
                    if regex.match(line):
                        res.append(e)
                        break
        return res

    def grep_marked(self, regex, mark, before=None, after=None):
        """ Return all entries with given mark matching given regex """
        return list(filter(lambda e: e.mark == mark, self.grep(regex, before, after)))

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

    def last_entry(self):
        """ Return the latest entry, or None if the log is empty """
        with self.path.open("rb") as f:
            try:
                return entry.Entry.from_binary_file(f)
            except entry.EntryReadError:
                return None

#--------- helper functions ---------#

def before_after(en, before, after):
    """ Return True if the entry was made before given date or after given date """
    if before is None and after is None:
        return True
    if before is not None and en.date < before:
        return True
    if after is not None and en.date > after:
        return True
    return False
