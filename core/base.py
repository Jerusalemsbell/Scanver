#!/usr/bin/env python
# encoding=utf-8
#codeby     道长且阻
#email      @ydhcui/QQ664284092
#https://github.com/ydhcui/Scanver


import requests
from requests import Session,Request  
import re
import socket
import urllib.parse as urlparse
import settings
from core.cmsfind import CmsFind
#CMS = CmsFind(settings.DATAPATH + '/cmsdata.json')

####################################
class BaseHost(object):
    '''主机'''
    def __init__(self,host,port,service='unknow'):
        self.host = host
        self.port = int(port)
        self.service = service

class BaseWebSite(BaseHost):
    '''定义一个网站的基类'''
    def __init__(self,url,proxy={},session=None,load=True):
        self.proxy = proxy
        self.session = session or Session()
        if url and url.startswith('//'):
            url = 'http:'+url
        if url and not url.upper().startswith('HTTP'):
            url = 'http://%s'%url
        self.url      = url
        parser        = urlparse.urlsplit(self.url)
        self.scheme   = parser.scheme #https
        self.netloc   = parser.netloc #www.baidu.com
        self.path     = parser.path   #www.baidu.com
        self.domain   = self.netloc
        self.host     = self.gethostbyname(self.netloc.split(':')[0])
        try:
            self.port = self.netloc.split(':')[1]
        except:
            self.port = 443 if self.scheme.upper() == 'HTTPS' else 80
        BaseHost.__init__(self,self.host,self.port,self.scheme)
        self.status_code= 0
        self._content   = set() #struts2 dedecms ...
        self.headers    = {}
        self.server     = '|' #Server: nginx/1.8.0 #Apache Tomcat/7.0.59
        self.xpoweredby = '|' #X-Powered-By: PHP/5.6.31'
        self.title      = ''
        self.cmsver     = ''
        try:
            self.load()
        except:
            pass
        if load:
            #self.cmsver = '|'.join(list(CMS.load(self.url)))
            if 'JSP' in self.xpoweredby:
                server = self.javaserver()
                self.server = server + '|' + self.server if server else res.headers.get('Server')

    def load(self):
        url = self.url + "/pag404.php.jsp.asp.js.jpg.%s"%self.host
        res = self.session.get(url,verify=False,proxies=self.proxy,timeout=60)
        self.page404 = res
        self.headers = res.headers
        self.server = res.headers.get('Server',self.server)
        xpoweredby1 = res.headers.get('X-Powered-By','')
        xpoweredby2 = self.findxpoweredby(res)
        self.xpoweredby = xpoweredby2+'|'+self.xpoweredby if xpoweredby2 else xpoweredby1
        res = self.session.get(self.url,verify=False,proxies=self.proxy,timeout=60)
        self.status_code = res.status_code
        text = res.text
        code = res.encoding or 'utf8'
        if text:
            self.title = ''.join(
                    re.findall(r"<title>([\s\S]*?)</title>",
                    text.encode(code).decode('utf-8'),
                    re.I))
        self.server = res.headers.get('Server',self.server)
        xpoweredby3 = res.headers.get('X-Powered-By',self.xpoweredby)
        xpoweredby4 = self.findxpoweredby(res)
        self.xpoweredby = xpoweredby4 + '|' + self.xpoweredby if xpoweredby4 else xpoweredby3+'|'+self.xpoweredby
        
    @staticmethod
    def findxpoweredby(res):
        xpoweredby = ' '
        headers = str(res.headers)
        content = res.text
        if 'ASP.NET' in headers or 'ASPSESSIONID' in headers:
            xpoweredby += '|ASP'
        if 'PHPSESSIONID' in headers:
            xpoweredby += '|PHP'
        if 'JSESSIONID' in headers:
            xpoweredby += '|JSP'
        if re.search(r'name="__VIEWSTATE" id="__VIEWSTATE"',content):
            xpoweredby += '|ASP'
        """
        if re.search(r'''href[\s]*=[\s]*['"][./a-z0-9]*\.jsp[x'"]''',content,re.I):
            xpoweredby += 'JSP'
        if re.search(r'''href[\s]*=[\s]*['"][./a-z0-9]*\.action['"]''',content,re.I):
            xpoweredby += 'JSP'
        if re.search(r'''href[\s]*=[\s]*['"][./a-z0-9]*\.do['"]''',content,re.I):
            xpoweredby += 'JSP'
        if re.search(r'''href[\s]*=[\s]*['"][./a-z0-9]*\.asp[x'"]''',content,re.I):
           xpoweredby += 'ASP'
        if re.search(r'''href[\s]*=[\s]*['"][./a-z0-9]*\.php[\?'"]''',content,re.I):
           xpoweredby += 'PHP'
        """
        return xpoweredby
    @staticmethod
    def javaserver(res):
        server = ' '
        tomcat = ''.join(re.findall("<h3>(.*?)</h3>",res.text))
        weblogic = ''.join(re.findall("<H4>(.*?)404 Not Found</H4>",res.text))
        if 'Tomcat' in res.text:
            server = tomcat
        if 'Hypertext' in res.text:
            server = 'Weblogic '+weblogic
        return server
    @staticmethod
    def gethostbyname(name):
        '''域名查ip'''
        try:
            return socket.gethostbyname(name)
        except socket.gaierror:
            return name
    @property
    def content(self):
        for s in self.server.split('|') + self.xpoweredby.split('|'):
            if s:self._content.add(s.strip())
        if self.cmsver:
            self._content.add(self.cmsver.strip())
        return '|'.join(self._content).lower()
    @content.setter
    def content(self,value):
        self._content.add(value)

