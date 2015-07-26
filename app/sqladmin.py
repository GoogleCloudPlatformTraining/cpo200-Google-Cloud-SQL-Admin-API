#!/usr/bin/env python
#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import sys
import json
import time
import random
import logging

import httplib2
import googleapiclient.discovery as api_discovery
from oauth2client import client as oauth2_client
from googleapiclient import errors

METADATA_SERVER = 'http://metadata/computeMetadata/v1'
USAGE_MESSAGE = 'usage: python sqladmin.py start OR stop'


def metaquery(http, endpoint):
    resp, content = http.request(endpoint,
                                 method='GET',
                                 body=None,
                                 headers={'Metadata-Flavor': 'Google'})
    if resp.status == 200:
        return content
    else:
        return None


def address_resource(ip_address):
    address = {
        "name": "ha-instance",
        "value": ip_address,
        "kind": "sql#aclEntry"
    }
    return address


def server_authorization(command, cloudsql, ip_address, project_id, sql_name):
    for retry in range(0, 5):
        try:
            response = cloudsql.instances().get(project=project_id,
                                                instance=sql_name,
                                                fields='settings').execute()
            if response and 'settings' in response:
                if command == 'start':
                    (response
                     ['settings']
                     ['ipConfiguration']
                     ['authorizedNetworks']
                     .append(address_resource(ip_address)))
                else:
                    (response
                     ['settings']
                     ['ipConfiguration']
                     ['authorizedNetworks']
                     .remove(address_resource(ip_address)))
                p_response = TODO04
                return(json.dumps(p_response,
                                  sort_keys=True,
                                  indent=4,
                                  separators=(',', ': ')))
            else:
                logging.debug('Unexpected response from the Cloud SQL API')
        except errors.HttpError as error_data:
            error = json.loads(error_data.content)
            if error.get('error').get('code') == 403:
                if retry == 4:
                    logging.debug("Could not complete the patch.")
                    return None
                else:
                    # exponential backoff retry
                    logging.debug("sleeping...")
                    time.sleep((2 ** retry) + random.randint(0, 60))
                    logging.debug("retrying...")
            else:
                raise
        except ValueError:
            logging.debug("Attempted to remove an unauthorized IP address.")
            return None


def main():
    if len(sys.argv) != 2:
        print USAGE_MESSAGE
        sys.exit(1)
    if not (sys.argv[1] == 'start' or sys.argv[1] == 'stop'):
        print USAGE_MESSAGE
        sys.exit(1)
    logging.basicConfig(level=logging.DEBUG)
    http = httplib2.Http()
    ip_endpoint = 'TODO01'
    ip_address = metaquery(http,
                           METADATA_SERVER +
                           ip_endpoint)
    token_data = metaquery(http,
                           METADATA_SERVER +
                           '/instance/service-accounts/default/token')
    # Replace the second marker with the metadata endpoint substring
    # required to query the project ID
    project_id = metaquery(http,
                           METADATA_SERVER +
                           'TODO02')
    # Replace the second marker with the metadata endpoint substring
    # required to query the value for the custom key 'sql-name'
    sql_name = metaquery(http,
                         METADATA_SERVER +
                         'TODO03')
    if token_data and sql_name and ip_address:
        j = json.loads(token_data)
        credentials = oauth2_client.AccessTokenCredentials(j['access_token'],
                                                           'my-user-agent/1.0')
        cloudsql = api_discovery.build('sqladmin',
                                       'v1beta4',
                                       http=credentials.authorize(http))
        logging.debug(server_authorization(command=sys.argv[1],
                                           cloudsql=cloudsql,
                                           ip_address=ip_address,
                                           project_id=project_id,
                                           sql_name=sql_name))
    else:
        logging.debug('There was an error contacting the metadata server.')

if __name__ == '__main__':
    main()
