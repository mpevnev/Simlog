""" This module contains a class for configuration of the logger. """

import datetime
import os
import pathlib
import re
import subprocess

import entry
import logfile

#--------- main class ---------#

class Logger():
    """ Main processing class """

    def __init__(self, args):
        try:
            self.editor = os.environ["EDITOR"]
        except KeyError:
            print("The logger requires EDITOR environment variable to be set.")
            raise ConfigError()
        self.logdir = pathlib.Path.home() / ".simlog"
        self.logfile = logfile.Logfile(self.logdir / "log")
        self.entryfile = self.logdir / "entry"
        self.command = args.command
        self.mark = args.mark
        self.reverse = args.reverse
        # parse '--date'
        if args.date is None:
            self.date = datetime.date.today()
        else:
            self.date = parse_date(args.date)
            if self.date is None:
                print(INVALID_DATE)
                raise ConfigError()
        # compile regex if it is given
        try:
            self.regex = re.compile(".*" + args.regex + ".*")
        except re.error as e:
            print(f"Error when parsing regex: {e.args[0]}.")
            raise ConfigError()
        except AttributeError:
            pass # if there's no regex field then we simply don't need it
        # parse '--before' and '--after'
        self.before, self.after = None, None
        if args.before is not None:
            self.before = parse_date(args.before)
            if self.before is None:
                print(INVALID_DATE)
                raise ConfigError()
        if args.after is not None:
            self.after = parse_date(args.after)
            if self.after is None:
                print(INVALID_DATE)
                raise ConfigError()

    def ensure_files(self):
        """
        Make sure all required directories and files are in required condition
        """
        if not self.logdir.exists():
            self.logdir.mkdir()
        self.logfile.ensure_existence()
        if self.entryfile.exists():
            os.remove(self.entryfile)

    #--------- central processing function ---------#

    def run(self):
        """ Run the specified command """
        if self.command == "add":
            self.add(self.date, self.mark)
        elif self.command == "view":
            self.view_specific(self.date, self.mark)
        elif self.command == "view-marked":
            self.view_marked(self.mark)
        elif self.command == "remove":
            self.remove_specific(self.date, self.mark)
        elif self.command == "remove-marked":
            self.remove_marked(self.mark)
        elif self.command == "view-all":
            self.view_all()
        elif self.command == "grep":
            self.grep(self.regex)
        elif self.command == "grep-marked":
            self.grep_marked(self.regex, self.mark)

    #--------- commands ---------#

    def add(self, date, mark):
        """ Add an entry to the log """
        try:
            subprocess.run([self.editor, str(self.entryfile)])
        except FileNotFoundError:
            print(f"EDITOR is set to '{self.editor}', which doesn't appear to be"
                + " a valid command.")
            raise ConfigError()
        if not self.entryfile.exists():
            raise NoEntryError()
        date = date or datetime.date.today()
        en = entry.Entry.from_text_file(self.entryfile, date, mark)
        old_entry = self.logfile.find_specific(date, mark)
        if old_entry is not None:
            old_entry.merge(en)
            self.logfile.replace(old_entry)
        else:
            last = self.logfile.last_entry()
            if last is None or last < en:
                # the entry needs to be put in the head of the log
                self.logfile.prepend(en)
            else:
                # the entry needs to be inserted between old entries
                self.logfile.insert_by_date(en)

        os.remove(self.entryfile)

    def view_specific(self, date, mark):
        """ View an entry with given mark and date """
        en = self.logfile.find_specific(date, mark)
        if en is not None:
            print(en, "\n")
        else:
            if mark != "":
                print(f"There are no entries with mark '{mark}' made on {date}.")
            else:
                print(f"There are no entries with no mark made on {date}.")

    def view_marked(self, mark):
        """ View all entries with the given mark """
        entries = self.logfile.filter_entries(lambda e: e.mark == mark,
                self.before, self.after)
        empty = True
        if self.reverse:
            entries = list(entries)
            entries.reverse()
        for e in entries:
            print(e)
            empty = False
        if empty:
            if mark == "":
                res = f"There are no unmarked entries"
            else:
                res = f"There are no entries with mark {mark}"
            if self.before is not None:
                date = self.before.strftime("%Y %b %d")
                res += f" made before {date}"
                if self.after is not None:
                    date = self.after.strftime("%Y %b %d")
                    res += f" and after {date}"
            else:
                if self.after is not None:
                    date = self.after.strftime("%Y %b %d")
                    res += f" made after {date}"
            res += " in the log."
            print(res)

    def view_all(self):
        """ View all entries """
        entries = self.logfile.all_entries(self.before, self.after)
        empty = True
        if self.reverse:
            entries = list(entries)
            entries.reverse()
        for e in entries:
            print(e)
            empty = False
        if empty:
            if self.before is None and self.after is None:
                print("The log is empty")
            elif self.before is not None and self.after is None:
                date = self.before.strftime("%Y %b %d")
                print(f"There are no entries made before {date}.")
            elif self.after is not None and self.before is None:
                date = self.after.strftime("%Y %b %d")
                print(f"There are no entries made after {date}.")
            else:
                date1 = self.before.strftime("%Y %b %d")
                date2 = self.after.strftime("%Y %b %d")
                print(f"There are no entries made before {date1} and after {date2}.")

    def remove_specific(self, date, mark):
        """ Remove an entry with given mark and date """
        self.logfile.remove(date, mark)

    def remove_marked(self, mark):
        """ Remove all entries with given mark """
        self.logfile.remove_several(lambda e: e.mark == mark,
                self.before, self.after)

    def grep(self, regex):
        """ View all entries matching given regex """
        entries = self.logfile.grep(regex, self.before, self.after)
        empty = True
        if self.reverse:
            entries = list(entries)
            entries.reverse()
        for e in entries:
            print(e)
            empty = False
        if empty:
            if self.before is None and self.after is None:
                print("There are no entries matching this regular expression.")
            elif self.before is not None and self.after is None:
                date = self.before.strftime("%Y %b %d")
                print(f"No entry made before {date} matches this regex.")
            elif self.after is not None and self.before is None:
                date = self.after.strftime("%Y %b %d")
                print(f"No entry made after {date} matches this regex.")
            else:
                date1 = self.before.strftime("%Y %b %d")
                date2 = self.after.strftime("%Y %b %d")
                print(f"No entry made before {date1} and after {date2} matches this regex.")

    def grep_marked(self, regex, mark):
        """ View all entries with given mark matching given regex """
        entries = self.logfile.grep_marked(regex, mark)
        empty = True
        if self.reverse:
            entries = list(entries)
            entries.reverse()
        for e in entries:
            print(e)
            empty = False
        if empty:
            if self.before is None and self.after is None:
                print(f"No entry with mark {mark} matches this regular expression.")
            elif self.before is not None and self.after is None:
                date = self.before.strftime("%Y %b %d")
                print(f"No entry with mark {mark} made before {date} matches this regex.")
            elif self.after is not None and self.before is None:
                date = self.after.strftime("%Y %b %d")
                print(f"No entry with mark {mark} made after {date} matches this regex.")
            else:
                date1 = self.before.strftime("%Y %b %d")
                date2 = self.after.strftime("%Y %b %d")
                print(f"No entry with mark {mark} made before {date1} and after {date2} \
                        matches this regex.")

#--------- helper functions ---------#

def parse_date(string):
    """ Return a date object from a given string, or None if parsing failed """
    formats = ["%Y-%m-%d"
              , "%Y %m %d"
              , "%Y-%b-%d"
              , "%Y %b %d"
              ]
    for f in formats:
        try:
            return datetime.datetime.strptime(string, f).date()
        except ValueError:
            pass
    return None

#--------- errors ---------#

class ConfigError(Exception):
    """ An error raised when an invalid configuration is read """
    pass

class NoEntryError(Exception):
    """ An error raised if no 'entry' file was created by calling EDITOR """
    pass

#--------- strings ---------#

INVALID_DATE = "Invalid date format. Please see 'simlog -h' for a list of valid date formats."
