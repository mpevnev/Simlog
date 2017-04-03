#!/usr/bin/python

""" Main module """

import entry
import logger

import argparse

def build_parser():
    """ Construct a command line arguments' parser """
    parser = argparse.ArgumentParser("logger")
    parser.add_argument("--mark", dest="mark", 
            help="Operate only on entries with given mark",
            default="")
    subparsers = parser.add_subparsers(help="Available commands", dest="command")

    # 'add' command
    add_parser = subparsers.add_parser("add", help="Add an entry to the log")

    # 'view' command
    view_parser = subparsers.add_parser("view", help="View the log")

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
    except entry.EntryReadError:
        print("Entry read from the log is malformed, terminating.")

if __name__ == "__main__":
    main()
