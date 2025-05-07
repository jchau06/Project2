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
from p2app import events


class Engine:
    """An object that represents the application's engine, whose main role is to
    process events sent to it by the user interface, then generate events that are
    sent back to the user interface in response, allowing the user interface to be
    unaware of any details of how the engine is implemented.
    """

    def __init__(self):
        """Initializes the engine"""
        self._connection = None
        self._handlers = {
            # Application-level functions
            events.OpenDatabaseEvent: self._handle_open_database,
            events.CloseDatabaseEvent: self._handle_close_database,
            events.QuitInitiatedEvent: self._handle_quit_application,

            # Continent-related functions
            events.StartContinentSearchEvent: self._handle_search_continent,
            events.LoadContinentEvent: self._handle_load_continent,
            events.SaveNewContinentEvent: self._handle_save_new_continent,
            events.SaveContinentEvent: self._handle_save_continent,

            # Country-related functions
            events.StartCountrySearchEvent: self._handle_search_country,
            events.LoadCountryEvent: self._handle_load_country,
            events.SaveNewCountryEvent: self._handle_save_new_country,
            events.SaveCountryEvent: self._handle_save_country,

            # Region-related functions
            events.StartRegionSearchEvent: self._handle_search_region,
            events.LoadRegionEvent: self._handle_load_region,
            events.SaveNewRegionEvent: self._handle_save_new_region,
            events.SaveRegionEvent: self._handle_save_region
        }


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

            yield events.DatabaseOpenedEvent(event.path())

        except sqlite3.DatabaseError:
            if self._connection:
                self._connection.close()
                self._connection = None
            yield events.DatabaseOpenFailedEvent(f"The file is not a valid SQLite database")
        except Exception as e:
            if self._connection:
                self._connection.close()
                self._connection = None
            yield events.DatabaseOpenFailedEvent(f"An unexpected error occurred: {e}")

    def _handle_close_database(self, event):
        if self._connection:
            self._connection.close()
            self._connection = None
        yield events.DatabaseClosedEvent()

    def _handle_quit_application(self, event):
        yield events.EndApplicationEvent()

    def _handle_search_continent(self, event):
        if self._connection is None:
            return

        try:
            input_code = (event.continent_code() or '').strip()
            input_name = (event.name() or '').strip()

            if not input_code and not input_name:
                # Possibly raise exception.
                yield events.ErrorEvent(f"No continent code or continent name has been provided.")
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

            rows = cursor.fetchall()
            if not rows:
                yield events.ErrorEvent(f"No continents have been found.")
                return

            for row in rows:
                continent = events.Continent(*row)
                yield events.ContinentSearchResultEvent(continent)

        except Exception as e:
            yield events.ErrorEvent(f"Cannot search continent due to an unexpected error - {e}")
            return

    def _handle_load_continent(self, event):
        try:
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
                continent = events.Continent(*row)
                yield events.ContinentLoadedEvent(continent)
        except Exception as e:
            yield events.ErrorEvent(f"Failed to load continent due to an unexpected error - {e}")


    def _handle_save_new_continent(self, event):
        try:
            continent = event.continent()
            cursor = self._connection.cursor()
            query = '''
                    INSERT INTO continent (continent_id, continent_code, name) VALUES (?, ?, ?)
                    '''
            cursor.execute(query, [continent.continent_id, continent.continent_code, continent.name])
            self._connection.commit()
            yield events.ContinentSavedEvent(continent)
        except Exception as e:
            yield events.SaveContinentFailedEvent(f"Could not save new continent because of an error - {e}")

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
            yield events.ContinentSavedEvent(continent)
        except Exception as e:
            yield events.SaveContinentFailedEvent(f"Could not update continent because of an error - {e}")

    def _handle_search_country(self, event):
        if self._connection is None:
            return

        try:
            input_code = (event.country_code() or '').strip()
            input_name = (event.name() or '').strip()

            if not input_code and not input_name:
                yield events.ErrorEvent(f"No country code or country name has been provided.")
                return

            query = '''
                    SELECT country_id, country_code, name, continent_id, wikipedia_link, keywords
                    FROM country
                    WHERE TRUE
                    '''

            params = []
            if input_code:
                query += ' AND country_code = ? '
                params.append(input_code)

            if input_name:
                query += ' AND name = ? '
                params.append(input_name)

            cursor = self._connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            if not rows:
                yield events.ErrorEvent(f"No countries have been found.")
                return

            for row in rows:
                country = events.Country(*row)
                yield events.CountrySearchResultEvent(country)

        except Exception as e:
            yield events.ErrorEvent(f"Failed to search country due to an unexpected error - {e}")
            return

    def _handle_load_country(self, event):
        try:
            country_id = event.country_id()
            cursor = self._connection.cursor()
            query = '''
                    SELECT country_id, country_code, name, continent_id, wikipedia_link, keywords
                    FROM country
                    WHERE country_id = ?
                    '''

            cursor.execute(query, [country_id])
            row = cursor.fetchone()
            if row:
                country = events.Country(*row)
                yield events.CountryLoadedEvent(country)
        except Exception as e:
            yield events.ErrorEvent(f"Failed to load country due to an unexpected error - {e}")


    def _handle_save_new_country(self, event):
        try:
            country = event.country()
            cursor = self._connection.cursor()
            query = '''
                    INSERT INTO country (country_id, country_code, name, continent_id, wikipedia_link, keywords) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    '''
            cursor.execute(query,
                           [country.country_id,
                            country.country_code,
                            country.name,
                            country.continent_id,
                            country.wikipedia_link,
                            country.keywords if country.keywords else None])
            self._connection.commit()
            yield events.CountrySavedEvent(country)
        except Exception as e:
            yield events.SaveCountryFailedEvent(
                f"Could not save new country because of an error - {e}")

    def _handle_save_country(self, event):
        try:
            country = event.country()
            cursor = self._connection.cursor()
            query = '''
                    UPDATE country 
                    SET name = ?, country_code = ?, continent_id = ?, wikipedia_link = ?, keywords = ?
                    WHERE country_id = ?
                    '''
            cursor.execute(query,
                           [country.name,
                            country.country_code,
                            country.continent_id,
                            country.wikipedia_link,
                            country.keywords if country.keywords else None,
                            country.country_id])
            self._connection.commit()
            yield events.CountrySavedEvent(country)
        except Exception as e:
            yield events.SaveCountryFailedEvent(f"Could not update country because of an error - {e}")

    def _handle_search_region(self, event):
        if self._connection is None:
            return

        try:
            input_region_code = (event.region_code() or '').strip()
            input_local_code = (event.local_code() or '').strip()
            input_name = (event.name() or '').strip()

            if not input_region_code and not input_local_code  and not input_name:
                yield events.ErrorEvent(f"No region code, local code, or region name has been provided.")
                return

            query = '''
                    SELECT region_id, region_code, local_code, name, continent_id, country_id, wikipedia_link, keywords
                    FROM region
                    WHERE TRUE
                    '''

            params = []
            if input_region_code:
                query += ' AND region_code = ? '
                params.append(input_region_code)

            if input_local_code:
                query += ' AND local_code = ? '
                params.append(input_local_code)

            if input_name:
                query += ' AND name = ? '
                params.append(input_name)

            cursor = self._connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            if not rows:
                yield events.ErrorEvent(f"No regions have been found.")
                return

            for row in rows:
                region = events.Region(*row)
                yield events.RegionSearchResultEvent(region)

        except Exception as e:
            yield events.ErrorEvent(f"Failed to search region due to an unexpected error - {e}")
            return

    def _handle_load_region(self, event):
        try:
            region_id = event.region_id()
            cursor = self._connection.cursor()
            query = '''
                    SELECT region_id, region_code, local_code, name, continent_id, country_id, wikipedia_link, keywords
                    FROM region
                    WHERE region_id = ?
                    '''

            cursor.execute(query, [region_id])
            row = cursor.fetchone()
            if row:
                region = events.Region(*row)
                yield events.RegionLoadedEvent(region)
        except Exception as e:
            yield events.ErrorEvent(f"Failed to load region due to an unexpected error - {e}")


    def _handle_save_new_region(self, event):
        try:
            region = event.region()
            cursor = self._connection.cursor()
            query = '''
                    INSERT INTO region (region_id, region_code, local_code, name, continent_id, country_id, wikipedia_link, keywords) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    '''
            cursor.execute(query,
                           [region.region_id,
                            region.region_code,
                            region.local_code,
                            region.name,
                            region.continent_id,
                            region.country_id,
                            region.wikipedia_link,
                            region.keywords if region.keywords else None])
            self._connection.commit()
            yield events.RegionSavedEvent(region)
        except Exception as e:
            yield events.SaveRegionFailedEvent(
                f"Could not save new region because of an error - {e}")

    def _handle_save_region(self, event):
        try:
            region = event.region()
            cursor = self._connection.cursor()
            query = '''
                    UPDATE region 
                    SET region_code = ?, local_code = ?, name = ?, continent_id = ?, country_id = ?, wikipedia_link = ?, keywords = ?
                    WHERE region_id = ?
                    '''

            cursor.execute(query,
                           [region.region_code,
                            region.local_code,
                            region.name,
                            region.continent_id,
                            region.country_id,
                            region.wikipedia_link if region.wikipedia_link else None,
                            region.keywords if region.keywords else None,
                            region.region_id])
            self._connection.commit()
            yield events.RegionSavedEvent(region)
        except Exception as e:
            yield events.SaveRegionFailedEvent(f"Could not update region because of an error - {e}")

    def _handle_unrecognized(self, event):
            yield from ()
