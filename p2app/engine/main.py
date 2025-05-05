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
from p2app.events import (OpenDatabaseEvent, DatabaseOpenedEvent, DatabaseOpenFailedEvent, CloseDatabaseEvent,
                          DatabaseClosedEvent, QuitInitiatedEvent, EndApplicationEvent, StartContinentSearchEvent,
                          ContinentSearchResultEvent, Continent, LoadContinentEvent, ContinentLoadedEvent,
                          SaveNewContinentEvent, ContinentSavedEvent, SaveContinentFailedEvent, SaveContinentEvent)



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
                          QuitInitiatedEvent: self._handle_quit_application,
                          StartContinentSearchEvent: self._handle_search_continent,
                          LoadContinentEvent: self._handle_load_continent,
                          SaveNewContinentEvent: self._handle_save_new_continent,
                          SaveContinentEvent: self._handle_save_continent}


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

            # Test if the input file is a valid SQLite database, if simple query fails
            # yield a user-friendly error.
            cursor = self._connection.cursor()
            cursor.execute("PRAGMA schema_version;")
            cursor.fetchone()

            yield DatabaseOpenedEvent(event.path())

        except sqlite3.DatabaseError:
            if self._connection:
                self._connection.close()
                self._connection = None
            yield DatabaseOpenFailedEvent(f"The file is not a valid SQLite database")
        except Exception as e:
            if self._connection:
                self._connection.close()
                self._connection = None
            yield DatabaseOpenFailedEvent(f"An unexpected error occurred: {e}")

    def _handle_close_database(self, event):
        if self._connection:
            self._connection.close()
            self._connection = None
        yield DatabaseClosedEvent()

    def _handle_quit_application(self, event):
        yield EndApplicationEvent()

    def _handle_search_continent(self, event):
        if self._connection is None:
            return

        try:
            input_code = (event.continent_code() or '').strip()
            input_name = (event.name() or '').strip()

            if not input_code and not input_name:
                # Possibly raise exception.
                return

            query = '''
                SELECT continent_id, continent_code, name
                FROM continent
                WHERE TRUE
            '''

            params = []
            if input_code:
                query += ' AND continent_code = ? '
                params.append(input_code)

            if input_name:
                query += ' AND name = ? '
                params.append(input_name)

            cursor = self._connection.cursor()
            cursor.execute(query, params)

            for row in cursor.fetchall():
                continent = Continent(*row)
                yield ContinentSearchResultEvent(continent)

        except Exception as e:
            # update this.
            return

    def _handle_load_continent(self, event):
        continent_id = event.continent_id()
        cursor = self._connection.cursor()
        query = '''
        SELECT continent_id, continent_code, name
        FROM continent
        WHERE continent_id = ?
        '''

        cursor.execute(query, [continent_id])
        row = cursor.fetchone()
        if row:
            continent = Continent(*row)
            yield ContinentLoadedEvent(continent)

    def _handle_save_new_continent(self, event):
        try:
            continent = event.continent()
            cursor = self._connection.cursor()
            query = '''
            INSERT INTO continent (continent_id, continent_code, name) VALUES (?, ?, ?)
            '''
            cursor.execute(query, [continent.continent_id, continent.continent_code, continent.name])
            self._connection.commit()
            yield ContinentSavedEvent(continent)
        except Exception as e:
            yield SaveContinentFailedEvent(f"Could not save new continent because of an error - {e}")

    def _handle_save_continent(self, event):
        try:
            continent = event.continent()
            cursor = self._connection.cursor()
            query = '''
                    UPDATE continent 
                    SET name = ?, continent_code = ? 
                    WHERE continent_id = ?
                    '''
            cursor.execute(query,
                           [continent.name, continent.continent_code, continent.continent_id])
            self._connection.commit()
            yield ContinentSavedEvent(continent)
        except Exception as e:
            yield SaveContinentFailedEvent(f"Could not update continent because of an error - {e}")

    def _handle_unrecognized(self, event):
        yield from ()