# core Module
#
# central dispatch for activation service
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import *
import logging
# Initalize modules
import bitcoin_pricing
import bitcoin_ledger
import activation

PRICE_IN_DOLLARS = 30
REFUND_CONFIRMS = 2

RPC_HOST = "aries"
RPC_PORT = 8332
RPC_USER = "bitcoinrpc"
RPC_PASSWD = "EsDt8nz5LhPdERzct5MwQJr7wT7iW2vPPjaNGvD3SFWm"

LOG_CHANNEL = "core"
LOG_FILE = "activation_errors.log"
LOG_FILE_LEVEL = logging.INFO

class Core:
    def __init__(self,screenLogHandler=None,logFile=None):
        # set up logging
        self.logger = logging.getLogger(LOG_CHANNEL)
        self.logger.setLevel(logging.DEBUG)
        fh = None
        if logFile == None:
            fh = logging.FileHandler(LOG_FILE)
        else:
            fh = logging.FileHandler(logFile)
        fh.setLevel(LOG_FILE_LEVEL)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        if screenLogHandler:
            self.logger.addHandler(screenLogHandler)
        # make sure we can connect to bitcoin client RPC interface

        self.rpc_conn = AuthServiceProxy("http://%s:%s@%s:%d" % (RPC_USER,
                                                                RPC_PASSWD,
                                                                RPC_HOST,
                                                                RPC_PORT))

        try:
            self.bitcoin_client_info = self.rpc_conn.getinfo()
        except JSONRPCException as e:
            self.logger.error("could not reach bitcoin RPC server: " + str(e))
            return None
        except e:
            self.logger.error("Core exception: " + str(e))
            return None

        # Initalize modules
        self.pricing = bitcoin_pricing.BitcoinPricing(logFile=logFile)
        self.ledger = bitcoin_ledger.BitcoinLedger(logFile=logFile)
        self.activation = activation.ActivationSignatureGenerator(logFile=logFile)

        if self.pricing == None or self.ledger == None:
            self.logger.error("One or more modules failed to start. Check you configuration!")
            return None

    def setRefundAddress(self,refundAddr,uuid):
        ledger_record = self.ledger.getLedgerRecord(uuid=uuid)

        if ledger_record:
            try:
                valid_addr = self.rpc_conn.validateaddress(refundAddr)
                if valid_addr['isvalid']:
                    # under no circumstances should the ledger contain invalid refund addresses
                    return self.ledger.setRefundAddress(ledger_record['id'],valid_addr['address'])
            except JSONRPCException as e:
                return False
        return False


    def processLedger(self):
        # retrieve all the unpaid accounts from the ledger and see if they match
        # newly posted transaction
        unpaid_accounts = self.ledger.retrieveUnpaid()
        unrefunded_accounts = self.ledger.retrieveUnrefunded()
        bitcoin_price = self.pricing.get24hourAvgForCurrency("USD")
        current_price = Decimal(PRICE_IN_DOLLARS) / Decimal(bitcoin_price)
        self.last_price = current_price

        total_accounts = len(unpaid_accounts)
        paid_accounts = 0
        refunded_accounts = 0
        amt_received_by_address = self.rpc_conn.listreceivedbyaddress()

        for each in unpaid_accounts.keys():
            account_balance = 0
            ledger_id = unpaid_accounts[each]
            # search through newly posted transactions for addresses from unpaid
            # accounts, then update balances and confirmations
            for transaction in amt_received_by_address:
                if transaction['address'] == each:
                    account_balance = transaction['amount']
                    self.ledger.setBalance(ledger_id,
                                            account_balance,
                                            transaction['confirmations'])
                    break

            if account_balance >= current_price:
                self.activate_uuid(ledger_id,current_price)
                paid_accounts += 1

        for each in unrefunded_accounts.keys():
            ledger_id = unrefunded_accounts[each]
            # search through newly posted transactions for addresses from
            # paid accounts, update confirmations, authorize refunds
            for transaction in amt_received_by_address:
                if transaction['address'] == each:
                    account_balance = transaction['amount']
                    self.logger.debug("Setting ledger balance: %s - %f" % (transaction['address'],account_balance))
                    self.ledger.setBalance(ledger_id,
                                            account_balance,
                                            transaction['confirmations'])
                    break

            ledger_record = self.ledger.getLedgerRecord(ledger_id)
            if ledger_record['bitcoinConfirmations'] >= REFUND_CONFIRMS:
                if ledger_record['refundAddress']:
                    refund_due = ledger_record['bitcoinBalance'] - ledger_record['pricePaid']
                    if refund_due > 0 and refund_due < Decimal(PRICE_IN_DOLLARS) * Decimal(.20):
                        self.logger.info("Remiting refund of %f to %s" % (refund_due,ledger_record['bitcoinAddress']))
                        self.remit_refund(ledger_id,refund_due)
                        refunded_accounts += 1


        self.logger.info("Found " + str(paid_accounts) + " newly paid out of " + str(total_accounts) + " accounts.")
        self.logger.info("Auto-refunded %d out of %d pending refunds." % (refunded_accounts,
                                                                        len(unrefunded_accounts)))

    def remit_refund(self,ledger_id,refund):
        ledger_record = self.ledger.getLedgerRecord(ledger_id)
        refund_due = ledger_record['bitcoinBalance'] - ledger_record['pricePaid']
        if refund_due > 0 and refund_due < (self.last_price * Decimal(.20)):
            # validate refundAddress with bitcoin client
            try:
                valid_addr = self.rpc_conn.validateaddress(ledger_record['refundAddress'])
                if valid_addr['isvalid']:
                    self.rpc_conn.sendfrom(ledger_record['uuid'],valid_addr['address'],refund_due)
                    # automatically refund overages within 20% of the
                    # price
                    self.ledger.markRefunded(ledger_id,refund_due)
            except JSONRPCException as e:
                self.logger.error("Bitcoin RPC exception while remitting refund: " + str(e))

    def activate_uuid(self,ledger_id,pricePaid):
        current_price = pricePaid
        if self.ledger.markPaid(ledger_id,current_price):
            ledger_record = self.ledger.getLedgerRecord(ledger_id)
            activation_id = self.activation.sign(ledger_record['uuid'])
            account_balance = ledger_record['bitcoinBalance']

            if activation_id < 1:
                self.logger.error("Error signing UUID: " + ledger_record['uuid'])
            else:
                self.ledger.setActivationSignatureId(ledger_id,activation_id)

    def updateForUuid(self,uuid,emailAddr=None):
        ledger_record = self.ledger.getLedgerRecord(uuid=uuid)
        bitcoin_price = self.pricing.get24hourAvgForCurrency("USD")
        current_price = Decimal(PRICE_IN_DOLLARS) / Decimal(bitcoin_price)

        if ledger_record:
            ledger_id = ledger_record['id']
            if ledger_record['emailAddress'] != emailAddr:
                if self.ledger.setEmailAddress(ledger_id,emailAddr):
                    ledger_record['emailAddress'] = emailAddr

            if ledger_record['pricePaid'] == None:
                # not yet paid, update transaction status
                # calculate account balance, based on posted transactions
                account_balance = 0
                recent_transactions = self.rpc_conn.listreceivedbyaddress()
                for each in recent_transactions:
                    if each['account'] == ledger_record['bitcoinAddress']:
                        account_balance = each['amount']
                        self.ledger.setBalance(ledger_id,account_balance,each['confirmations'])
                        break

                if account_balance >= current_price:
                    self.activate_uuid(ledger_id,current_price)

                ledger_record = self.ledger.getLedgerRecord(ledger_id)
                ledger_record['bitcoinPrice'] = str(bitcoin_price)
                ledger_record['currentPrice'] = current_price

            return ledger_record
        else:
            # establish a new bitcoin account or return address from existing
            bitcoin_addr = self.rpc_conn.getaccountaddress(uuid)
            ledger_id = self.ledger.createLedgerRecord(uuid,bitcoin_addr,emailAddr=emailAddr)
            new_ledger_record = self.ledger.getLedgerRecord(uuid=uuid)

            new_ledger_record['bitcoinPrice'] = str(bitcoin_price)
            new_ledger_record['currentPrice'] = current_price
            return new_ledger_record

if __name__ == "__main__":
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    ch.setFormatter(formatter)

    stub = Core(ch,logFile="/tmp/activation_cron.log")
    try:
        stub.processLedger()
    except e:
        print "Exception: " + str(e)
