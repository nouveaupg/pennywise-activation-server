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

    def test_fetchLatestRecords(self):
        ledger = bitcoin_ledger.BitcoinLedger()
        self.assertIsNotNone(ledger)

        new_uuid1 = str(uuid.uuid4()).upper()
        new_uuid2 = str(uuid.uuid4()).upper()
        new_uuid3 = str(uuid.uuid4()).upper()

        bitcoin_addr1 = '1JrTrzBJ8LnJVk9Mkt5WccGRMrN2ysRnSQ'
        bitcoin_addr2 = '1JrTrzBJ6LnJVk9Mkt5WccGRMrN2ysRnSQ'
        bitcoin_addr3 = '1JrTrzBJ7LnJVk9Mkt5WccGRMrN2ysRnSQ'

        new_ledger_id1 = ledger.createLedgerRecord(uuid=new_uuid1,bitcoinAddr=bitcoin_addr1)
        new_ledger_id2 = ledger.createLedgerRecord(uuid=new_uuid2,bitcoinAddr=bitcoin_addr2,emailAddr='nouveau.pg@gmail.com')
        new_ledger_id3 = ledger.createLedgerRecord(uuid=new_uuid3,bitcoinAddr=bitcoin_addr3)

        self.assertTrue(new_ledger_id1 > 0)
        self.assertTrue(new_ledger_id2 > 0)
        self.assertTrue(new_ledger_id3 > 0)

        latestRecords = ledger.latestRecords(0,3)
        self.assertIsNone(latestRecords[0]['emailAddress'])
        self.assertEqual(latestRecords[0]['uuid'],new_uuid3)
        self.assertEqual(latestRecords[0]['id'],new_ledger_id3)
        self.assertEqual(latestRecords[0]['bitcoinAddress'],bitcoin_addr3)

        self.assertEqual(latestRecords[1]['emailAddress'],'nouveau.pg@gmail.com')
        self.assertEqual(latestRecords[1]['uuid'],new_uuid2)
        self.assertEqual(latestRecords[1]['id'],new_ledger_id2)
        self.assertEqual(latestRecords[1]['bitcoinAddress'],bitcoin_addr2)

        self.assertIsNone(latestRecords[2]['emailAddress'])
        self.assertEqual(latestRecords[2]['uuid'],new_uuid1)
        self.assertEqual(latestRecords[2]['id'],new_ledger_id1)
        self.assertEqual(latestRecords[2]['bitcoinAddress'],bitcoin_addr1)

if __name__ == '__main__':
    unittest.main()
