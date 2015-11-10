import unittest
import uuid
import bitcoin_ledger

class BitcoinLedgerUnitTests(unittest.TestCase):
    """ Unit tests for BitcoinLedger """

    def test_createNewRecord(self):
        ledger = bitcoin_ledger.BitcoinLedger()
        self.assertIsNotNone(ledger)
        new_uuid = str(uuid.uuid4()).upper()
        new_ledger_id = ledger.createLedgerRecord(uuid=new_uuid,bitcoinAddr='1JrTrzBJ8LnJVk9Mkt5WccGRMrN2ysRnSQ')
        self.assertTrue(new_ledger_id > 0)
        ledger_record = ledger.getLedgerRecord(ledgerId=new_ledger_id)
        self.assertIsNotNone(ledger_record)
        self.assertTrue('uuid' in ledger_record)
        self.assertTrue(ledger_record['uuid'] == new_uuid)
        self.assertIsNone(ledger_record['pricePaid'])

if __name__ == '__main__':
    unittest.main()
