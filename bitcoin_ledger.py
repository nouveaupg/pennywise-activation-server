# bitcoin_ledger Module
#
# Keeps track of paid and pending bitcoin payments
#
# Depends on the following tables
#
# CREATE TABLE bitcoin_ledger (ledger_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
#   uuid CHAR(36) NOT NULL,
#   email VARCHAR(65),
#   bitcoin_address VARCHAR(35) NOT NULL,
#   bitcoin_confirmations INT UNSIGNED DEFAULT 0,
#   bitcoin_balance DOUBLE DEFAULT 0,
#   price_paid DOUBLE DEFAULT NULL,
#   refund_paid UNSIGNED INT DEFAULT NULL,
#   refund_address VARCHAR(35),
#   activation_signature INT unsigned,
#   created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#   paid TIMESTAMP,
#   refunded TIMESTAMP,
#   UNIQUE(uuid));
#
# CREATE TABLE refunds (refund_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
#   refund_btc_address VARCHAR(35) NOT NULL,
#   refund_tx_confirmations INT UNSIGNED DEFAULT 0,
#   refund_value_int64 BIGINT UNSIGNED NOT NULL,
#   refund_btc_tx_id VARCHAR(55) DEFAULT NULL,
#   refund_type ENUM("automatic","manual"),
#   refund_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

# MySQL credentials
LEDGER_DB_HOST = "localhost"
LEDGER_DB_NAME = "ledger_test"
LEDGER_DB_USER = "root"
LEDGER_DB_PASSWD = ""

import sys
import logging
import datetime
import MySQLdb

LOG_CHANNEL = "bitcoin_ledger"
LOG_FILE = "activation_errors.log"
LOG_FILE_LEVEL = logging.DEBUG

