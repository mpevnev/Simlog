""" This module contains a class for configuration of the logger. """

import datetime
import os
import pathlib
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
        if args.date is None:
            self.date = datetime.date.today()
        else:
            self.date = parse_date(args.date)
            if self.date is None:
                print("Invalid date format. Please see 'simlog -h' for a list "
                        + "of valid date formats.")
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

    #--------- commands ---------#

    def add(self, date, mark):
        """ Add an entry to the log """
        subprocess.run([self.editor, str(self.entryfile)])
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
        entries = self.logfile.filter_entries(lambda e: e.mark == mark)
        if entries != []:
            for e in entries:
                print(e, "\n")
        else:
            if mark == "":
                print(f"There are no unmarked entries in the log.")
            else:
                print(f"There are no entries with mark {mark} in the log.")

    def remove_specific(self, date, mark):
        """ Remove an entry with given mark and date """
        self.logfile.remove(date, mark)

    def remove_marked(self, mark):
        """ Remove all entries with given mark """
        self.logfile.remove_several(lambda e: e.mark == mark)

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
