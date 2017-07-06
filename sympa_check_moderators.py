#!/usr/bin/env python3

import os
import configparser
from datetime import datetime
from member_access_lib import *
import MySQLdb
from phabricator import Phabricator


if __name__ == "__main__":
    # Get the server config
    configfile = configparser.ConfigParser()
    configfile.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
    config = {}
    config['api_key'] = configfile.get('civicrm', 'api_key')
    config['key'] = configfile.get('civicrm', 'key')
    config['rest_url'] = configfile.get('civicrm', 'rest_url')
    config['log_file'] = "sympa_check_moderators.log"

    ma = MemberAccess(config)

    ma.logger.info("Checking if lists moderators/admins are still members.")
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

    ma.logger.info("Checking the moderators/administrators of all the lists.")
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

    cur.execute("""
        SELECT DISTINCT list_admin, user_admin, role_admin
        FROM admin_table;
        """)

    moderators = []
    for row in cur.fetchall():
        if row[1] not in all_emails:
            moderator = {
                'email': row[1],
                'list': row[0],
                'status': row[2]
            }
            moderators.append(moderator)

            ma.logger.info("{} is still {} of {} and should not.".format(
                moderator['email'],
                moderator['status'],
                moderator['list']))

    if moderators:
        phab = Phabricator()

        task_projects = [
            "PHID-PROJ-ziupm2pb2wsg43kzn2lo",  # Sympa
            "PHID-PROJ-ou65kxyzkrnflebtx6ln"  # Adhésions
        ]

        comment = "Les personnes suivantes sont gestionnaires de \
                            liste et ne sont plus à jour de cotisation:\n"

        for m in moderators:
            comment += " * {}: {} ({})\n".format(m['email'],
                                                 m['list'],
                                                 m['status'])

        # Reopening the task if closed and adding a comment
        task_details = [
            {
                "type": "status",
                "value": "open"
            },
            {
                "type": "comment",
                "value": comment
            }
        ]

        ret = phab.maniphest.edit(transactions=task_details,
                                  objectIdentifier=59)
        if ret:
            ma.logger.info("Phabricator task updated.")

    db.close()
    print("Execution finished at {}".format(datetime.now()))
