import numpy as np, wave, sys
SR=48000; DUR=23.5; N=int(SR*DUR); out=np.zeros(N); rng=np.random.default_rng(3)
def add(sig,t,g=1.0):
    i=int(t*SR); j=min(N,i+len(sig)); out[i:j]+=sig[:j-i]*g
def env(n,a=0.005,d=0.3):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/d)
def scratch(t0,t1,g=.05):
    n=int((t1-t0)*SR); x=rng.standard_normal(n)
    x=np.convolve(x,np.ones(6)/6,'same')-np.convolve(x,np.ones(60)/60,'same')   # crude band-pass
    am=0.6+0.4*np.abs(np.sin(np.arange(n)/SR*2*np.pi*7.5))                       # stroke rhythm
    fade=np.minimum(1,np.minimum(np.arange(n),n-np.arange(n))/(0.03*SR))
    add(x*am*fade,t0,g)
def plonk(t,f,g=.35,d=.6,idx=1.2):
    n=int(d*4*SR); tt=np.arange(n)/SR; m=np.sin(2*np.pi*f*2*tt)*idx*np.exp(-tt/.15)
    add(np.sin(2*np.pi*f*tt+m)*env(n,.003,d),t,g)
def click(t,g=.18):
    n=int(.03*SR); add(rng.standard_normal(n)*env(n,.0005,.004),t,g)
def thud(t,g=.7):
    n=int(1.2*SR); tt=np.arange(n)/SR; f=55+60*np.exp(-tt/.05)
    add(np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,.002,.35),t,g)
def whoosh(t,d=.5,g=.12):
    n=int(d*SR); x=rng.standard_normal(n); x=np.convolve(x,np.ones(30)/30,'same'); add(x*np.sin(np.linspace(0,np.pi,n))**2,t,g*4)
thud(0.3,.8)
for i in range(10): click(0.05+i*.15,.12)
for i in range(10): plonk(.6+i*.12,300*2**(-i/12),.1,.2,.5)
for a_,b_ in [(2.6,3.0),(3.1,4.4),(4.4,5.4),(6.1,6.6),(10.9,12.0),(13.0,15.2),(15.6,16.6),(17.0,18.0),(19.3,20.3)]: scratch(a_,b_,.045)
for i,f in enumerate([392,440,523]): plonk(3.4+i*.4,f,.18,.3)
thud(6.5,.5); plonk(6.5,110,.2,1.0,1.5)
whoosh(7.8,.6)
for i in range(40): plonk(8.6+i*.025,880+ (i%8)*40,.03,.08,.2)
for i in range(8): plonk(9.6+i*.12,1046,.05,.15,.3)
for f in (262,330,392): plonk(11.0,f,.14,1.0,.6)
whoosh(12.8,.6)
for i in range(9):
    t0=15.2+i*.42; whoosh(t0,.5,.05)
    if i%3==2: thud(t0+1.25,.25)
    else: plonk(t0+1.0,523+ (i%2)*130,.2,.25,.8)
for f in (147,185,220,294): plonk(19.3,f,.12,1.6,.6)
tt=np.arange(N)/SR; pad=sum(np.sin(2*np.pi*f*tt+np.sin(tt*.3+f)) for f in (98,98.5,147,196.3))
pad*=0.010*np.minimum(1,tt/1.5)*np.minimum(1,(DUR-tt)/1.5); out+=pad
out/=max(1e-9,np.abs(out).max())*1.15
w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
s=(np.clip(out,-1,1)*32767).astype('<i2'); w.writeframes(np.repeat(s,2).tobytes()); w.close(); print('ok')
