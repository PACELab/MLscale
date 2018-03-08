import numpy as np
import time
from sklearn import neighbors

edata=np.loadtxt(open('../expDataNew/data_rt_rr_statwosysdsk.txt','rb'),delimiter=',')

train_size=6160

X = edata[:,1:]
y = edata[:,0]

trX=X[:train_size]
trY=np.array(y[:train_size])

tstX=X[train_size:]
tstY=np.array(y[train_size:])

###############################################################################
# Fit regression model
n_neighbors = 5 # knn parameter

##for i, weights in enumerate(['uniform', 'distance']): can choose weight function here
knn = neighbors.KNeighborsRegressor(n_neighbors, weights='distance')

st=time.time()
knn.fit(trX, trY)
el=time.time()-st
print "KNN regression training time for %d sec examples is %0.3f"%(train_size,el)

tstY_ = np.array(knn.predict(tstX))
err=abs(tstY-tstY_)/abs(tstY)
print sum(err)/len(err)*100

trY_ = np.array(knn.predict(trX))
err=abs(trY-trY_)/abs(trY)
print sum(err)/float(len(err))*100


