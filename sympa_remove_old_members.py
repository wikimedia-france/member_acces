#!/usr/bin/env python3

import configparser
from member_access_lib import *
import MySQLdb

lists = ['benevoles',
         'comite-audit',
         'comm',
         'controle-interne'
         'direction',
         'formation',
         'lobbying',
         'microfi',
         'qualite',
         'referents',
         'strategie',
         'tech',
         'tresorerie']

if __name__ == "__main__":

    # Get the server config
    configfile = configparser.ConfigParser()
    configfile.read('config.ini')
    config = {}
    config['api_key'] = configfile.get('civicrm', 'api_key')
    config['key'] = configfile.get('civicrm', 'key')
    config['rest_url'] = configfile.get('civicrm', 'rest_url')

    ma = MemberAccess(config)

    # Get current members (including those in grace status)
    current_members = ma.get_contacts_in_group(135, check_orgs=1)

    # Get staff members
    staff = ma.get_contacts_in_group(38)

    contacts_to_keep = current_members + staff

    all_emails = []

    for c in contacts_to_keep:
        emails = ma.contact_emails(c)
        all_emails += emails

    all_emails = list(set(all_emails))
    all_emails.sort()

    print(all_emails)

    # Connect to the Sympa MySQL Db
    user = configfile.get('mysql', 'user')
    password = configfile.get('mysql', 'password')

    db = MySQLdb.connect(host="localhost",
                         user=user,
                         passwd=password,
                         db="sympa")

    # you must create a Cursor object. It will let
    #  you execute all the queries you need
    cur = db.cursor()

    # Use all the SQL you like
    cur.execute("SELECT * FROM subscriber_table WHERE list_subscriber='wlm'")

    # print all the first cell of all the rows
    for row in cur.fetchall():
        print(row[0])

    db.close()
