#!/usr/bin/env python
from channelfinder import ChannelFinderClient
import _conf
import sqlite3
import sys
import os


def main():
    '''
    Accepts a filename as an argument on the command line. The filename is used as the output location for the data,
    if the file is an sqlite database it will connect, create the appropriate tables, and populate it with the data.
    It will create a new file if one does not exist at the location:

    ex = {u'name': u'V_1:LS1_CA01:CAV1_D1127:PHA_CSET',
          u'owner': u'sql-to-cfs',
          u'properties': [
              {u'name': u'elemHandle', u'owner': u'sql-to-cfs', u'value': u'setpoint'},
              {u'name': u'elemField', u'owner': u'sql-to-cfs', u'value': u'PHA'},
              {u'name': u'elemName', u'owner': u'sql-to-cfs', u'value': u'LS_CA01:CAV1_D1127'},
              {u'name': u'elemType', u'owner': u'sql-to-cfs', u'value': u'CAV'},
              {u'name': u'elemLength', u'owner': u'sql-to-cfs', u'value': u'0.24'},
              {u'name': u'elemPosition', u'owner': u'sql-to-cfs', u'value': u'0.4470635'},
              {u'name': u'elemIndex', u'owner': u'sql-to-cfs', u'value': u'3'}
          ],
          u'tags': [
              {u'name': u'phyutil.sub.CA01', u'owner': u'sql-to-cfs'},
              {u'name': u'phyutil.sys.LINAC', u'owner': u'sql-to-cfs'},
              {u'name': u'phyutil.sys.LS1', u'owner': u'sql-to-cfs'}
          ]}

          to

    insert into pvs values (1, 'V_1:LS1_CA01:CAV1_D1127:PHA_CSET', 'setpoint', 'PHA', 0, 0, 0, 'phyutil.sub.CA01;phyutil.sys.LINAC;phyutil.sys.LS1', 0, 0, 0, 0, 0, 0, 0, 0)
    insert into elements values (1, 'LS_CA01:CAV1_D1127', 'CAV', 0.24, 0.4470635, 3, 0, 0, 0)
    insert into elem_pvs values (1, 1, 1)
    '''
    cf = {}
    tags = {}
    props = {}
    conf = _conf._testConf
    BaseURL = conf.get('DEFAULT', 'BaseURL')
    username = conf.get('DEFAULT', 'username')
    password = conf.get('DEFAULT', 'password')
    client = ChannelFinderClient(BaseURL=BaseURL, username=username, password=password)

    db = sys.argv[1]
    # os.chdir(os.path.dirname(__file__))
    conn = sqlite3.connect(db)
    c = conn.cursor()



    pv_whitelist = ['pv', 'elemHandle', 'elemField', 'tags']
    elems_whitelist = ['elemName', 'elemType', 'elemLength', 'elemPosition', 'elemIndex']

    elem_id = -1

    try:
        c.execute('CREATE TABLE elements(elem_id INTEGER PRIMARY KEY AUTOINCREMENT, elemName TEXT NOT NULL, elemType TEXT NOT NULL, elemLength REAL, elemPosition REAL, elemIndex INTEGER NOT NULL, elemGroups TEXT, fieldPolar INTEGER, virtual INTEGER DEFAULT 0, UNIQUE(elemName, elemType, elemIndex) ON CONFLICT FAIL);')
        c.execute('CREATE TABLE pvs(pv_id INTEGER PRIMARY KEY AUTOINCREMENT, pv TEXT NOT NULL UNIQUE, elemHandle TEXT, elemField TEXT, hostName TEXT, devName TEXT, iocName TEXT, tags TEXT, speed REAL, hlaHigh REAL, hlaLow REAL, hlaStepsize REAL, hlaValRef REAL, archive INT DEFAULT 0, size INT DEFAULT 0, epsilon REAL DEFAULT 0.0);')
        c.execute('CREATE TABLE elements__pvs(elem_pvs_id INTEGER PRIMARY KEY AUTOINCREMENT, elem_id INTEGER, pv_id INTEGER, FOREIGN KEY(elem_id) REFERENCES elements(elem_id), FOREIGN KEY(pv_id) REFERENCES pvs(pv_id), UNIQUE(elem_id, pv_id) ON CONFLICT REPLACE);')
    except sqlite3.OperationalError:
        pass  # tables exists
    pv_columns = c.execute('PRAGMA table_info(pvs);').fetchall()
    elems_columns = c.execute('PRAGMA table_info(elements);').fetchall()

    for ch in client.find(name='*'):
        new_pv = [0, 0, 0, None, None, None, 0, None, None, None, None, None, 0, 0, 0.0]
        new_elem = [0, 0, 0, 0, 0, None, None, 0]
        tag_string = ""
        new_pv[0] = ch['name'].encode('ascii', 'ignore')
        for tag in ch['tags']:
            if tag_string == "":
                tag_string = tag['name']
            else:
                tag_string += ";" + tag['name']
        new_pv[6] = tag_string.encode('ascii', 'ignore')
        for prop in ch['properties']:
            # Build pv:
            if prop['name'] == 'elemHandle':
                new_pv[1] = prop['value'].encode('ascii', 'ignore')
            if prop['name'] == 'elemField':
                new_pv[2] = prop['value'].encode('ascii', 'ignore')
            # Build element:
            if prop['name'] == 'elemName':
                new_elem[0] = prop['value'].encode('ascii', 'ignore')
            if prop['name'] == 'elemType':
                new_elem[1] = prop['value'].encode('ascii', 'ignore')
            if prop['name'] == 'elemLength':
                new_elem[2] = prop['value'].encode('ascii', 'ignore')
            if prop['name'] == 'elemPosition':
                new_elem[3] = prop['value'].encode('ascii', 'ignore')
            if prop['name'] == 'elemIndex':
                new_elem[4] = prop['value'].encode('ascii', 'ignore')
        pv = c.execute('SELECT * FROM pvs WHERE pv =(?);', (new_pv[0],)).fetchall()
        if not pv:
            c.execute('INSERT INTO pvs(pv, elemHandle, elemField, hostName, devName, iocName, tags, speed, hlaHigh, hlaLow, hlaStepsize, hlaValRef, archive, size, epsilon) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);', tuple(new_pv))
            pv_id = c.lastrowid
        else:  # pv exists
            pv_id = pv[0][0]
        elem = c.execute('SELECT * FROM elements WHERE elemName =(?);', (new_elem[0],)).fetchall()
        if not elem:
            c.execute('INSERT INTO elements(elemName, elemType, elemLength, elemPosition, elemIndex, elemGroups, fieldPolar, virtual) VALUES (?, ?, ?, ?, ?, ?, ?, ?);', tuple(new_elem))
            elem_id = c.lastrowid
        else:  # elem exists
            elem_id = elem[0][0]

        elem_pvs_id = (elem_id, pv_id)
        if not c.execute('SELECT * FROM elements__pvs WHERE pv_id =?', (pv_id,)).fetchall():
            c.execute('INSERT INTO elements__pvs(elem_id, pv_id) VALUES ' + str(elem_pvs_id) + ';')

    conn.commit()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        if os.path.isfile(sys.argv[1]):
            main()
        else:
            file = open(sys.argv[1], 'w+')
            file.close()
            main()
    else:
        print "Script requires file argument to run"
