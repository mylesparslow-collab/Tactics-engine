import os, sys, importlib, copy
os.environ.setdefault("OMP_NUM_THREADS","1")
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'units'))
import numpy as np
from PIL import Image
from multiprocessing import Pool
SC=int(os.environ.get("SC","2"))
def job(a):
    mod,row,i=a
    m=importlib.import_module(mod)
    from styles import styled
    P,over=m.frames()[row][i]
    return styled(m,P,'cel',over)
if __name__=='__main__':
    mod=sys.argv[1]; spec=sys.argv[2:]  # row:i
    jobs=[(mod,s.split(':')[0],int(s.split(':')[1])) for s in spec]
    with Pool(2) as p: res=p.map(job,jobs)
    W=Image.new('RGBA',(96*len(res),112),(104,106,112,255))
    for k,r in enumerate(res):
        W.alpha_composite(Image.fromarray(r),(96*k,0))
    W=W.resize((W.width*SC,W.height*SC),Image.NEAREST)
    W.save('/tmp/claude-0/-home-user/e6171783-1e19-5fd1-8383-8baebc627213/scratchpad/%s_cel.png'%mod)
