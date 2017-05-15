#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import configparser
from pprint import pprint


"""
REST API doc from https://wiki.civicrm.org/confluence/display/CRMDOC44/Using+the+API

https://wiki.civicrm.org/confluence/display/CRMDOC/REST+interface#RESTinterface-CreatingAPIkeysforusers
"""

# Read the config file
config = configparser.ConfigParser()
config.read('config.ini')
api_key = config.get('civicrm', 'api_key')
key = config.get('civicrm', 'key')
rest_url = config.get('civicrm', 'rest_url')

# Base params
base_payload = {
    'api_key': api_key,
    'key': key,
    'json': 1,
    'debug': 1,
    'version': 3,
    'options[limit]': 0
}


def API_query(query_payload):
    """
    Executes a query on the API and returns the result
    as a python dict
    """
    payload = {**base_payload, **query_payload}
    response = requests.post(rest_url, params=payload)
    data = json.loads(response.text)
    if data['is_error'] == 0:
        return json.loads(response.text)
    else:
        raise Exception(data['error_message'])


def get_contacts_in_group(group, check_orgs=0):
    """
    This function uses the Contact and not the GroupContact entity
    because we want to work with smartgroups as well as regular groups
    """
    query_payload = {
        'entity': "Contact",
        'action': 'get',
        'group': {group: 1},
    }

    response = API_query(query_payload)

    contacts = []
    for k, v in response['values'].items():
        contacts.append(v['contact_id'])

        if check_orgs and v['contact_type'] == "Organization":
            relationships = check_members(v['contact_id'])
            contacts += relationships

    return contacts


def check_members(contact):
    # Get Individual contacts related to Org contacts
    print("checking relations to {}".format(contact))
    relations = []
    query_payload = {
        'entity': "Relationship",
        'action': 'get',
        'contact_id_b': contact,
        'is_active': 1
    }
    response = API_query(query_payload)
    values = response['values']
    if len(values):
        for k, v in values.items():
            relations.append(v['contact_id_a'])

    return relations


def change_group_contact_status(contact, group, status):
    # Adds or removes a contact from a group
    if status not in ["Added", "Removed"]:
        raise ValueError("Status must be either Added or Removed")
    query_payload = {
        'entity': "GroupContact",
        'action': 'create',
        'group_id': group,
        'contact_id': contact,
        'status': status
    }

    print("Contact {} {} from group {}".format(
        contact,
        status.lower(),
        group))

    response = API_query(query_payload)


if __name__ == "__main__":
    # Get current members (including those in grace status)
    current_members = get_contacts_in_group(135, check_orgs=1)

    # Get staff members
    staff = get_contacts_in_group(38)

    contacts_to_keep = current_members + staff

    # Remove non-members/staff from the Wikimembres group
    wikimembres = get_contacts_in_group(14)

    for contact in wikimembres:
        if contact not in contacts_to_keep:
            change_group_contact_status(contact, 121, "Added")
            change_group_contact_status(contact, 14, "Removed")

    # Remove non-members/staff from the discussions@list
    discussions = get_contacts_in_group(13)

    for contact in discussions:
        if contact not in contacts_to_keep:
            change_group_contact_status(contact, 121, "Added")
            change_group_contact_status(contact, 13, "Removed")
