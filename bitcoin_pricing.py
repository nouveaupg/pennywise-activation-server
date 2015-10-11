# bitcoin_pricing Module
#
# Retrieves and tracks bitcoin prices from bitcoincharts.com API
#
# Depends on the following table, be sure to check the limits of
# serial data type and DECIMAL precision when adding many/esoteric
# currencies.
#
# CREATE TABLE bitcoin_pricing (
#   serial MEDIUMINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
#   trailing_24hour_avg DECIMAL(7,2) NOT NULL,
#   currency_symbol CHAR(3),
#   timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

# Bitcoin pricing API endpoint
API_ENDPOINT = "http://api.bitcoincharts.com/v1/weighted_prices.json"
# amount of time between API fetches
API_REQUEST_PERIOD = 900

SUPPORTED_CURRENCIES = ["USD"]

# MySQL credentials
PRICING_DB_HOST = "localhost"
PRICING_DB_NAME = "activation"
PRICING_DB_USER = "root"
PRICING_DB_PASSWD = ""

import urllib2
import json
import sys
import logging
import datetime
import MySQLdb
from decimal import *

LOG_CHANNEL = "bitcoin_pricing"
LOG_FILE = "activation_errors.log"
LOG_FILE_LEVEL = logging.ERROR

class BitcoinPricing:
    def __init__(self,screenLogHandler=None,logFile=None):
        # set up logging
        self.logger = logging.getLogger(LOG_CHANNEL)
        self.logger.setLevel(logging.DEBUG)
        fh = None
        if logFile:
            fh = logging.FileHandler(LOG_FILE)
        else:
            fh = logging.FileHandler(LOG_FILE)
        if fh:
            fh.setLevel(LOG_FILE_LEVEL)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        if screenLogHandler:
            self.logger.addHandler(screenLogHandler)
        # try connecting to the database, seeing if we need to fetch data
        # we are only allowed one request to the API every 15 minutes
        try:
            self.conn = MySQLdb.connect(PRICING_DB_HOST,
                                user=PRICING_DB_USER,
                                passwd=PRICING_DB_PASSWD,
                                db=PRICING_DB_NAME)
            self.logger.debug("Connected to Bitcoin pricing database.")
            x = self.conn.cursor()
            x.execute("SELECT (timestamp) FROM bitcoin_pricing ORDER BY serial DESC LIMIT 1;")
            row = x.fetchone()
            if row:
                time_delta = datetime.datetime.now() - row[0]
                elapsed_seconds = int(time_delta.total_seconds())
                if elapsed_seconds > API_REQUEST_PERIOD:
                    self.logger.debug(str(elapsed_seconds) + " seconds since last fetch, starting new API request.")
                    self.fetch_bitcoin_pricing()
                else:
                    self.logger.debug("Bitcoin pricing database is current.")
            else:
                self.logger.debug("No pricing records found, starting new API request.")
                self.fetch_bitcoin_pricing()

        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return None

    def test(self):
        self.logger.info("Testing pricing for SUPPORTED_CURRENCIES: " + str(SUPPORTED_CURRENCIES))
        self.logger.info("API Endpoint: " + API_ENDPOINT)
        failure = False
        for each in SUPPORTED_CURRENCIES:
            avg = self.get24hourAvgForCurrency(each)
            if avg:
                self.logger.info(each + ": " + str(avg) + " (24 hour avg)")
            else:
                self.logger.error("Could not get price for " + each)
                failure = True
        if failure:
            self.logger.error("Could not get pricing data for one or more supported currencies. Check your configuration!")
            return False
        else:
            self.logger.info("Successfully retrieved pricing data for each supported currency.")
            return True

    def get24hourAvgForCurrency(self,currency):
        if currency not in SUPPORTED_CURRENCIES:
            self.logger.error("Requesting price for unsupported currency (%s). Check your configuration!" % currency)
            return None
        try:
            x = self.conn.cursor()
            x.execute("SELECT * FROM bitcoin_pricing WHERE currency_symbol='%s' ORDER BY serial DESC LIMIT 1;" % currency)
            row = x.fetchone()
            time_delta = datetime.datetime.now() - row[3]
            elapsed_seconds = int(time_delta.total_seconds())
            if elapsed_seconds < API_REQUEST_PERIOD:
                self.logger.debug("Found price of " + str(row[1]) + " for " + currency + " from " + str(elapsed_seconds) + " seconds ago.")
                return row[1]
            else:
                self.fetch_bitcoin_pricing()
                x.execute("SELECT * FROM bitcoin_pricing WHERE currency_symbol='%s' ORDER BY serial DESC LIMIT 1;" % currency)
                row = x.fetchone()
                self.logger.debug("Fetched price of " + str(row[1]) + " for " + currency + " from API server.")
                return row[1]

        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return None

    def fetch_bitcoin_pricing(self):
        try:
            self.logger.debug("Requesting pricing data from API endpoint: " + API_ENDPOINT)
            json_data = urllib2.urlopen(API_ENDPOINT)
            self.logger.debug("Received response from API server.")
            decoded_data = json.load(json_data)
            for each in SUPPORTED_CURRENCIES:
                avg = decoded_data[each]['24h']
                self.logger.debug("24 hour average for " + each + ": " + avg)
                sql = """INSERT INTO bitcoin_pricing (trailing_24hour_avg,
                                                            currency_symbol)
                                                            VALUES (%s,'%s')""" % (avg,each)
                self.logger.debug("Executing SQL: " + sql)
                x = self.conn.cursor()
                x.execute(sql)
                self.conn.commit()
            return True
        except urllib2.URLError as e:
            self.logger.error("URLLib2 raised exception: %s",str(e.reason))
            return False
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return False
        except:
            self.logger.error("fetch_bitcoin_pricing exception: " + str(sys.exc_info()[0]))
            return False

if __name__ == "__main__":
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    ch.setFormatter(formatter)

    pricing = BitcoinPricing(ch)
    pricing.test()