class BitcoinLedger:
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
            self.logger.debug("Connected to Bitcoin ledger database.")

        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return None

    def createLedgerRecord(self,uuid,bitcoinAddr,emailAddr=None):
        if uuid == None or bitcoinAddr == None:
            self.logger.error("Could not create bitcoin ledger record: missing uuid or bitcoin address")
            return None
        if emailAddr:
            sql = """INSERT INTO bitcoin_ledger (uuid,email,bitcoin_address)
                                    VALUES ('%s','%s','%s')""" % (uuid,emailAddr,bitcoinAddr)
        else:
            sql = """INSERT INTO bitcoin_ledger (uuid,bitcoin_address)
                                    VALUES ('%s','%s')""" % (uuid,bitcoinAddr)
        self.logger.debug("Executing SQL: " + sql)
        try:
            x = self.conn.cursor()
            x.execute(sql)
            last_row_id = x.lastrowid
            self.conn.commit()
            return last_row_id
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return None

    def getLedgerRecord(self,ledgerId=None,uuid=None,bitcoinAddr=None):
        sql = """SELECT ledger_id,
                        bitcoin_ledger.uuid,
                        email,
                        bitcoin_address,
                        bitcoin_confirmations,
                        bitcoin_balance,
                        price_paid,
                        refund_paid,
                        refund_address,
                        activation.signature,
                        bitcoin_ledger.created,
                        paid,
                        refunded
                FROM bitcoin_ledger
                LEFT JOIN activation
                ON bitcoin_ledger.activation_signature=activation.activation_id"""
        if ledgerId:
            sql += " WHERE bitcoin_ledger.ledger_id=%d;" % ledgerId
        elif uuid:
            sql += " WHERE bitcoin_ledger.uuid='%s';" % uuid
        elif bitcoinAddr:
            sql += " WHERE bitcoin_ledger.bitcoin_address='%s';" % bitcoinAddr
        else:
            sql = None

        if sql:
            try:
                x = self.conn.cursor()
                x.execute(sql)
                row = x.fetchone()
                if row:
                    return {"id":row[0],
                            "uuid":row[1],
                            "emailAddress":row[2],
                            "bitcoinAddress":row[3],
                            "bitcoinConfirmations":row[4],
                            "bitcoinBalance":row[5],
                            "pricePaid":row[6],
                            "refundPaid":row[7],
                            "refundAddress":row[8],
                            "activationSignature":row[9],
                            "dateCreated":row[10],
                            "datePaid":row[11],
                            "dateRefunded":row[12]}
                else:
                    return None
            except MySQLdb.Error as e:
                self.logger.error("MySQLdb raised exception: %s",str(e))
                return None
        else:
            self.logger.error("getLedgerRecord failed: no arguments")
            return None

    def latestRecords(self,offset,count):
        sql = """SELECT ledger_id,
                        uuid,
                        email,
                        bitcoin_address,
                        bitcoin_confirmations,
                        bitcoin_balance,
                        price_paid,
                        refund_paid,
                        refund_address,
                        activation_signature,
                        created,
                        paid,
                        refunded FROM bitcoin_ledger ORDER BY ledger_id DESC
                        LIMIT %d OFFSET %d;""" % (count,offset)
        try:
            x = self.conn.cursor()
            self.logger.debug("Executing SQL: " + sql)
            x.execute(sql)
            results = []
            for row in x:
                each_record = {"id":row[0],
                        "uuid":row[1],
                        "emailAddress":row[2],
                        "bitcoinAddress":row[3],
                        "bitcoinConfirmations":row[4],
                        "bitcoinBalance":row[5],
                        "pricePaid":row[6],
                        "refundPaid":row[7],
                        "refundAddress":row[8],
                        "activationSignature":row[9],
                        "dateCreated":row[10],
                        "datePaid":row[11],
                        "dateRefunded":row[12]}
                results.append(each_record)
            return results
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return None

    def getStatistics(self):
        # some fancy sql
        sql = """SELECT COUNT(*),
                    sum(case when price_paid is not null then 1 else 0 end) paid,
                    sum(case when refund_paid is not null then 1 else 0 end) refunded
                    FROM bitcoin_ledger;"""
        try:
            x = self.conn.cursor()
            self.logger.debug("Executing SQL: " + sql)
            x.execute(sql)
            row = x.fetchone()
            if row:
                return {"total":int(row[0]),"paid":int(row[1]),"refunded":int(row[2])}
            else:
                self.logger.error("BitcoinLedger.getStatistics SQL failed")
                return None
        except TypeError:
            return {"total":0, "paid":0, "refunded":0}
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return None

    def retrieveUnpaid(self):
        # returns object containing bitcoin_addr => ledger_id mapping
        sql = "SELECT bitcoin_address,ledger_id FROM bitcoin_ledger WHERE price_paid IS NULL ORDER BY ledger_id DESC;"

        try:
            x = self.conn.cursor()
            self.logger.debug("Executing SQL: " + sql)
            x.execute(sql)
            results = {}
            for row in x:
                results[row[0]] = row[1]
            return results
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return None

    def retrieveUnrefunded(self):
        # returns list of unrefunded ledger objects
        sql = """SELECT bitcoin_address,
                        ledger_id
                        FROM bitcoin_ledger
                        WHERE refund_paid IS NULL AND price_paid IS NOT NULL
                        ORDER BY ledger_id DESC;"""

        try:
            x = self.conn.cursor()
            self.logger.debug("Executing SQL: " + sql)
            x.execute(sql)
            results = {}
            for row in x:
                results[row[0]] = row[1]
            return results
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return None

    def setActivationSignatureId(self,ledgerId,activationId):
        try:
            x = self.conn.cursor()
            if activationId:
                sql = "UPDATE bitcoin_ledger SET activation_signature=%d WHERE ledger_id=%d;" % (activationId,ledgerId)
            else:
                sql = "UPDATE bitcoin_ledger SET activation_signature=NULL WHERE ledger_id=%d;" % (ledgerId)
            self.logger.debug("Executing SQL: " + sql)
            x.execute(sql)
            self.conn.commit()
            return True
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return False
        return False

    def setRefundAddress(self,ledgerId,refundAddr):
        try:
            x = self.conn.cursor()
            sql = "UPDATE bitcoin_ledger SET refund_address='%s' WHERE ledger_id=%d;" % (refundAddr,ledgerId)
            self.logger.debug("Executing SQL: " + sql)
            x.execute(sql)
            self.conn.commit()
            return True
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return False
        return False

    def setBalance(self,ledgerId,balance,confirmations):
        try:
            x = self.conn.cursor()
            sql = "UPDATE bitcoin_ledger SET bitcoin_balance=%F,bitcoin_confirmations=%d WHERE ledger_id=%d;" % (balance,confirmations,ledgerId)
            self.logger.debug("Executing SQL: " + sql)
            x.execute(sql)
            self.conn.commit()
            return True
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return False
        return False

    def setEmailAddress(self,ledgerId,emailAddr):
        try:
            x = self.conn.cursor()
            sql = "UPDATE bitcoin_ledger SET email_address='%s' WHERE ledger_id=%d;" % (emailAddr,ledgerId)
            self.logger.debug("Executing SQL: " + sql)
            x.execute(sql)
            self.conn.commit()
            return True
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return False
        return False

    def markPaid(self,ledgerId,bitcoinPaid):
        # if you want to place a confirmation limit
        #
        # ledger_record = self.getLedgerRecord(ledgerId)
        # if ledger_record['bitcoin_confirmations'] < CONFIRMATION_LIMIT:
        #   return False
        try:
            x = self.conn.cursor()
            sql = "UPDATE bitcoin_ledger SET price_paid=%f,paid=NOW() WHERE ledger_id=%d;" % (bitcoinPaid,ledgerId)
            self.logger.debug("Executing SQL: " + sql)
            x.execute(sql)
            self.conn.commit()
            return True
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return False
        return False

    def markRefunded(self,ledgerId,bitcoinRefunded):
        try:
            x = self.conn.cursor()
            sql = "UPDATE bitcoin_ledger SET refund_paid=%f,refunded=NOW() WHERE ledger_id=%d;" % (bitcoinRefunded,ledgerId)
            self.logger.debug("Executing SQL: " + sql)
            x.execute(sql)
            self.conn.commit()
            return True
        except MySQLdb.Error as e:
            self.logger.error("MySQLdb raised exception: %s",str(e))
            return False
        return False

if __name__ == "__main__":
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    ch.setFormatter(formatter)

    ledger = BitcoinLedger(ch)
    if ledger:
        totals = ledger.getStatistics()
        print "Connected to Bitcoin ledger (%d total records, %d paid, %d refunded)" % (totals["total"],totals["paid"],totals["refunded"])
