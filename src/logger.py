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
        self.logdir = pathlib.Path.home() / ".logger"
        self.logfile = logfile.Logfile(self.logdir / "log")
        self.entryfile = self.logdir / "entry"
        self.command = args.command
        self.args = args

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
        mark = self.args.mark
        if self.command == "add":
            self.add(mark=mark)
        elif self.command == "view":
            self.view_specific(mark=mark)

    #--------- specific commands ---------#

    def add(self, date=None, mark=""):
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
            self.logfile.prepend(en)

        os.remove(self.entryfile)

    def view_specific(self, date=None, mark=""):
        """ View an entry with given mark and date """
        date = date or datetime.date.today()
        en = self.logfile.find_specific(date, mark)
        if en is not None:
            print(en, "\n")
        else:
            print(f"There are no entries with mark '{mark}' made on {date}.")

#--------- errors ---------#

class ConfigError(Exception):
    """ An error raised when an invalid configuration is read """
    pass

class NoEntryError(Exception):
    """ An error raised if no 'entry' file was created by calling EDITOR """
    pass
