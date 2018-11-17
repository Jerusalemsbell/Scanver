from core.crawler1 import Crawler
import queue


x=Crawler('http://127.0.0.1/xss',level=1,proxy={'http':'http://127.0.0.1:1111','https':'http://127.0.0.1:1111'})
x.start()

while x.ISSTART or not x.ResQueue.empty():
        try:
            q,r = x.ResQueue.get(block=False)
            #print(r.status_code,q.method,q.url)
        except queue.Empty:
            pass
