# scanver

前台Web使用tornado开出api接口  

后端需安装redis 使用celery进行任务调度  

安装：
  python3 -m pip install -r requirements.txt  
  
分布式部署时可以分别在conf.ini 里面设置nodeid值；然后在新建任务选项里面选择指定扫描节点，如果不指定默认是在当前节点。

初始化：  
  python3 models.py   
  python3 task.py init 
  
开启web服务：python3 webserver.py --port=8315 

开启扫描服务：python3 task.py worker -c 4 --loglevel=INFO --logfile=./data/logs/celery.log 
前端源码：https://github.com/ydhcui/scanui  

默认密码sc/1111  

截图：扫描任务管理  
![img](https://github.com/ydhcui/Scanver/blob/master/QQ%E6%88%AA%E5%9B%BE20181212115122.png?raw=true) 
截图：扫描任务详情  
![img](https://github.com/ydhcui/Scanver/blob/master/QQ%E6%88%AA%E5%9B%BE20181212120443.png?raw=true)  
截图：漏洞分类汇总  
![img](https://github.com/ydhcui/Scanver/blob/master/QQ%E6%88%AA%E5%9B%BE20181212114829.png?raw=true)  
截图：漏洞扫描结果  
![img](https://github.com/ydhcui/Scanver/blob/master/QQ%E6%88%AA%E5%9B%BE20181212115011.png?raw=true)  
截图：资产扫描结果
![img](https://github.com/ydhcui/Scanver/blob/master/QQ%E6%88%AA%E5%9B%BE20181114113907.png?raw=true)  
截图：后台celery日志

![service](https://github.com/ydhcui/Scanver/blob/master/QQ%E6%88%AA%E5%9B%BE20181115010210.png?raw=true)  
