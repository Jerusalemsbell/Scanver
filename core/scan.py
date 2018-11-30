#!/usr/bin/env python
# encoding=utf-8
#codeby     道长且阻
#email      ydhcui@suliu.net/QQ664284092
#https://github.com/ydhcui/Scanver

import socket
import re
import os
import sys
import traceback
import time
import json
import urllib
import threading
import datetime
import copy
import queue
from lib import requests
from lib.dns.resolver import Resolver

from core.websearch import BaiduEngine,SogouEngine,SoEngine,BingEngine
from core.plugin import PluginsManage,BaseHttpPlugin,BaseWebPlugin,BaseHostPlugin
from core.crawler1 import Crawler
#from core.nmapscan import PortScan
from core.portscan import PortScan
from core.util import gethosts,getfiles,getports,getdomain,CoroutinePool
from core.base import BaseHost,BaseWebSite
from core.log import logging
from service import app

import models
import settings
requests.packages.urllib3.disable_warnings()

class BaseScan(object):
    @classmethod
    def gethttptitle(self):    
        MP = models.PortResult
        sw = MP.port_type == 'tcp'
        sw &= MP.service_name == 'http'
        pool = CoroutinePool(10)
        for q in MP.select().where(sw):
            pool.spawn(self.selecthttp,q)
            #self.selecthttp(q)
        pool.join()
        print('task done')
    @classmethod
    def selecthttp(self,q):
        '''获取http服务的headers信息'''
        h = str(q.host)
        p = str(q.port)
        print(h,p)
        pto = 'https' if ('443' in p or str(q.status_code) == '400')  else 'http'
        url = '%s://%s:%s/'%(pto, h, p)
        w = BaseWebSite(url,load=False)
        q.port_type = 'tcp/http/%s'%self.writewebsite(w)
        q.save()
    @classmethod
    def writewebsite(self,w):
        logging.info("Writewebsite %s %s %s %s "%(w.status_code,w.host,w.port,w.domain))
        r,cd = models.HttpResult.get_or_create(host=w.host,port=w.port)
        r.state     = w.status_code
        r.banner    = w.server
        r.domain    = w.domain
        r.xpoweredby= w.xpoweredby
        r.title     = w.title
        r.headers   = w.headers
        r.content   = w.content
        r.updatedate= datetime.datetime.now()
        r.save()

    def __init__(self,taskid):
        PluginsManage.load('./payloads')
        M = models.ScanTask
        self.Q = M.get(M.task_id==taskid)
        self.T = app.AsyncResult(taskid)
        self.settings = {}
        self.target = None
        self.args = json.loads(self.Q.task_args)
        self.target = str(self.Q.task_host).strip()
        '''
        int(self.args.get('filter',1))      #是否使用过滤
        int(self.args.get('write',1))       #是否覆盖原先的扫描结果
        int(self.args.get('ping',0))        #是否使用ping过滤主机
        int(self.args.get('threads',100))   #扫描线程数
        int(self.args.get('timeout',10))    #超时时间
        str(self.args.get('port',''))       #要扫描的端口
        int(self.args.get('level',1))       #是否扫描POST请求
        str(self.args.get('plug',''))       #扫描的插件
        dict(self.args.get('headers',"{}")) #自定义请求头
        '''
    def scan(self):
        pass

    def set_settings(self,*args,**kwargs):
        self.settings.update(kwargs)

    def start(self):
        self.Q.task_code = 'working'
        self.Q.task_pid = str(os.getpid())
        self.Q.save()
        try:
            self.auths = self.get_auth()
            self.scan()
        except Exception as e:
            type,value,tb = sys.exc_info()
            e = '\n'.join(set(traceback.format_exception(type,value,tb)))
            logging.error(str(e))
        finally:
            self.Q.finishdate = datetime.datetime.now()
            self.Q.task_pid  = '0'
            self.Q.task_code  = 'finish'
            self.Q.save()

    def get_auth(self,pwds=None):
        '''获取项目用户名密码'''
        pwds = getfiles(settings.DATAPATH + '/pass.txt')
        MD = models.DictResult
        auths = set()
        #读取库中本项目的用户名和密码
        userquery = MD.select().where((MD.projectid == self.Q.projectid)&(MD.dict_key == 'user'))
        pwdquery = MD.select().where((MD.projectid == self.Q.projectid)&(MD.dict_key == 'pwd'))
        for u in userquery:
            for p in pwdquery:
                auths.add((str(u.dict_value),str(p.dict_value)))
        #for u in userquery:
        #    auths.add((str(u.dict_value),None))
        for p in pwdquery:
            auths.add((None,str(p.dict_value)))
        if pwds:#本地密码
            for pwd in pwds:
                auths.add((None,pwd))
        return auths

    def payloadverify(self,plug,host):
        '''插件验证'''
        #logging.info('check %s-%s-%s'%(plug.__class__,host.host,host.port))               
        filter = int(self.args.get('filter',1)) #是否需要过滤、
        try:
            socket.setdefaulttimeout(360)
            if not filter or plug.filter(host):
                logging.info('filter %s-%s-%s-%s'%(plug.__class__,host.service,host.host,host.port))
                for user,pwd in self.auths if plug.BRUTE else [(None,'123456')]:
                    if user:
                        verify = plug.verify(host,user=user,pwd=pwd)
                    else:
                        verify = plug.verify(host,pwd=pwd)
                    if verify:
                        logging.warn('verify %s-%s-%s-%s-%s'%(plug.__class__,host.host,host.port,user,pwd))
                        return self.callback_bug(plug)
        except Exception as e:
            type,value,tb = sys.exc_info()
            e = '\n'.join(set(traceback.format_exception(type,value,tb)))
            logging.error(str(e))

    def callback_bug(self,payload):
        '''回调写入漏洞信息'''
        RV,cd = models.Vulnerable.get_or_create(vul_name = payload.bugname)
        if cd:
            RV.vul_desc     = payload.bugdesc
            RV.vul_plan     = payload.bugplan
            RV.vul_rank     = payload.bugrank
            RV.vul_owasp    = payload.bugowasp
            RV.vul_number   = payload.bugnumber
            RV.save()
        addr = payload.bugaddr
        RB,cd = models.BugResult.get_or_create(
            taskid      = self.Q,
            projectid   = self.Q.projectid,
            userid      = self.Q.projectid.project_user,
            vulid       = RV,
            bug_addr    = addr)
        RB.bug_tag      = payload.bugtag
        RB.bug_note     = payload.bugnote
        RB.request      = payload.bugreq
        RB.response     = payload.bugres
        RB.updatedate   = datetime.datetime.now()
        RB.save()

    def writehost(self,ret):
        '''写入端口扫描结果'''
        for host,value in ret.items():
            RH,created      = models.HostResult.get_or_create(projectid = self.Q.projectid, host_ip = host)
            RH.userid       = self.Q.projectid.project_user
            RH.host_name    = value['hostname']
            #RH.os_version   = value['status']
            RH.mac_addr     = value['mac']
            RH.updatedate   = datetime.datetime.now()
            RH.note         = value['status']
            RH.os_type      = value['ostype']
            RH.save()
            for host,port,protocol,state,service,product,extrainfo,version,data in value['ports']:
                RP,created      = models.PortResult.get_or_create(hostid=RH,host=RH.host_ip,port=port)
                RP.port_type    = protocol
                RP.port_state   = state
                RP.service_name = service
                RP.soft_name    = product
                RP.soft_type    = extrainfo
                RP.soft_ver     = version
                RP.response     = str(data)
                RP.updatedate   = datetime.datetime.now()
                RP.save()

    def portscan(self,target):
        '''端口扫描'''
        write = int(self.args.get('write',1))
        ping = int(self.args.get('ping',0))
        threads = int(self.args.get('threads',100))
        timeout = int(self.args.get('timeout',5))
        isfilter = int(self.args.get('isfilter'),0)
        ports = self.args.get('port',None)
        block = self.args.get('block',[])

        logging.info('[portscan][host:%s][port:%s][write:%s][ping:%s][threads:%s][timeout:%s]'%(target,ports,write,ping,threads,timeout))

        target = set(gethosts(target))
        target = target.difference(set(block))
        if isfilter:
            H = models.HostResult
            hosts = set([(h.host_ip) for h in H.select().where(H.projectid = self.Q.projectid)])
            target = target.difference(hosts)

        ps = PortScan(
                target,
                ports = ports,
                neping = ping,
                threads = threads,
                timeout = timeout)
        self.writehost(ps.scan())

