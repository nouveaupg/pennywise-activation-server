# activation Module
#
# Handles the generation and storage of activation signatures. Depends on
# table below

# CREATE TABLE activation (activation_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
#                            uuid CHAR(36) NOT NULL,
#                            signature TEXT,
#                            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                            UNIQUE(uuid));

import logging
import datetime
import MySQLdb

LOG_CHANNEL = "activation"
LOG_FILE = "activation_errors.log"
LOG_FILE_LEVEL = logging.ERROR

ACTIVATION_DB_HOST = "localhost"
ACTIVATION_NAME = "activation"
ACTIVATION_USER = "root"
ACTIVATION_PASSWD = ""

class ActivationSignatureGenerator:
    def __init__(self,screenLogHandler=None):
        # set up logging
        self.logger = logging.getLogger('activation')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(LOG_FILE)
        fh.setLevel(LOG_FILE_LEVEL)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        if screenLogHandler:
            self.logger.addHandler(screenLogHandler)
        # try connecting to the database
        try:
            self.conn = MySQLdb.connect(LEDGER_DB_HOST,
                                user=LEDGER_DB_USER,
                                passwd=LEDGER_DB_PASSWD,
                                db=LEDGER_DB_NAME)
            self.logger.debug("Connected to activation signature database.")

        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return None

    def sign(self,uuid):
        try:
