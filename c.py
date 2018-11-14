from core.crawler import BaseRequest,Crawler
import queue
import threading

x=Crawler('https://ask.solidot.org/')
x.settings.update(
    timeout=10,
    threads=100,
    proxy={'http':'http://127.0.0.1:1111','https':'http://127.0.0.1:1111'},
    level=True)
threading.Thread(target=x.run).start()

while x.ISSTART or not x.ResQueue.empty():
    try:
        q,r = x.ResQueue.get(block=False)
        print(r.status_code,q.method,q.url)
    except queue.Empty:
        pass