class HttpScan(BaseScan):
    def webscan(self):
        pool = CoroutinePool(3)
        for payload in BaseWebPlugin.payloads():
            pool.spawn(self.payloadverify,payload,self.crawle.website)
        pool.join()

    def httpscan(self):
        while self.crawle.ISSTART or not self.crawle.ResQueue.empty():
            try:
                req,res = self.crawle.ResQueue.get(block=False)
                #print(res.status_code,req.url)
                req = copy.deepcopy(req)
                res = copy.deepcopy(res)
                for payload in BaseHttpPlugin.payloads():
                    try:
                        payload.filter(self.crawle,req,res) \
                        and payload.verify(self.crawle,req,res) \
                        and self.callback_bug(payload)
                    except Exception as e:
                        print(e)
            except queue.Empty:
                pass
            except Exception as e:
                type,value,tb = sys.exc_info()
                e = '\n'.join(set(traceback.format_exception(type,value,tb)))
                logging.error(str(e))

    def scan(self):
        headers = json.loads(self.args.get('headers',"{}"))
        proxy= json.loads(self.args.get('proxy',"{}"))
        level = int(self.args.get('level',1)) #post 扫描
        threads = int(self.args.get('threads',10))
        timeout = int(self.args.get('timeout',60))
        sleep = int(self.args.get('sleep',2))

        if not self.target.startswith(('http','HTTP')):
            self.target = 'http://' + self.target
        if not self.target.endswith('/'):
            self.target += '/'

        for target in gethosts(self.target):
            self.portscan(target)
        self.crawle = Crawler(self.target,
            level=1,headers=headers,proxy=proxy,threads=threads,timeout=timeout,sleep=sleep)
        #self.crawle.settings.update(self.args)
        #self.crawle.settings.update(proxy={'http':'http://127.0.0.1:1111','https':'http://127.0.0.1:1111'})
        self.crawle.start()
        th=[]
        #th.append(threading.Thread(target=self.crawle.run1))
        th.append(threading.Thread(target=self.webscan))
        th.append(threading.Thread(target=self.httpscan))
        for t in th:
            #t.daemon = True
            t.start()
        for t in th:
            t.join()

        #扫描完成写入httpret结果
        self.writewebsite(self.crawle.website)

