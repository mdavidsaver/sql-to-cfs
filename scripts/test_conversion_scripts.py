from channelfinder import ChannelFinderClient
import unittest
import _conf
import sqlite3
import os
import subprocess


class Test_sql_to_cfs(unittest.TestCase):

    def setUp(self):
        self.conf = _conf._testConf
        BaseURL = self.conf.get('DEFAULT', 'BaseURL')
        username = self.conf.get('DEFAULT', 'username')
        password = self.conf.get('DEFAULT', 'password')
        self.client = ChannelFinderClient(BaseURL=BaseURL, username=username, password=password)
        os.chdir(os.path.dirname(__file__))
        os.chdir("../db")
        self.conn = sqlite3.connect("test_db.sqlite")
        c = self.conn.cursor()
        # Remove all channels for re-add during test
        for pv in c.execute('SELECT * from pvs'):
            if self.client.find(name=pv[1]):
                self.client.delete(channelName=pv[1])
        # Ensure all channels were removed
        for pv in c.execute('SELECT * from pvs'):
            self.assertFalse(self.client.find(name=pv[1]))

    def tearDown(self):
        '''
        Note: Not removing tags or properties because it would destroy existing data. Possible workaround:
        Sufficiently unique names on test channels, tags, and properties.
        '''
        c = self.conn.cursor()
        # Remove all channels for test clean up
        for pv in c.execute('SELECT * from pvs'):
            if self.client.find(name=pv[1]):
                self.client.delete(channelName=pv[1])
        # Ensure all channels were removed
        for pv in c.execute('SELECT * from pvs'):
            self.assertFalse(self.client.find(name=pv[1]))
        if os.path.exists('../db/_test_output.sqlite'):
            os.remove('../db/_test_output.sqlite')

    def test_cli(self):
        '''
        1. Converts existing test_db.sqlite database into existing CFS using sql-to-cfs.
        2. Asserts that the new channel names exist.
        3. Converts all channels in CF into new _test_output.sqlite database using cfs-to-sql.
        4. Iterates through test_db.sqlite and asserts that all data was migrated to _test_output.sqlite.
        '''
        os.chdir(os.path.dirname(__file__))
        # Run script
        subprocess.call(['./sql-to-cfs.py', '../db/test_db.sqlite'])
        c = self.conn.cursor()
        # Ensure all channels were created
        for pv in c.execute('SELECT * from pvs'):
            self.assertTrue(self.client.find(name=pv[1]))
        file = open('../db/_test_output.sqlite', 'w+')
        subprocess.call(['./cfs-to-sql.py', '../db/_test_output.sqlite'])
        test_conn = sqlite3.connect('../db/_test_output.sqlite')
        c2 = test_conn.cursor()
        for pv in c.execute('SELECT * from pvs'):
            # Ignores first element (ID) which is not consistent
            self.assertEqual(pv[1:], c2.execute('select * from pvs where pv =?', (pv[1],)).fetchone()[1:])
        for elem in c.execute('SELECT * from elements'):
            # Ignores first element (ID) which is not consistent
            self.assertEqual(elem[1:], c2.execute('select * from elements where elemName =?', (elem[1],)).fetchone()[1:])

if __name__ == '__main__':
    unittest.main()