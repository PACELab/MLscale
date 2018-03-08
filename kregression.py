# Authors: Jan Hendrik Metzen <jhm@informatik.uni-bremen.de>
# License: BSD 3 clause
from __future__ import division
import time

import numpy as np

from sklearn.svm import SVR
from sklearn.grid_search import GridSearchCV
from sklearn.learning_curve import learning_curve
from sklearn.kernel_ridge import KernelRidge

rng = np.random.RandomState(0)

edata=np.loadtxt(open('../expDataNew/data_rt_rr_statwosysdsk.txt','rb'),delimiter=',')

#############################################################################
# Generate sample data
X=edata[:,1:]
y=edata[:,0]

#############################################################################
# Fit regression model
train_size = 6160 # 70% training, 30% test
svr = GridSearchCV(SVR(kernel='rbf', gamma=0.1), cv=5, param_grid={"C": [1e0, 1e1, 1e2, 1e3], "gamma": np.logspace(-2, 2, 5)})

kr = GridSearchCV(KernelRidge(kernel='rbf', gamma=0.1), cv=5, param_grid={"alpha": [1e0, 0.1, 1e-2, 1e-3], "gamma": np.logspace(-2, 2, 5)})

t0 = time.time()
svr.fit(X[:train_size], y[:train_size])
svr_fit = time.time() - t0
print("SVR complexity and bandwidth selected and model fitted in %.3f s" % svr_fit)

t0 = time.time()
kr.fit(X[:train_size], y[:train_size])
kr_fit = time.time() - t0
print("KRR complexity and bandwidth selected and model fitted in %.3f s" % kr_fit)

sv_ratio = svr.best_estimator_.support_.shape[0] / train_size
print("Support vector ratio: %.3f" % sv_ratio)

X_plot=X[train_size:]

t0 = time.time()
y_svr = np.array(svr.predict(X_plot))
svr_predict = time.time() - t0
print("SVR prediction for %d inputs in %.3f s" % (X_plot.shape[0], svr_predict))

y_act=np.array(y[train_size:])
err=abs(y_act-y_svr)/abs(y_act)
print "Test error:",sum(err)/len(err)*100

trY_ = np.array(svr.predict(X[:train_size]))
y_act=np.array(y[:train_size])
err=abs(y_act-trY_)/abs(trY_)
print "Train error:",sum(err)/len(err)*100

print "Best parameters for SVR:%s with score:%0.2f"%(svr.best_params_,svr.best_score_)

t0 = time.time()
y_kr = np.array(kr.predict(X_plot))
kr_predict = time.time() - t0
print("KRR prediction for %d inputs in %.3f s" % (X_plot.shape[0], kr_predict))

y_act=np.array(y[train_size:])
err=abs(y_act-y_kr)/abs(y_act)
print "Test error:",sum(err)/len(err)*100

trY_ = np.array(kr.predict(X[:train_size]))
y_act=np.array(y[:train_size])
err=abs(y_act-trY_)/abs(trY_)
print "Train error:",sum(err)/len(err)*100

print "Best parameters for KR:%s with score:%0.2f"%(kr.best_params_,kr.best_score_)

