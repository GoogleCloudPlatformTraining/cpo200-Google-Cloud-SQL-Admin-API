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
import json
import time
import random
import logging

import httplib2
import googleapiclient.discovery as api_discovery
from oauth2client import client as oauth2_client
from googleapiclient import errors

METADATA_SERVER = 'http://metadata/computeMetadata/v1'
RETRY = 5


def metaquery(endpoint):
    for retry in range(0, RETRY):
        try:
            http = httplib2.Http()
            resp, content = http.request(endpoint,
                                         method='GET',
                                         body=None,
                                         headers={'Metadata-Flavor': 'Google'})
            if resp.status == 200:
                return content
            else:
                return None
        except httplib.ResponseNotReady:
           if retry == (RETRY - 1):
               logging.debug("Could not retrieve metadata")
               return None
           else:
               # exponential backoff retry
               logging.debug("sleeping...")
               time.sleep((2 ** retry) + random.randint(0, 5))
               logging.debug("retrying metadata retrieval...")


def address_resource(ip_address):
    address = {
        "name": "ha-instance",
        "value": ip_address,
        "kind": "sql#aclEntry"
    }
    return address


def server_authorization(cloudsql, ip_address, project_id, sql_name):
    for retry in range(0, RETRY):
        try:
            response = cloudsql.instances().get(project=project_id,
                                                instance=sql_name,
                                                fields='settings').execute()
            (response['settings']['ipConfiguration']['authorizedNetworks']
             .append(address_resource(ip_address)))
            logging.debug(json.dumps(response,
                                     sort_keys=True,
                                     indent=4,
                                     separators=(',', ': ')))
            # Replace the fourth marker with the API call required to patch
            # a Cloud SQL instance
            p_response = TODO04
            time.sleep(random.randint(1, 6))
            verify = cloudsql.instances().get(project=project_id,
                                              instance=sql_name,
                                              fields='settings').execute()
            networks = verify['settings']['ipConfiguration']['authorizedNetworks']
            if networks.count(address_resource(ip_address)) == 1:
                return(json.dumps(p_response,
                                  sort_keys=True,
                                  indent=4,
                                  separators=(',', ': ')))
            else:
                return None
        except errors.HttpError as error_data:
            error = json.loads(error_data.content)
            if error.get('error').get('code') in (403, 500):
                if retry == (RETRY - 1):
                    logging.debug("Could not complete the patch.")
                    return None
                else:
                    # exponential backoff retry
                    logging.debug("sleeping...")
                    time.sleep((2 ** retry) + random.randint(0, 60))
                    logging.debug("retrying API request...")
            else:
                raise


def main():
    logging.basicConfig(level=logging.DEBUG)
    # Replace the first marker with the metadata endpoint substring
    # required to query the value of the external IP address
    ip_endpoint = 'TODO01'
    ip_address = metaquery(METADATA_SERVER +
                           ip_endpoint)
    token_data = metaquery(METADATA_SERVER +
                           '/instance/service-accounts/default/token')
    # Replace the second marker with the metadata endpoint substring
    # required to query the project ID
    project_id = metaquery(METADATA_SERVER +
                           'TODO02')
    # Replace the second marker with the metadata endpoint substring
    # required to query the value for the custom key 'sql-name'
    sql_name = metaquery(METADATA_SERVER +
                         'TODO03')
    if token_data and sql_name and ip_address:
        http = httplib2.Http()
        j = json.loads(token_data)
        credentials = oauth2_client.AccessTokenCredentials(j['access_token'],
                                                           'my-user-agent/1.0')
        cloudsql = api_discovery.build('sqladmin',
                                       'v1beta4',
                                       http=credentials.authorize(http))
        patch_response = server_authorization(cloudsql=cloudsql,
                                              ip_address=ip_address,
                                              project_id=project_id,
                                              sql_name=sql_name)
        if patch_response:
            logging.debug(patch_response)
        else:
            logging.debug("Giving up, could not complete the patch authorization.")
    else:
        logging.debug('There was an error contacting the metadata server.')

if __name__ == '__main__':
    main()