class ServiceScan(BaseScan):
    def scan(self):
        #不使用存活扫描时将IP分开来单个扫描保证进度能完整保存
        ping = int(self.args.get('ping',1))
        for target in [self.target] if ping else gethosts(self.target):
            self.portscan(target)

class HostsScan(BaseScan):
    def scan(self):

        MP = models.Project
        MH = models.HostResult
        MR = models.PortResult
        ping = int(self.args.get('ping',0))
        for target in [self.target] if ping else gethosts(self.target):
            self.portscan(target)
        ret = []
        payloads = BaseHostPlugin.payloads() + BaseWebPlugin.payloads()
        for plug in payloads:
            for H in gethosts(self.target):
                for P in MR.select().join(MH).where((MH.host_ip == H)&(MH.projectid == self.Q.projectid)):
                    if isinstance(plug,BaseHostPlugin):
                        host = BaseHost(str(P.host),str(P.port),service=str(P.service_name))
                        ret.append((plug,host))
                    elif str(P.service_name) == 'http':
                        hp = 'https' if '443' in str(P.port) else 'http'
                        url = '%s://%s:%s/'%(hp,str(P.host),str(P.port))
                        host = BaseWebSite(url)
                        ret.append((plug,host))

        pool = CoroutinePool(len(payloads))
        for plug,host in ret:
            pool.spawn(self.payloadverify,plug,host)
        pool.join()

class PluginsScan(BaseScan):
    def scan(self):
        MP = models.Project
        MH = models.HostResult
        MR = models.PortResult

        plug_names = self.args.get('plug','').split(',')
        for plug_name in plug_names:
            logging.info('Scan plug name: %s'%plug_name)
            hosts = self.target
            ret = []
            try:
                R = MP.get(MP.project_id == hosts)
                for H in MH.select().where(MH.projectid == R):
                    ret.append(str(H.host_ip))
            except MP.DoesNotExist:
                for H in gethosts(self.target):
                    ret.append(H)

            wret = []
            hret = []
            for H in ret:
                for P in MR.select().join(MH).where((MH.host_ip == H)&(MH.projectid == self.Q.projectid)):
                    if str(P.service_name) == 'http':
                        hp = 'https' if '443' in str(P.port) else 'http'
                        url = '%s://%s:%s/'%(hp,str(P.host),str(P.port))
                        host = BaseWebSite(url)
                        wret.append(host)
                    else:
                        host = BaseHost(str(P.host),str(P.port),service=str(P.service_name))
                        hret.append(host)

            ret = []
            for plug in PluginsManage.get_plugins(plug_name):
                if isinstance(plug,BaseHostPlugin):
                    for host in hret:
                        ret.append((plug,host))
                elif isinstance(plug,BaseWebPlugin):
                    for host in wret:
                        ret.append((plug,host))

            pool = CoroutinePool(10)
            for plug,host in ret:
                pool.spawn(self.payloadverify,plug,host)
            pool.join()


class DomainScan(BaseScan):
    namelist = getfiles(settings.DATAPATH + '/subdomain.txt')
    def recv(self,domain):
        try:
            answers = self.resolvers.query(domain)
        except:
            answers = []
        return answers

    def baiduce(self,target):
        try:
            res = requests.get('http://ce.baidu.com/index/getRelatedSites?site_address=%s'%target)
            res = json.loads(res.text)
            for subdomain in [v.get('domain') for v in res.get('data',[])]:
                for answer in self.recv(subdomain):
                    self.result.add((subdomain,answer.address))
        except:pass

    def brute(self,target):
        target = target.strip()
        for subdomain in self.namelist:
            subdomain = subdomain.strip() + '.' + target
            for answer in self.recv(subdomain):
                self.result.add((subdomain,answer.address))

    def scan(self):
        h = self.target
        h = h if 'http' in h else 'http://%s'%h
        target = getdomain(h)
        self.resolvers = Resolver()
        self.answers = []
        self.result = set()
        self.baiduce(target)
        self.brute(target)
        self.writehost([(h,80,1,'http','',d) for d,h in self.result])


class GetTitle(BaseScan):
    def scan(self):
        self.gethttptitle()

