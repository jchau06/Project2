# p2app/engine/main.py
#
# ICS 33 Spring 2025
# Project 2: Learning to Fly
#
# An object that represents the engine of the application.
#
# This is the outermost layer of the part of the program that you'll need to build,
# which means that YOU WILL DEFINITELY NEED TO MAKE CHANGES TO THIS FILE.
import sqlite3
from p2app.events import OpenDatabaseEvent, DatabaseOpenedEvent, DatabaseOpenFailedEvent, CloseDatabaseEvent, DatabaseClosedEvent, QuitInitiatedEvent, EndApplicationEvent


class Engine:
    """An object that represents the application's engine, whose main role is to
    process events sent to it by the user interface, then generate events that are
    sent back to the user interface in response, allowing the user interface to be
    unaware of any details of how the engine is implemented.
    """

    def __init__(self):
        """Initializes the engine"""
        self._connection = None
        self._handlers = {OpenDatabaseEvent: self._handle_open_database,
                          CloseDatabaseEvent: self._handle_close_database,
                          QuitInitiatedEvent: self._handle_quit_application}


    def process_event(self, event):
        """A generator function that processes one event sent from the user interface,
        yielding zero or more events in response."""

        # This is a way to write a generator function that always yields zero values.
        # You'll want to remove this and replace it with your own code, once you start
        # writing your engine, but this at least allows the program to run.
        handler = self._handlers.get(type(event), self._handle_unrecognized)
        yield from handler(event)

    def _handle_open_database(self, event):
        try:
            self._connection = sqlite3.connect(event.path())
            yield DatabaseOpenedEvent(event.path())
        except Exception as e:
            yield DatabaseOpenFailedEvent(str(e))

    def _handle_close_database(self, event):
        if self._connection:
            self._connection.close()
            self._connection = None
        yield DatabaseClosedEvent()

    def _handle_quit_application(self, event):
        yield EndApplicationEvent()

    def _handle_unrecognized(self, event):
        yield from ()