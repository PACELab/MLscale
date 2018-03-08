from ffnet import ffnet, mlgraph, readdata, savenet, loadnet
import time
import numpy as np


# Read data file
print "READING DATA..."
data = readdata( './data_w_k_statwosysdsk.txt', delimiter = ' ' )
n=int(656*1)

for i in range(2,10):
	input =  data[:, [0,1,i]] 
	target = data[:, [i+8]]

# Generate standard layered network architecture and create network
	conec = mlgraph((input.shape[1],8,1))
	net = ffnet(conec)

	print "TRAINING NETWORK..."

	net.randomweights()
	st=time.time()
	net.train_tnc(input[:n], target[:n])
	el=time.time()-st
	print "Time to train NN with %d examples: %0.3f sec"%(n,el)

	output, regression = net.test(input[:n], target[:n], iprint = 0)

	y_act=np.array(target[:n])
	y_prd=np.array(output)
	err=abs(y_act-y_prd)/abs(y_act)
	print "Training error",sum(err)/len(err)*100

