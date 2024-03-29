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
import subprocess
import MySQLdb

LOG_CHANNEL = "activation"
LOG_FILE = "activation_errors.log"
LOG_FILE_LEVEL = logging.ERROR

LEDGER_DB_HOST = "localhost"
LEDGER_DB_USER = "root"
LEDGER_DB_PASSWD = ""
LEDGER_DB_NAME = "activation"

class ActivationSignatureGenerator:
    def __init__(self,screenLogHandler=None,logFile=None):
        # set up logging
        self.logger = logging.getLogger(LOG_CHANNEL)
        self.logger.setLevel(logging.DEBUG)
        fh = None
        if logFile == None:
            fh = logging.FileHandler(LOG_FILE)
        else:
            fh = logging.FileHandler(logFile)
        if fh:
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
            x = self.conn.cursor()
            x.execute("SELECT activation_id FROM activation WHERE uuid='%s';" % uuid)
            row = x.fetchone()
            if row:
                self.logger.error("Activation already exists for " + uuid)
                return False
            else:
                # call external process to sign uuid
                proc = subprocess.Popen(["/home/staging/SignUUID",uuid],stdout=subprocess.PIPE)
                activation_signature =  proc.stdout.read()
                if activation_signature:
                    sql = "INSERT INTO activation (uuid,signature) VALUES ('%s','%s')" % (uuid,activation_signature)
                    x.execute(sql)
                    self.logger.debug("Executing SQL: " + sql)
                    last_row = x.lastrowid
                    self.conn.commit()
                    return last_row
                else:
                    self.logger.error("No signature returned by external processs")
                    return None
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return None
        except e:
            self.logger.error("Signing failed: " + str(e))
            return None
