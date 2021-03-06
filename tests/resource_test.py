# -*- coding: utf-8 -
#
# Copyright (c) 2008 (c) Benoit Chesneau <benoitc@e-engura.com> 
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
import os
import socket
import threading
import unittest
import urlparse
import urllib2

from restclient.transport import HTTPLib2Transport
from restclient.rest import Resource, RestClient
from restclient.errors import RequestFailed, ResourceNotFound, \
Unauthorized, RequestError


from _server_test import HOST, PORT, run_server_test


class RestClientTestCase(unittest.TestCase):
    
    def setUp(self):
        self.transport = transport = HTTPLib2Transport()
        self.client = RestClient(transport)
        
    def testMakeUri(self):
        self.assert_(self.client.make_uri("http://localhost", "/") == "http://localhost/")
        self.assert_(self.client.make_uri("http://localhost/") == "http://localhost/")
        self.assert_(self.client.make_uri("http://localhost/", "/test/echo") == "http://localhost/test/echo")
        self.assert_(self.client.make_uri("http://localhost/", "/test/echo/") == "http://localhost/test/echo/")
        self.assert_(self.client.make_uri("http://localhost", "/test/echo/") == "http://localhost/test/echo/")
        self.assert_(self.client.make_uri("http://localhost", "test/echo") == "http://localhost/test/echo")
        self.assert_(self.client.make_uri("http://localhost", "test/echo/") == "http://localhost/test/echo/")
        
class ResourceTestCase(unittest.TestCase):

    def setUp(self):
        run_server_test()
        self.transport = transport = HTTPLib2Transport()
        self.url = 'http://%s:%s' % (HOST, PORT)
        self.res = Resource(self.url, transport)

    def tearDown(self):
        self.res = None

    def testGet(self):
        result = self.res.get()
        self.assert_(result == "welcome")
        self.assert_(self.res.response.status == 200)

    def testUnicode(self):
        result = self.res.get('/unicode')
        self.assert_(result == u"éàù@")

    def testUrlWithAccents(self):
        result = self.res.get('/éàù')
        self.assert_(result == "ok")
        self.assert_(self.res.response.status == 200)

    def testUrlUnicode(self):
        result = self.res.get(u'/test')
        self.assert_(result == "ok")
        self.assert_(self.res.response.status == 200)
        result = self.res.get(u'/éàù')
        self.assert_(result == "ok")
        self.assert_(self.res.response.status == 200)

    def testGetWithContentType(self):
        result = self.res.get('/json', headers={'Content-Type': 'application/json'})
        self.assert_(self.res.response.status == 200)
        def bad_get():
            result = self.res.get('/json', headers={'Content-Type': 'text/plain'})
        self.assertRaises(RequestFailed, bad_get) 

    def testGetWithContentType2(self):
        res = Resource(self.url, self.transport, 
                headers={'Content-Type': 'application/json'})
        result = res.get('/json')
        self.assert_(res.response.status == 200)
        

    def testNotFound(self):
        def bad_get():
            result = self.res.get("/unknown")

        self.assertRaises(ResourceNotFound, bad_get)

    def testGetWithQuery(self):
        result = self.res.get('/query', test="testing")
        self.assert_(self.res.response.status == 200)

    def testGetWithIntParam(self):
        result = self.res.get('/qint', test=1)
        self.assert_(self.res.response.status == 200)

    def testSimplePost(self):
        result = self.res.post(payload="test")
        self.assert_(result=="test")

    def testPostByteString(self):
        result = self.res.post('/bytestring', payload="éàù@")
        self.assert_(result == u"éàù@")

    def testPostUnicode(self):
        result = self.res.post('/unicode', payload=u"éàù@")
        self.assert_(result == u"éàù@")

    def testPostWithContentType(self):
        result = self.res.post('/json', payload="test",
                headers={'Content-Type': 'application/json'})
        self.assert_(self.res.response.status == 200 )
        def bad_post():
            result = self.res.post('/json', payload="test",
                    headers={'Content-Type': 'text/plain'})
        self.assertRaises(RequestFailed, bad_post)

    def testEmptyPost(self):
        result = self.res.post('/empty', payload="",
                headers={'Content-Type': 'application/json'})
        self.assert_(self.res.response.status == 200 )
        result = self.res.post('/empty',headers={'Content-Type': 'application/json'})
        self.assert_(self.res.response.status == 200 )

    def testPostWithQuery(self):
        result = self.res.post('/query', test="testing")
        self.assert_(self.res.response.status == 200)
    
    def testPostForm(self):
        result = self.res.post('/form', payload={ "a": "a", "b": "b" })
        self.assert_(self.res.response.status == 200)

    def testSimplePut(self):
        result = self.res.put(payload="test")
        self.assert_(result=="test")

    def testPutWithContentType(self):
        result = self.res.put('/json', payload="test",
                headers={'Content-Type': 'application/json'})
        self.assert_(self.res.response.status == 200 )
        def bad_put():
            result = self.res.put('/json', payload="test",
                    headers={'Content-Type': 'text/plain'})
        self.assertRaises(RequestFailed, bad_put)

    def testEmptyPut(self):
        result = self.res.put('/empty', payload="",
                headers={'Content-Type': 'application/json'})
        self.assert_(self.res.response.status == 200 )
        result = self.res.put('/empty',headers={'Content-Type': 'application/json'})
        self.assert_(self.res.response.status == 200 )

    def testPutWithQuery(self):
        result = self.res.put('/query', test="testing")
        self.assert_(self.res.response.status == 200)

    def testHead(self):
        result = self.res.head('/ok')
        self.assert_(self.res.response.status == 200)

    def testDelete(self):
        result = self.res.delete('/delete')
        self.assert_(self.res.response.status == 200)

    def testFileSend(self):
        content_length = len("test")
        import StringIO
        content = StringIO.StringIO("test")
        result = self.res.post('/json', payload=content,
                headers={
                    'Content-Type': 'application/json',
                    'Content-Length': str(content_length)
                })

        self.assert_(self.res.response.status == 200 )

    def testFileSend2(self):
        import StringIO
        content = StringIO.StringIO("test")

        def bad_post():
            result = self.res.post('/json', payload=content,
                headers={'Content-Type': 'application/json'})

        self.assertRaises(RequestError, bad_post)

    def testAuth(self):
        transport = HTTPLib2Transport()
        transport.add_credentials("test", "test")

        res = Resource(self.url, transport)
        result = res.get('/auth')
        self.assert_(res.response.status == 200)

        transport = HTTPLib2Transport()
        def niettest():
            res = Resource(self.url, transport)
            result = res.get('/auth')
        self.assertRaises(Unauthorized, niettest)
        
    

 
    
if __name__ == '__main__':
    from _server_test import run_server_test
    run_server_test() 
    unittest.main()
