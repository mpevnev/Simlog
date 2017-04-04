#!/usr/bin/python

""" Main module """

import entry
import logger

import argparse

def build_parser():
    """ Construct a command line arguments' parser """
    parser = argparse.ArgumentParser("simlog")
    parser.add_argument("-m", "--mark", dest="mark", 
        help="operate only on entries with given mark",
        default="")
    parser.add_argument("-d", "--date", dest="date",
        help="operate on entries with given date. Date can be in any of the \
            following formats: 'YYYY-MM-DD', 'YYYY MM DD', \
            'YYYY-Mon-DD', 'YYYY Mon DD'",
        default=None)
    subparsers = parser.add_subparsers(help="Available commands", dest="command")

    # 'add' command
    add_parser = subparsers.add_parser("add", help="Add an entry to the log")

    # 'view' command
    view_parser = subparsers.add_parser("view", help="View the log")

    # 'view-marked' command
    view_marked_parser = subparsers.add_parser("view-marked", 
        help="View all marked entries. '--mark' option is ignored")
    view_marked_parser.add_argument("mark")

    # 'view-all' command 
    view_all_parser = subparsers.add_parser("view-all",
        help="View all entries.")

    # 'remove' command
    remove_parser = subparsers.add_parser("remove", 
        help="Remove an entry with given date and mark")

    # 'remove-marked' command
    remove_marked_parser = subparsers.add_parser("remove-marked",
        help="Remove all the entries with given mark. '--mark' option is ignored")
    remove_marked_parser.add_argument("mark")

    # 'grep' command
    grep_parser = subparsers.add_parser("grep",
        help="View all entries matching given regular expression")
    grep_parser.add_argument("regex")

    # 'grep-marked' command
    grep_marked_parser = subparsers.add_parser("grep-marked",
        help="View all entries with given mark that match given regex. \
                '--mark' option is ignored")
    grep_marked_parser.add_argument("regex")
    grep_marked_parser.add_argument("mark")

    return parser

def main():
    """ Main """
    try:
        parser = build_parser()
        args = parser.parse_args()
        logg = logger.Logger(args)
        logg.ensure_files()
        logg.run()
    except logger.ConfigError:
        print("Invalid configuration detected, terminating.")
    except logger.NoEntryError:
        print("Entry file was not created, nothing will be added to the log.")

if __name__ == "__main__":
    main()
