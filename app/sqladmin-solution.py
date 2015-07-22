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

import httplib2
import googleapiclient.discovery as api_discovery
from oauth2client import client as oauth2_client

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


def main():
    if len(sys.argv) != 2:
        print USAGE_MESSAGE
        sys.exit(1)
    if not (sys.argv[1] == 'start' or sys.argv[1] == 'stop'):
        print USAGE_MESSAGE
        sys.exit(1)
    http = httplib2.Http()
    ip_endpoint = '/instance/network-interfaces/0/access-configs/0/external-ip'
    ip_address = metaquery(http,
                           METADATA_SERVER +
                           ip_endpoint)
    token_data = metaquery(http,
                           METADATA_SERVER +
                           '/instance/service-accounts/default/token')
    project_id = metaquery(http,
                           METADATA_SERVER +
                           '/project/project-id')
    sql_name = metaquery(http,
                         METADATA_SERVER +
                         '/instance/attributes/sql-name')
    if token_data and sql_name and ip_address:
        j = json.loads(token_data)
        credentials = oauth2_client.AccessTokenCredentials(j['access_token'],
                                                           'my-user-agent/1.0')
        cloudsql = api_discovery.build('sqladmin',
                                       'v1beta4',
                                       http=credentials.authorize(http))
        response = cloudsql.instances().get(project=project_id,
                                            instance=sql_name,
                                            fields='settings').execute()
        address = address_resource(ip_address)
        if response and 'settings' in response:
            if sys.argv[1] == 'start':
                (response
                 ['settings']
                 ['ipConfiguration']
                 ['authorizedNetworks']
                 .append(address))
            else:
                for response_address in (response
                                         ['settings']
                                         ['ipConfiguration']
                                         ['authorizedNetworks']):
                    if response_address['value'] == ip_address:
                        (response
                         ['settings']
                         ['ipConfiguration']
                         ['authorizedNetworks']
                         .remove(response_address))
            p_response = cloudsql.instances().patch(project=project_id,
                                                    instance=sql_name,
                                                    body=response).execute()
            print json.dumps(p_response,
                             sort_keys=True,
                             indent=4,
                             separators=(',', ': '))
        else:
            print 'Unexpected response from the Cloud SQL API'
    else:
        print "There was an error contacting the metadata server."
if __name__ == '__main__':
    main()
