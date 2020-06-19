#!/usr/bin/python3
"""
Defines a custom node model
"""

from hashlib import sha1
import hmac
import random
import codecs
import time
from urllib.parse import quote
import base64
import os
import models
from models.base import BaseNode, Base
from sqlalchemy import Column, String, Integer, ForeignKey
import json
import requests
from models.auth import Auth

auth = Auth()


class CustomNode(BaseNode, Base):
    """
    This model stores the needed data for the nodes
    """
    __tablename__ = 'custom_nodes'
    user_id = Column(String(60), ForeignKey('users.id'), nullable=False)
    name = Column(String(60))
    # Request or process
    work_type = Column(String(20), default='request')
    # Format 'GET https://example.com
    api_url = Column(String(100), default='')
    # Format 'users/{id}/nodes' this depends on self.data
    api_endpoint = Column(String(100), default='')
    string = Column(String(200))
    # Format { key1:value1, key2:value2 }
    headers = Column(String(500), default='{}')
    # Format [ id1, id2, id3 ]
    innodes = Column(String(2000), default='[]')
    # Query data will store a JSON string
    # Format { key1:value1, key2:value2 }
    data = Column(String(2000), default='{}')
    # Format [ id1, id2, id3 ]
    outnodes = Column(String(2000), default='[]')
    """scrapping, JSON, comparision (for the triggers)
    work_type == process and analisis_mode == 'comparision'
    analisis_params format should be
    [{value1:, value2:, cond:}]
    and the Response will be Boolean True or false"""
    analisis_mode = Column(String(20), default='JSON')
    # format [{ key: 'field', stop_val: '>' , path: ''}]
    analisis_params = Column(String(2000), default='[]')
    trigger = Column(String(5))  # True or False
    timeout = Column(Integer, default=0)
    # Format {outnodes}
    inner_connections = Column(String(2000), default='')
    # Default node color
    color = Column(String(16), default='#9bfa18')
    board_id = Column(String(60), default='')
    # content = Column(String(16), default='', nullable=True)
    # # this will store the inode request response

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return json.dumps(self.__dict__)

    def request(self, data):
        """
        Makes a request using the model data and a
        """
        # print('------------------------------')
        # print('\tRequest by', self.name)
        # print('------------------------------')

        if len(self.api_url) <= 0:
            # print('No URL defined')
            return (None, None)
        protocol, url = self.api_url.split(' ')
        headers = {}
        response = None
        url += self.parse_endpoint()
        if self.headers != '{}':
            headers = json.loads(self.headers)
            # # print(headers)
        # print(headers, type(headers), '\n',
        #    protocol, url, '\n', data, type(data))
        try:
            if protocol == 'GET':
                response = requests.get(url, params=data, headers=headers)
            elif protocol == 'POST':
                response = requests.post(url, params=data, headers=headers)
            # print('\033[34m*************Response*********')
            # # print('*{:<30}*'.format(str(response.content)))
            # print('*{:<30}*'.format(str(response.json())))
            # # print('*{:<30}*\033[0m'.format(str(response.reason)))
            # print('*******************************\033[0m')
        except Exception as e:
            # # print('An error has ocurred while requesting,
            #  maybe there are not internet connection')
            print('\033[31mRequest Error\033[0m', e)
        if response.status_code == 200:
            try:
                # print(self.name, json.dumps(response.json(), indent=2))
                response = response.json()
            except Exception as e:
                # print(e)
                response = response.content
        else:
            response = {'error': response.reason,
                        'message': response.json()['errors'][0]['message'],
                        'code': response.status_code}
        # # print(response.json())
        # # print(response.json())
        return response, response

    def processResponse(self, response):
        """
        Process the received result from request to
        the formated output fields defined by
        analisis_mode: scrapping, parse json
        analisis_params: {key:, stop_val:, path}
        """
        resp = {}
        # print(self.name, self.analisis_mode)
        # # print(type(self.analisis_params) == dict)
        if type(self.analisis_params) != dict:
            params = json.loads(self.analisis_params)
        else:
            params = self.analisis_params
        # print('\033[33mprocessing:\033[0m ', self.name)
        # # print(self.analisis_mode)
        if self.analisis_mode == 'comparision':
            # print('##  Comparission mode  ##')
            # # print('processing input', params, response)
            cond = None
            val1 = None
            val2 = None
            for par in params:
                if 'key' in par:
                    val1 = par['key']
                if 'comp' in par:
                    val2 = par['comp']
                if 'cond' in par:
                    cond = par['cond']
            # print(val1, cond, val2)
            val1 = response[val1]
            res = eval(val1 + ' ' + cond + ' ' + val2)
            # print(res)
            if not res:
                return False
            return res
        if self.analisis_mode == 'gen_signature':
            # print('==========Gen Signature=============')

            r = response
            # print(r)
            method, url = r['url'].split(' ')
            data = json.loads(self.analisis_params)
            sign = auth.gen_sig(data[0],
                                data[1], r['data'], url, method)
            # print(sign)
            # print('====================================')
            return sign
        # this process extracts the data from the reponse object
        if len(params) > 0:
            for param in params:
                # # print(json.dumps(param, indent=2))
                paths = param['path'].split('/')
                # print(self.name, self.analisis_mode)
                # print('paths: ', paths)
                obj = response
                last = len(paths) - 1
                for i, path in enumerate(paths):
                    try:
                        index = int(path)
                        obj = obj[index]
                    except Exception:
                        if path in obj:
                            obj = obj[path]
                    if last == i:
                        resp[param['key']] = obj
            if self.analisis_mode == 'get_updates':
                # print('\n\tgetting updates\n')
                # print(resp[param['key']])
                obj = resp[param['key']]
                count = json.loads(self.data)['count']
                # print(count)
                self.logger.log(self.name, param['key'] + ' length is ' + str(len(obj)))
                if len(obj) > int(count):
                    # print('there is a new record')
                    # print(obj[len(obj) - 1])
                    # TODO
                    # set the counter to the new value
                    data = json.loads(self.data)
                    data['count'] = int(len(obj)) - 1
                    self.data = json.dumps(data)
                    self.save()
                    return obj[len(obj) - 1]
                else:
                    return {}
                # print('------------------')
            return resp
        else:
            if self.analisis_mode == 'replace':
                # print(self.string)
                parsed = self.parse_string(self.string, response)
                # print('\033[36mparsed string:\033[0m\n\t', parsed,)
                return parsed
            return response

    def run_node_task(self, params, logger):
        """
        If response is an empty dict, makes the request with the stored data,
        if the task is called from another node process it will use the data
        comming that node
        """
        self.logger = logger
        logger.log(self.name, 'Running task')
        # print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        # print('\t\tRun', self.name, 'task\nParams:\n', params)
        # print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        data = {}
        json_log = {}
        complete = None
        rand = ''
        tmp_data = None
        time = ''  # tag for the nounce generated values
        if len(json.loads(self.innodes)) > 0:
            logger.log(self.name, 'Checking innodes')
            innodes = json.loads(self.innodes)
            node = models.storage.get(CustomNode, innodes[0])
            if node.analisis_mode == 'gen_signature':
                logger.log(self.name, 'innode -> gen_signature mode')
                heads = {}
                heads['data'] = json.loads(self.headers)
                for h in heads['data'].keys():
                    if heads['data'][h] == 'random':
                        rand = h
                        heads['data'][h] = auth.gen_nonce()
                    elif heads['data'][h] == 'time':
                        time = h
                        heads['data'][h] = auth.get_time()
                heads['url'] = self.api_url
                tmp_data = self.data
                logger.log(self.name, 'Replacing ' + ' in ' + json.dumps(params))
                dat = self.data.replace('*content*', params)
                dat = json.loads(dat)
                dat['status'] += ' {}'.format(auth.get_time())
                self.data = json.dumps(dat)
                # heads['data'] = params
                heads['data']['status'] = dat['status']
                # print('incoming params to', node.name, '\n', heads)
                data, json_log = node.run_node_task(heads, logger)
                headers = json.loads(self.headers)
                if rand in headers:
                    headers[rand] = heads['data'][rand]
                if time in headers:
                    headers[time] = heads['data'][time]
                headers['oauth_signature'] = data
                self.headers = json.dumps(headers)
            else:
                data, json_log = node.run_node_task(params, logger)
            # # print(data)
        # Handles the request if the worker is request
        # take in count the headers
        # and the behavior give by the innodes-data response
        if self.work_type == 'request':
            logger.log(self.name, 'Request mode')
            # print('.......................')
            # print('Request from', self.name)
            # print('data:', data, '\nparams:', params)
            headers = {}
            tmp_headers = self.headers
            need_auth = False
            for head in json.loads(self.headers):
                if 'auth' in head:
                    need_auth = True
            if need_auth:
                headers['Authorization'] = auth.gen_header(
                    json.loads(self.headers))
                # print('headers: ', self.headers)
                # print('___result_headers___')
                # print(headers)
                self.headers = json.dumps(headers)
            # print('.......................')
            data, json_log = self.request(self.parse_data(data))
            self.headers = tmp_headers
            # search signature an delete it from model,
            # also restart nounce 'random' tag
            headers = json.loads(self.headers)
            if 'oauth_signature' in headers:
                del headers['oauth_signature']
            if rand in headers:
                headers[rand] = 'random'
            if time in headers:
                headers[time] = 'time'
            self.headers = json.dumps(headers)
            if tmp_data:
                self.data = tmp_data
            self.save()
        # Set this variable to be able to call multiple innodes
        # The data here is filtered by the analisis_params parameters
        if len(params) > 0:
            data = self.parse_data(params)
        logger.log(self.name, self.analisis_mode)
        data = self.processResponse(data)
        if self.work_type == 'request':
            logger.json_log[self.name] = json_log
        else:
            logger.json_log[self.name] = data
        for key in logger.json_log.keys():
            if type(logger.json_log[key]) is not dict:
                logger.json_log[key] = [logger.json_log[key]]
        # ==================================
        # Now ask if this node has outnodes execute them
        # This needs a way to handle efectively the recursion
        # sucessive nodes are processed in queu system
        # the returned data for each node determines the flow
        if len(json.loads(self.outnodes)) > 0 and len(data) > 0:
            outnodes = json.loads(self.outnodes)
            for nod in outnodes:
                node = models.storage.get(CustomNode, nod)
                if node.analisis_mode == 'comparision':
                    parms = json.loads(node.analisis_params)
                    for i, par in enumerate(parms):
                        if 'value1' in par:
                            del parms[i]
                    parms.append({'value1': data.get(list(data.keys())[0])})
                    node.analisis_params = json.dumps(parms)
                    node.save()
                    data, comp = node.run_node_task(data, logger)
                    if data is False:
                        break
                else:
                    if len(json_log) <= 0:
                        json_log = data
                    data, json_log = node.run_node_task(json_log, logger)
                if type(data) == dict:
                    data = self.parse_data(data)
        return data, json_log

    def colors(self):
        """
        returns a list of color
        """
        return ['#f32e9c', '#932989', '#9bfa18', '#ef912f', '#f9463a']

    def parse_data(self, params):
        """
        Parse the params to take the extends the data object
        """
        data = json.loads(self.data)
        if type(params) == dict:
            for key in params.keys():
                data[key] = params[key]
        return data  # add also the incoming params

    def parse_string(self, format_string, data):
        """
        Search patterns and replace values in the endpoint
        """
        keys = ['{' + k + '}' for k in data.keys()]
        # # print(format, data)
        resp = format_string
        for i, k in enumerate(keys):
            resp = resp.replace(str(k), str(data[k[1:-1]]))
        # # print(format_string)
        # # print('parsed response', resp)
        return resp

    def parse_endpoint(self):
        """
        Search patterns and replace values in the endpoint
        """
        keys = ['{' + k + '}' for k in self.parse_data({}).keys()]
        resp = self.api_endpoint
        for k in keys:
            resp = resp.replace(k, self.parse_data({})[k[1:-1]])
        return resp
