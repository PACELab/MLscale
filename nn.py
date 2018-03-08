from ffnet import ffnet, mlgraph, readdata, savenet, loadnet
import time
import numpy as np


# Read data file
print "READING DATA..."
data = readdata( '../expDataNew/data_rt_rr_statwosysdsk.txt', delimiter = ',' )
input =  data[:, 1:] 
target = data[:, :1]

# Generate standard layered network architecture and create network
conec = mlgraph((input.shape[1],(input.shape[1]+1)/2,1))
net = ffnet(conec)

print "TRAINING NETWORK..."
n=6168

net.randomweights()
st=time.time()
net.train_tnc(input[:n], target[:n])
el=time.time()-st
print "Time to train NN with %d examples: %0.3f sec"%(n,el)
# Save net
#savenet(net,'rt_rr_statwosysdsk.network')

print
print "TESTING NETWORK..."
output, regression = net.test(input[n:], target[n:], iprint = 1)

y_act=np.array(target[n:])
y_prd=np.array(output)
err=abs(y_act-y_prd)/abs(y_act)
print "Test error",sum(err)/len(err)*100


output, regression = net.test(input[:n], target[:n], iprint = 0)

y_act=np.array(target[:n])
y_prd=np.array(output)
err=abs(y_act-y_prd)/abs(y_act)
print "Training error",sum(err)/len(err)*100

#pe=0
#for i in range(0,len(output)):
#	pe+=(abs(target[n+i]-output[i]))/target[n+i]
#	k=1
#	o,r= net.test([input[n+i]/k],target[n+i],iprint=0)
#	while o[0]>100:
#		o,r= net.test([input[n+i]/k],target[n+i],iprint=0)
#		print "Output is: ", o," for k: ",k
#		k+=1
#print "Manual error",(pe/len(output))*100