class BaseRequest(object):
    '''定义一个http请求的基类'''
    def __init__(self,url,data={},method='GET',headers={},
        files={},cookies={},auth=None,hooks=None, json=None,
        session=None,proxy={}):
        if url and((url.startswith('//'))or(not url.upper().startswith('HTTP'))):
            url = 'http:'+url
        self.url    = url
        self.method = method.strip()
        self.version= 'HTTP/1.1'
        parser      = urlparse.urlsplit(self.url)
        self.scheme = parser.scheme #https
        self.netloc = parser.netloc #www.baidu.com
        self.path   = parser.path   #/params.php
        self.params = dict([q.split('=')[:2] for q in parser.query.split('&') if '=' in q])
        self.headers= {
            "User-Agent":"Mozilla/Scanolv1.1",
            "Accept-Language":"zh-CN,zh;q=0.8",
            "Connection":"keep-alive",
            "Referer":'%s://%s/'%(self.scheme,self.netloc),}
        self.headers.update(headers)
        if data and method == 'GET':
            self.params.update(data)
            self.data   = {}
        else:
            self.data   = data
        self.auth   = auth 
        self.json   = json
        self.cookies= cookies
        self.proxy  = proxy
        self.files  = files or []
        self.session= session or Session() 
        
    def __repr__(self):
        s=[]
        s.append("%s %s %s"%(
            self.method.upper(),
            '%s?%s'%(self.path,
                '&'.join(['%s=%s'%(k,v) for k,v in self.params.items()])) \
                if self.params else self.path,
            self.version))
        s.append('Host: %s'%(self.netloc))
        for k,v in self.headers.items():
            s.append("%s: %s"%(k,v))
        if self.data:
            data = "&".join(["%s=%s"%(k,v) for k,v in self.data.items()])
            s.append('Content-Length: %d\r\n'%(len(data)))
            s.append(data)
        else:
            s.append('\r\n')
        return '\r\n'.join(s)

    def prepare(self):
        return Request(
            method=self.method,
            url='%s://%s%s'%(self.scheme,self.netloc,self.path),
            headers=self.headers,
            files=self.files,
            data=self.data,
            json=self.json,
            params=self.params,
            auth=self.auth,
            cookies=self.cookies,
        )

    def response(self):
        req = self.session.prepare_request(self.prepare())
        res = self.session.send(req,proxies=self.proxy,verify=False)
        logging.info("%s-%s-%s"%(res.status_code,req.method,req.url))
        return res
            
    def _diff(self):
        return (self.method,self.netloc,self.path,
            ''.join(self.params.keys()),
            ''.join(self.data.keys()),)
    def __eq__(self,req):
        return self._diff() == req._diff()

    def __hash__(self):
        return hash(self._diff_())

class ConnectionError(requests.ConnectionError):
    pass


if __name__ == '__main__':
    u=[
        'http://127.0.0.1/www',
    ]
    for i in u:
        s = BaseWebSite(i)
        print(s.server,s.xpoweredby)