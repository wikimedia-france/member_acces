#!/usr/bin/env python3

import os
import configparser
from datetime import datetime
from member_access_lib import *
import MySQLdb


def remove_contact_from_list(cursor, contact, sympa_list):
    """Removes the specified contact from the specified list"""
    query = """
        DELETE FROM subscriber_table
        WHERE list_subscriber = %s
        AND user_subscriber = %s
        AND included_subscriber = 0;
    """
    result = cursor.execute(query, [sympa_list, contact])

    if result:
        ma.logger.info("Address {} has been removed from list {}".format(
            contact, sympa_list))
    else:
        ma.logger.warning("Warning: Address {} has not been \
            removed from list {}".format(
            contact, sympa_list))


if __name__ == "__main__":
    managed_lists = ['benevoles',
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
    # Get the server config
    configfile = configparser.ConfigParser()
    configfile.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
    config = {}
    config['api_key'] = configfile.get('civicrm', 'api_key')
    config['key'] = configfile.get('civicrm', 'key')
    config['rest_url'] = configfile.get('civicrm', 'rest_url')
    config['log_file'] = "sympa_remove_old_members.log"

    ma = MemberAccess(config)

    ma.logger.info("Removing former members from these lists: ".format(
        ', '.join(managed_lists)))
    ma.logger.info("Execution started at {}".format(datetime.now()))


    # Get current members (including those in grace status)
    ma.logger.info("Retrieving all current members and staff...")
    current_members = ma.get_contacts_in_group(135, check_orgs=1)

    # Get staff members
    staff = ma.get_contacts_in_group(38)

    contacts_to_keep = current_members + staff
    ma.logger.info("{} contacts found.".format(len(contacts_to_keep)))

    ma.logger.info("Retrieving all emails associated with these contacts...")
    all_emails = ["communautes@wikimedia.fr", "tech@wikimedia.fr"]

    for c in contacts_to_keep:
        emails = ma.contact_emails(c)
        all_emails += emails

    all_emails = list(set(all_emails))
    all_emails.sort()
    ma.logger.info("{} email addresses found".format(len(all_emails)))

    ma.logger.info("Retrieving the subscribers of all the mentioned lists...")
    # Connect to the Sympa MySQL Db
    user = configfile.get('mysql', 'user')
    password = configfile.get('mysql', 'password')
    host = configfile.get('mysql', 'host')
    database = configfile.get('mysql', 'database')

    db = MySQLdb.connect(host=host,
                         user=user,
                         passwd=password,
                         db=database)
    cur = db.cursor()

    lists_str = ', '.join('"{0}"'.format(l) for l in managed_lists)

    # Get all subscribers to the managed lists
    cur.execute("""
        SELECT list_subscriber, user_subscriber
        FROM subscriber_table
        WHERE list_subscriber IN ({})
        AND included_subscriber=0
        """.format(lists_str))

    for row in cur.fetchall():
        if row[1] not in all_emails:
            remove_contact_from_list(cur, row[1], row[0])
    db.close()

    ma.logger.info("Execution finished at {}".format(datetime.now()))
