from pylab import *
import plasticity

def make_square(N=4,sz=100,rates=[10,40],display=False):
    
    idx=r_[0:sz]
    
    sq_sz=sz/N
    l=[]
    for i in range(N):
        
    
        r=ones(idx.shape)*rates[0]
        r[((sq_sz*i)<=idx) & (idx<(sq_sz*(i+1)))]=rates[1]
        
        l.append(r)
        
    a=array(l,numpy.float)
        
    if display:
        
        for r in a:
            plot(r)
    
    
    return a

if True:  # make square patterns
    num_patterns=10
    N=100
    rates=make_square(num_patterns,N,[1,50])
    data={'im':[rates],'im_scale_shift':[1.0,0.0]}        
    plasticity.utils.zpickle.save(data,'square10.dat')
