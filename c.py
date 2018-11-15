from core.portscan import PortScan

s=PortScan('113.109.22.5')
for h,v in s.scan().items():
    print(h,v)


