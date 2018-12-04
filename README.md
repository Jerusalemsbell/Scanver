# scanver

前台Web使用tornado开出api接口  

后端使用celery进行任务调度  
安装：
  python3 -m pip -r requirements.txt
初始化：  
  python3 models.py   
  python3 task.py init 
默认密码sc/1111
开启web服务：python3 webserver.py --port=8315 

开启扫描服务：python3 task.py worker --loglevel=INFO -c 4

截图：资产自动扫描录入
![img](https://github.com/ydhcui/Scanver/blob/master/QQ%E6%88%AA%E5%9B%BE20181114113907.png?raw=true)
截图：后台celery日志  
![service](https://github.com/ydhcui/Scanver/blob/master/QQ%E6%88%AA%E5%9B%BE20181115010210.png?raw=true)
