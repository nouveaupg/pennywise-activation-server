# core Module
#
# central dispatch for activation service
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import logging

import bitcoin_pricing
import bitcoin_ledger

PRICE_IN_DOLLARS 20

RPC_HOST "aries"
RPC_PORT 8332
RPC_USER "bitcoinrpc"
RPC_PASSWD "EsDt8nz5LhPdERzct5MwQJr7wT7iW2vPPjaNGvD3SFWm"

LOG_CHANNEL = "activation"
LOG_FILE = "activation_errors.log"
LOG_FILE_LEVEL = logging.ERROR

class Core:
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
            self.logger.error("rpc exception: " + str(e))
            return None

        # Initalize modules
        self.pricing = bitcoin_pricing.BitcoinPricing()
        self.ledger = bitcoin_ledger.BitcoinLedger()

        if self.pricing == None or self.ledger == None:
            self.logger.error("One or more modules failed to start. Check you configuration!")
            return None

    def processLedger(self):
        # retrieve all the unpaid accounts from the ledger and see if they match
        # newly posted transaction
        unpaid_accounts = self.ledger.retrieveUnpaid()
        bitcoin_price = self.pricing.get24hourAvgForCurrency("USD")
        current_price = double(PRICE_IN_DOLLARS / bitcoin_price)

        total_accounts = len(unpaid_accounts)
        paid_accounts = 0
        amt_received_by_address = self.rpc_conn.listreceivedbyaddress()

        for each in unpaid_accounts.keys():
            account_balance = 0
            # search through newly posted transactions for addresses from unpaid_accounts
            for transaction in amt_received_by_address:
                if transaction.address == each:
                    account_balance = transaction.amount
                    self.rpc_conn.setBalance(unpaid_accounts[each],
                                                account_balance,
                                                transaction.confirmations)
                    break

            if account_balance >= current_price:
                if self.ledger.markPaid(ledger_id,current_price):
                    refund_due = account_balance - current_price
                    paid_accounts += 1
                    if refund_due > 0 and
                        refund_due < current_price * .20 and
                        ledger_record['refundAddress'] != None:
                        # validate refundAddress with bitcoin client
                        valid_addr = self.rpc_conn.validateaddress(ledger_record['refundAddress'])
                        if valid_addr['isvalid']:
                            self.rpc_conn.sendfrom(ledger_record['uuid'],valid_addr['address'],refund_due)
                            # automatically refund overages within 20% of the
                            # price
                            self.ledger.markRefunded(ledger_id,refund_due)
        self.logger.info("Found " + paid_accounts + " newly paid out of " + total_accounts + " accounts.")

    def updateForUuid(self,uuid,emailAddr=None):
        ledger_record = self.ledger.getLedgerRecord(uuid=uuid)
        bitcoin_price = self.pricing.get24hourAvgForCurrency("USD")
        current_price = double(PRICE_IN_DOLLARS / bitcoin_price)

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
                    if each.account == ledger_record['bitcoinAddress']:
                        account_balance = each.amount
                        self.ledger.setBalance(ledger_id,account_balance,each.confirmations)
                        break

                if account_balance >= current_price:
                    if self.ledger.markPaid(ledger_id,current_price):
                        amount_to_refund = account_balance - current_price
                        if amount_to_refund > 0 and
                            amount_to_refund < PRICE_IN_DOLLARS * .20 and
                            ledger_record['refundAddress'] != None:
                            # validate refundAddress with bitcoin client
                            try:
                                valid_addr = self.rpc_conn.validateaddress(ledger_record['refundAddress'])
                                # automatically refund overages within 20% of the
                                # price
                                if valid_addr['isvalid']:
                                    self.rpc_conn.sendfrom(ledger_record['uuid'],valid_addr['address'],amount_to_refund)
                                    self.ledger.markRefunded(ledger_id,amount_to_refund)
                            except e:
                                self.logger.error("rpc exception: " + str(e))
                                return None


                ledger_record['bitcoinPrice'] = str(bitcoin_price)
                ledger_record['currentPrice'] = current_price

            return ledger_record
        else:
            # establish a new bitcoin account or return address from existing
            bitcoin_addr = self.rpc_conn.getaccountaddress(uuid)
            ledger_id = self.ledger.createLedgerRecord(uuid,bitcoin_addr,emailAddr=emailAddr)
            new_ledger_record = self.ledger.getLedgerRecord(ledgerId=ledger_id)

            new_ledger_record['bitcoinPrice'] = str(bitcoin_price)
            new_ledger_record['currentPrice'] = current_price
            return new_ledger_record

if __name__ == "__main__":
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    ch.setFormatter(formatter)

    stub = Core(ch)
    stub.processLedger()
