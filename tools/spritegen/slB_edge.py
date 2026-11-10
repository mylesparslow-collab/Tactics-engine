import os, sys, importlib
os.environ["OMP_NUM_THREADS"]="1"
sys.path.insert(0,'.'); sys.path.insert(0,'units')
import numpy as np
from styles import styled
name,row,i=sys.argv[1],sys.argv[2],int(sys.argv[3])
mod=importlib.import_module(name)
P,over=mod.frames()[row][i]
im=np.asarray(styled(mod,P,'cel',over))
a=im[...,3]>0
print(im.shape)
ys,xs=np.nonzero(a)
print('bbox x',xs.min(),xs.max(),'y',ys.min(),ys.max())
for x in list(range(0,3))+list(range(im.shape[1]-3,im.shape[1])):
    print(x, np.nonzero(a[:,x])[0].tolist())
