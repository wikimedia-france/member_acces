#!/usr/bin/env python3

import os
import configparser
from member_access_lib import *

if __name__ == "__main__":

    # Get the server config
    configfile = configparser.ConfigParser()
    configfile.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
    config = {}
    config['api_key'] = configfile.get('civicrm', 'api_key')
    config['key'] = configfile.get('civicrm', 'key')
    config['rest_url'] = configfile.get('civicrm', 'rest_url')
    config['log_file'] = "civicrm_remove_old_members.log"

    ma = MemberAccess(config)

    # Get current members (including those in grace status)
    current_members = ma.get_contacts_in_group(135, check_orgs=1)

    # Get staff members
    staff = ma.get_contacts_in_group(38)

    contacts_to_keep = current_members + staff

    # Remove non-members/staff from the Wikimembres group
    wikimembres = ma.get_contacts_in_group(14)

    for contact in wikimembres:
        if contact not in contacts_to_keep:
            ma.change_group_contact_status(contact, 121, "Added")
            ma.change_group_contact_status(contact, 14, "Removed")

    # Remove non-members/staff from the discussions@list
    discussions = ma.get_contacts_in_group(13)

    for contact in discussions:
        if contact not in contacts_to_keep:
            ma.change_group_contact_status(contact, 121, "Added")
            ma.change_group_contact_status(contact, 13, "Removed")
