#!/usr/bin/env python
from channelfinder import ChannelFinderClient
import _conf
import sqlite3
import sys
import os


def main():
    '''
    Accepts a filename as an argument on the command line. The file should be an SQLite Database in the same format
    as the test_db.sqlite example file. This program will submit to the Python ChannelFinder Client all of the fields
    whitelisted below in the following format in a single batch request, after first creating all of their
    tags and properties:

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

    pv_columns = c.execute('PRAGMA table_info(pvs);').fetchall()
    elems_columns = c.execute('PRAGMA table_info(elements);').fetchall()

    pv_whitelist = ['pv', 'elemHandle', 'elemField', 'tags']
    elems_whitelist = ['elemName', 'elemType', 'elemLength', 'elemPosition', 'elemIndex']

    for e_pv_id in c.execute('SELECT * from elements__pvs'):
        ch_name = None
        elem_id = (e_pv_id[1],)
        pv_id = (e_pv_id[2],)
        pv = conn.cursor().execute('SELECT * from pvs WHERE pv_id =?', pv_id).fetchone()
        for i in range(1, len(pv)):
            if pv_columns[i][1] in pv_whitelist:
                if pv_columns[i][1] == 'pv':
                    ch_name = pv[i]
                    add_channel_to_cf(cf, ch_name)
                elif pv_columns[i][1] == 'tags':
                    add_tags_to_ch(cf, tags, ch_name, pv[i])
                else:
                    add_prop_to_ch(cf, props, ch_name, pv_columns[i][1], pv[i])
        elems = conn.cursor().execute('SELECT * from elements where elem_id =?', elem_id).fetchone()
        for i in range(1, len(elems)):
            if elems_columns[i][1] in elems_whitelist:
                add_prop_to_ch(cf, props, ch_name, elems_columns[i][1], elems[i])

    # print tags.values()
    client.set(tags=tags.values())
    # print props.values()
    client.set(properties=props.values())
    # print cf.values()
    client.set(channels=cf.values())


def add_channel_to_cf(cf, ch_name):
    # print "Add ", ch_name, " to cf"
    if ch_name not in cf:
        cf[ch_name] = {u'name': ch_name, u'owner': u'sql-to-cfs', u'properties': [], u'tags': []}


def add_tags_to_ch(cf, tags, ch_name, tag_string):
    # print "Add ", tag_string, " to ", ch_name, " in cf"
    for tag_name in str.split(str(tag_string), ';'):
        if tag_name not in tags:
            tags[tag_name] = {u'name': tag_name, u'owner': u'sql-to-cfs'}
        cf[ch_name][u'tags'].append({u'name': tag_name, u'owner': u'sql-to-cfs'})


def add_prop_to_ch(cf, props, ch_name, prop_name, prop_val):
    # print "Add ", prop_name, " to ", ch_name, " with value: ", prop_val, " in cf"
    if prop_name not in props:
        props[prop_name] = {u'name': prop_name, u'owner': u'sql-to-cfs'}
    cf[ch_name][u'properties'].append({u'name': prop_name, u'owner': u'sql-to-cfs', u'value': prop_val})


if __name__ == "__main__":
    if len(sys.argv) == 2:
        if os.path.isfile(sys.argv[1]):
            main()
        else:
            print "Bad argument"
    else:
        print "Script requires file argument to run"
