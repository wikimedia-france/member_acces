#!/usr/bin/env python3

import requests
import json
from easylogger import easylogger
from logging import INFO


class MemberAccess:
    def __init__(self, config):
        self.api_key = config['api_key']
        self.key = config['key']
        self.rest_url = config['rest_url']
        self.logfile = config['log_file']

        # Base params
        self.base_payload = {
            'api_key': config['api_key'],
            'key': config['key'],
            'json': 1,
            'debug': 1,
            'version': 3,
            'options[limit]': 0
        }

        self.logger = easylogger(self.logfile, INFO)

    def API_query(self, query_payload):
        """
        Executes a query on the API and returns the result
        as a python dict
        """
        payload = self.base_payload.copy()
        payload.update(query_payload)
        response = requests.post(self.rest_url, params=payload)
        self.logger.debug('API call: {}'.format(response.url))
        data = json.loads(response.text)
        if data['is_error'] == 0:
            return json.loads(response.text)
        else:
            # self.logger.error(data['error_message'])
            raise Exception(data['error_message'])

    def get_contacts_in_group(self, group, check_orgs=0):
        """
        This function uses the Contact and not the GroupContact entity
        because we want to work with smartgroups as well as regular groups
        """

        self.logger.info("Querying contacts for group {}".format(group))
        query_payload = {
            'entity': "Contact",
            'action': 'get',
            'group': {group: 1},
        }

        response = self.API_query(query_payload)

        contacts = []
        for k, v in response['values'].items():
            contacts.append(v['contact_id'])

            if check_orgs and v['contact_type'] == "Organization":
                relationships = self.check_members(v['contact_id'])
                contacts += relationships

        self.logger.info("{} contacts found in group {}".format(
            len(contacts),
            group))
        return contacts

    def check_members(self, contact):
        # Get Individual contacts related to Org contacts
        self.logger.info("checking relations to {}".format(contact))
        relations = []
        query_payload = {
            'entity': "Relationship",
            'action': 'get',
            'contact_id_b': contact,
            'is_active': 1
        }
        response = self.API_query(query_payload)
        values = response['values']
        if len(values):
            for k, v in values.items():
                relations.append(v['contact_id_a'])

        self.logger.info("{} relations found for contact {}".format(
            len(relations),
            contact))
        return relations

    def contact_emails(self, contact):
        # Get all the valid emails associated with the contact
        query_payload = {
            'entity': "Email",
            'action': 'get',
            'contact_id': contact,
            'on_hold': 0,
        }
        response = self.API_query(query_payload)
        values = response['values']
        emails = []
        if len(values):
            for k, v in values.items():
                emails.append(v['email'])

        emails = list(set(emails))
        self.logger.info("{} emails found for contact {}".format(
            len(emails),
            contact))
        return emails

    def change_group_contact_status(self, contact, group, status):
        # Adds or removes a contact from a group
        if status not in ["Added", "Removed"]:
            self.logger.error("Status must be either Added or Removed")
            raise ValueError("Status must be either Added or Removed")

        query_payload = {
            'entity': "GroupContact",
            'action': 'create',
            'group_id': group,
            'contact_id': contact,
            'status': status
        }

        self.API_query(query_payload)

        self.logger.info("Contact {} {} from group {}".format(
            contact,
            status.lower(),
            group))
