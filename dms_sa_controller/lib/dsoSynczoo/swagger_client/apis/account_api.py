# coding: utf-8

"""
AccountApi.py
Copyright 2016 SmartBear Software

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from __future__ import absolute_import

import sys
import os

# python 2 and python 3 compatibility library
from six import iteritems

from ..configuration import Configuration
from ..api_client import ApiClient


class AccountApi(object):
    """
    NOTE: This class is auto generated by the swagger code generator program.
    Do not edit the class manually.
    Ref: https://github.com/swagger-api/swagger-codegen
    """

    def __init__(self, api_client=None):
        config = Configuration()
        if api_client:
            self.api_client = api_client
        else:
            if not config.api_client:
                config.api_client = ApiClient()
            self.api_client = config.api_client

    def accounts_get(self, page, page_size, **kwargs):
        """
        get all account
        this endpoint returns all account's

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please define a `callback` function
        to be invoked when receiving the response.
        >>> def callback_function(response):
        >>>     pprint(response)
        >>>
        >>> thread = api.accounts_get(page, page_size, callback=callback_function)

        :param callback function: The callback function
            for asynchronous request. (optional)
        :param float page: the start page. (required)
        :param float page_size: item size pre page. (required)
        :return: PageAccount
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ['page', 'page_size']
        all_params.append('callback')

        params = locals()
        for key, val in iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method accounts_get" % key
                )
            params[key] = val
        del params['kwargs']

        # verify the required parameter 'page' is set
        if ('page' not in params) or (params['page'] is None):
            raise ValueError("Missing the required parameter `page` when calling `accounts_get`")
        # verify the required parameter 'page_size' is set
        if ('page_size' not in params) or (params['page_size'] is None):
            raise ValueError("Missing the required parameter `page_size` when calling `accounts_get`")

        resource_path = '/accounts'.replace('{format}', 'json')
        method = 'GET'

        path_params = {}

        query_params = {}
        if 'page' in params:
            query_params['page'] = params['page']
        if 'page_size' in params:
            query_params['pageSize'] = params['page_size']

        header_params = {}

        form_params = {}
        files = {}

        body_params = None

        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.\
            select_header_accept(['application/json'])
        if not header_params['Accept']:
            del header_params['Accept']

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.\
            select_header_content_type([])

        # Authentication setting
        auth_settings = []

        response = self.api_client.call_api(resource_path, method,
                                            path_params,
                                            query_params,
                                            header_params,
                                            body=body_params,
                                            post_params=form_params,
                                            files=files,
                                            response_type='PageAccount',
                                            auth_settings=auth_settings,
                                            callback=params.get('callback'))
        return response

    def accounts_account_id_get(self, account_id, **kwargs):
        """
        get the account info by accountId
        this endpoint returns account's info, include group,user,vnf.

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please define a `callback` function
        to be invoked when receiving the response.
        >>> def callback_function(response):
        >>>     pprint(response)
        >>>
        >>> thread = api.accounts_account_id_get(account_id, callback=callback_function)

        :param callback function: The callback function
            for asynchronous request. (optional)
        :param str account_id: account id (required)
        :return: AccountInfo
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ['account_id']
        all_params.append('callback')

        params = locals()
        for key, val in iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method accounts_account_id_get" % key
                )
            params[key] = val
        del params['kwargs']

        # verify the required parameter 'account_id' is set
        if ('account_id' not in params) or (params['account_id'] is None):
            raise ValueError("Missing the required parameter `account_id` when calling `accounts_account_id_get`")

        resource_path = '/accounts/{accountId}'.replace('{format}', 'json')
        method = 'GET'

        path_params = {}
        if 'account_id' in params:
            path_params['accountId'] = params['account_id']

        query_params = {}

        header_params = {}

        form_params = {}
        files = {}

        body_params = None

        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.\
            select_header_accept(['application/json'])
        if not header_params['Accept']:
            del header_params['Accept']

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.\
            select_header_content_type([])

        # Authentication setting
        auth_settings = []

        response = self.api_client.call_api(resource_path, method,
                                            path_params,
                                            query_params,
                                            header_params,
                                            body=body_params,
                                            post_params=form_params,
                                            files=files,
                                            response_type='AccountInfo',
                                            auth_settings=auth_settings,
                                            callback=params.get('callback'))
        return response
