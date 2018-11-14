# scanver

前台Web使用tornado开出api接口  

后端使用celery进行任务调度  

初始化：  
  python3 models.py   
  python3 task.py init 
  
开启web服务：python3 webserver.py  

开启扫描服务：python3 task.py worker

截图：资产自动扫描录入
![img](https://github.com/ydhcui/Scanver/blob/master/QQ%E6%88%AA%E5%9B%BE20181114113907.png?raw=true)
