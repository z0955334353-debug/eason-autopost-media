import json, time, subprocess, datetime as dt, os
F='fii_2026.json'
out={k:v for k,v in json.load(open(F)).items() if v} if os.path.exists(F) else {}
d=dt.date(2026,1,2)
while d<=dt.date(2026,11,26):
    k=d.strftime('%Y%m%d')
    if d.weekday()<5 and k not in out:
        u=f"https://www.twse.com.tw/rwd/zh/fund/BFI82U?type=day&dayDate={k}&response=json"
        for _ in range(3):
            r=subprocess.run(['curl','-s','-m','20',u],capture_output=True,text=True)
            try: j=json.loads(r.stdout); break
            except Exception: j=None; time.sleep(2)
        if j is not None:
            if j.get('stat')=='OK': out[k]={x[0].strip():int(x[3].replace(',','')) for x in j['data']}
            else: out[k]=False
            json.dump(out,open(F,'w'),ensure_ascii=False)
        time.sleep(0.4)
    d+=dt.timedelta(days=1)
print('days',len(out),'trading',sum(1 for v in out.values() if v))
