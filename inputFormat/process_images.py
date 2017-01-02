#!/usr/bin/env python

# this script processes the images, and saves hdf5 versions of them
# the basic format contains two parts:
#   1) an image saved at some resolution, like 0-255 value per pixel
#          the default is a uint16 integer (0-65535) 
#   2) a variable called im_scale_shift which contains two floats
#
# the float-value of the image would be:
#   im_float=im_int*im_scale_shift[0] + im_scale_shift[1]
#
# the bbsk images are angular size 60 degrees x 40 degrees
# the raw images are resized so that 
#   each pixel ~ 0.5 degrees (cat retina)  - default
# 
#            ...or...
#
# the raw images are resized so that each pixel ~ 13 degrees (mouse retina)
#


import sys
import copy
import glob
import numpy
import Image
import os
from Waitbar import *
import h5py
import array
import pylab
from filters import *

# for difference of gaussians (dog)
import scipy.signal as sig

# for the olshausen images
from scipy.io import loadmat

# for whitening
from scipy.fftpack import fft2, fftshift, ifft2, ifftshift
from scipy import real,absolute


def read_raw_vanhateren100(show=True):
    fnames=glob.glob('original/vanhateren_iml/*.iml')
    im_list=[]
    w = Waitbar(True)
    
    for i,filename in enumerate(fnames):
        fin = open( filename, 'rb' )
        s = fin.read()
        fin.close()
        arr = array.array('H', s)
        arr.byteswap()
        img = numpy.array(arr, dtype='uint16').reshape(1024,1536)
        
        im_list.append(img)
        if show:
            imm=Image.fromarray(img)
            imm.show(command='display')
        
        w.update((i+1)/100.0)
        print w,
        sys.stdout.flush()
    
    var={'im':im_list,'im_scale_shift':[1.0,0.0]}
    return var


def read_raw_olshausen10(show=True):

    data=loadmat('original/olshausen/IMAGES_RAW.mat')
    IMAGES=data['IMAGESr']
    
    im_list=[]
    for i in range(10):
        im=IMAGES[:,:,i].copy()
        if show:
            imm=Image.fromarray(im)
            imm.show(command='display')
        im_list.append(im)
    
    var={'im':im_list,'im_scale_shift':[1.0,0.0]}
    
    return var

def read_raw_olshausen10_white(show=True):

    data=loadmat('original/olshausen/IMAGES.mat')
    IMAGES=data['IMAGES']
    
    im_list=[]
    for i in range(10):
        im=IMAGES[:,:,i].copy()
        if show:
            imm=Image.fromarray(im)
            imm.show(command='display')
            
        im_list.append(im)
    
    var={'im':im_list,'im_scale_shift':[1.0,0.0]}
    
    return var


def read_raw_new_images12(show=True):
    
    files=glob.glob('original/new_images12/new_images12*.png')
    files.sort()
    
    im_list=[]
    
    print "Image files: ",len(files)
    
    
    for fname in files:
    
        im=Image.open(fname)
        if show:
            im.show(command='display')
        
        a=numpy.asarray(im.getdata(),dtype='B')
        a.shape=im.size[::-1]
    
        im_list.append(a)
        
        
    var={'im':im_list,'im_scale_shift':[1.0,0.0]}
    
    return var
 
 
def read_raw_bbsk(animal='cat',subset=True,show=True):
    
    if subset:
        files=glob.glob('original/subset_bbsk081604/*.jpg')
    else:
        files=glob.glob('original/all_bbsk081604/*.jpg')
    
    files.sort()
    
    im_list=[]
    
    print "Image files: %d" % len(files)
    print "Animal:", animal
    w = Waitbar(True)
    
    file_count=len(files)
    for count,fname in enumerate(files):

        im=Image.open(fname)
        orig_size=im.size
        
        # the bbsk images are angular size 60 degrees x 40 degrees
        # the raw images are resized so that 
        #   5.5 pixels ~ 0.5 degrees (cat retina)  - default
        # 
        #            ...or...
        #
        #   13 pixels ~ 7 degrees (mouse retina)
        #
        # see the contained iccns.pdf
        #
        
        if animal=='cat':
            new_size=[int(o*60./0.5*5.5/orig_size[0]) for o in orig_size]
        elif animal=='mouse':
            new_size=[int(o*60./7.*13/orig_size[0]) for o in orig_size]
        else:
            raise ValueError
        
        im=im.convert("L")
        
        if fname==files[0]:
            print "Resize: %dx%d --> %dx%d" % (orig_size[0],orig_size[1],
                                                new_size[0],new_size[1])
        im=im.resize(new_size)
        
        if show:
            im.show()
        
        # I know these have a max value of 255, so 'B' will work
        a=numpy.asarray(im.getdata(),dtype='B')
        a.shape=im.size[::-1]
    
        im_list.append(a)
        
        w.update((count+1)/float(file_count))
        print w,
        sys.stdout.flush()
        
    var={'im':im_list,'im_scale_shift':[1.0,0.0]}
    print
    
    return var



def overtitle(s):
    from matplotlib.font_manager import FontProperties
    import pylab

    t = pylab.gcf().text(0.5,
        0.92, s,
        horizontalalignment='center',
        fontproperties=FontProperties(size=16))
        
def view(fname,which_pics=None,figure=None):
    import pylab
    import math
    try:
        var=hdf5_load_images(fname)
    except AttributeError,TypeError:
        var=fname
        
    var=dict(var)

    if figure is None:    
        pylab.figure()
    else:
        pylab.figure(figure)
    
    pylab.show()
    gray=pylab.cm.gray

    total_num_pics=len(var['im'])
    
    if which_pics:
        var['im']=[var['im'][i] for i in which_pics if i<len(var['im'])]
    else:
        which_pics=range(len(var['im']))
    
    num_pics=len(var['im'])
    c=math.ceil(math.sqrt(num_pics))
    r=math.ceil(num_pics/c)
    
    for i in range(num_pics):
        pylab.subplot(r,c,i+1)
        pylab.imshow(var['im'][i],cmap=pylab.cm.gray)
        #pylab.pcolor(var['im'][i],cmap=pylab.cm.gray)
        pylab.hold(False)
        pylab.axis('equal')
    #        pylab.imshow(var['im'][i],cmap=gray,aspect='preserve')
        pylab.axis('off')
        pylab.title('%d' % which_pics[i])
        pylab.draw()

    overtitle('%dx%dx%d' % 
            (var['im'][0].shape[0],var['im'][0].shape[1],total_num_pics))
    pylab.draw()
    pylab.show()


def hdf5_save_images(var,fname):
    f=h5py.File(fname,'w')

    f.attrs['im_scale_shift']=var['im_scale_shift']
    for i,im in enumerate(var['im']):
        f.create_dataset('image%d' % i,data=im)

    f.close()

def hdf5_load_images(fname):
    f=h5py.File(fname,'r')
    var={}
    var['im_scale_shift']=list(f.attrs['im_scale_shift'])
    N=len(f.keys())
    var['im']=[]
    for i in range(N):
        var['im'].append(numpy.array(f['image%d' % i]))

    f.close()

    return var

def hdf5_fname(fname):
    base,ext=os.path.splitext(fname)
    return base+".hdf5"


def save(var,fname,overwrite=True):
    if not overwrite and os.path.exists(fname):
        print "%s already exists...skipping." % fname
        return
        
    print "Writing ",fname
    hdf5_save_images(var,fname)

if __name__=="__main__":
    if False:
        base='bbsk081604'
        imfname='hdf5/'+base+".hdf5"
        var_raw=hdf5_load_images(imfname)
    
    
        imfname='hdf5/'+base+"_shift5_pos.hdf5"
        var=make_dog(var_raw)
        var=scale_shift(var,1.0,5.0,truncate=True)
        save(var,imfname,overwrite=False)
        
        imfname='hdf5/'+base+"_neg_shift5_pos.hdf5"
        var=make_dog(var_raw)
        var=scale_shift(var,-1.0,5.0,truncate=True)
        save(var,imfname,overwrite=False)


    base='new_images12'
    imfname='hdf5/'+base+".hdf5"
    var_raw=hdf5_load_images(imfname)
    
    
    imfname='hdf5/'+base+"_shift5_pos.hdf5"
    var=make_dog(var_raw)
    var=scale_shift(var,1.0,5.0,truncate=True)
    var=make_norm(var,subtract_mean=False)
    save(var,imfname,overwrite=True)
        
    imfname='hdf5/'+base+"_neg_shift5_pos.hdf5"
    var=make_dog(var_raw)
    var=scale_shift(var,-1.0,5.0,truncate=True)
    var=make_norm(var,subtract_mean=False)
    save(var,imfname,overwrite=True)


if False:

    datasets=['bbsk','bbsk_all','new_images12','olshausen','vanhateren']
    #datasets=['bbsk_all_mouse']
    processing=['norm','posneg_dog','dog','white']
    
    for i,dataset in enumerate(datasets):
    
        if dataset=='bbsk':
            base='bbsk081604'
            imfname='hdf5/'+base+".hdf5"
            
            try:
                var_raw=hdf5_load_images(imfname)
            except IOError:
                var_raw=read_raw_bbsk(show=False)
                save(var_raw,imfname,overwrite=False)
        elif dataset=='bbsk_all_mouse':
            base='bbsk081604_mouse'
            imfname='hdf5/'+base+".hdf5"
            
            try:
                var_raw=hdf5_load_images(imfname)
            except IOError:
                var_raw=read_raw_bbsk(show=False,subset=False,animal='mouse')
                save(var_raw,imfname,overwrite=False)
        elif dataset=='bbsk_all':
            base='bbsk081604_all'
            imfname='hdf5/'+base+".hdf5"
            
            try:
                var_raw=hdf5_load_images(imfname)
            except IOError:
                var_raw=read_raw_bbsk(show=False,subset=False)
                save(var_raw,imfname,overwrite=False)
                
        elif dataset=='new_images12':
            base='new_images12'
            imfname='hdf5/'+base+".hdf5"

            try:
                var_raw=hdf5_load_images(imfname)
            except IOError:
                var_raw=read_raw_new_images12(show=False)
                save(var_raw,imfname,overwrite=False)

        elif dataset=='olshausen':
            base='olshausen10'
            imfname='hdf5/'+base+".hdf5"
        
            fname='original/olshausen/IMAGES.mat'
            if not os.path.exists(fname):
                print "Could not find %s. Need to download the database.  Skipping %s" % (fname,dataset)
                continue

            try:
                var_raw=hdf5_load_images(imfname)
            except IOError:
                var_raw=read_raw_olshausen10(show=False)
                save(var_raw,imfname,overwrite=False)
                
        elif dataset=='vanhateren':
            base='vanhateren100'
            imfname='hdf5/'+base+".hdf5"

            fnames=glob.glob('original/vanhateren_iml/*.iml')
            if not fnames:
                print "Could not find any vanhateren_iml files. Need to download the database.  Skipping %s" % (dataset)
                continue
            try:
                var_raw=hdf5_load_images(imfname)
            except IOError:
                var_raw=read_raw_vanhateren100(show=False)
                save(var_raw,imfname,overwrite=False)
                
        else:
            raise ValueError,"Unknown dataset %s" % dataset
        
        if False:
            view(var_raw,[1,2,3,4,5,6,7,8,9,10,11,12],figure=imfname)
    
        
        for proc in processing:
            imfname='hdf5/'+base+"_"+proc+".hdf5"
            if os.path.exists(imfname):
                print "%s exists...skipping" % imfname
                # comment this line if you only want to view new files
                if False:
                    var=hdf5_load_images(imfname)
                    view(var,[1,2,3,4,5,6,7,8,9,10,11,12],figure=imfname)
            else:                
                if proc=='norm':
                    var=make_norm(var_raw)
                elif proc=='dog':
                    if 'mouse' in dataset: # use 3:9 for mouse
                        var=make_dog(var_raw,3,9)                    
                    else:  # use 1:3, default
                        var=make_dog(var_raw)
                elif proc=='posneg_dog':
                    if 'mouse' in dataset: # use 3:9 for mouse
                        var=make_dog(var_raw,3,9)                    
                    else:  # use 1:3, default
                        var=make_dog(var_raw)
                        
                    N=len(var['im'])
                    for i in range(N):    
                        var['im'].append(-var['im'][i])
                        
                elif proc=='white':
                    var=make_white(var_raw)
                    
                set_resolution(var,'uint16')
                save(var,imfname)
                
                
                view(var,[1,2,3,4,5,6,7,8,9,10,11,12],figure=imfname)
            
    datasets=['new_images12','olshausen']
    processing=['dog_rot13','white_rot13']
    
    for i,dataset in enumerate(datasets):
    
        if dataset=='bbsk':
            base='bbsk081604'
            imfname='hdf5/'+base+".hdf5"
            
            try:
                var_raw=hdf5_load_images(imfname)
            except IOError:
                var_raw=read_raw_bbsk(show=False)
                save(var_raw,imfname,overwrite=False)
        elif dataset=='bbsk_all':
            base='bbsk081604_all'
            imfname='hdf5/'+base+".hdf5"
            
            try:
                var_raw=hdf5_load_images(imfname)
            except IOError:
                var_raw=read_raw_bbsk(show=False,subset=False)
                save(var_raw,imfname,overwrite=False)
                
        elif dataset=='new_images12':
            base='new_images12'
            imfname='hdf5/'+base+".hdf5"

            try:
                var_raw=hdf5_load_images(imfname)
            except IOError:
                var_raw=read_raw_new_images12(show=False)
                save(var_raw,imfname,overwrite=False)

        elif dataset=='olshausen':
            base='olshausen10'
            imfname='hdf5/'+base+".hdf5"
        
            fname='original/olshausen/IMAGES.mat'
            if not os.path.exists(fname):
                print "Could not find %s. Need to download the database.  Skipping %s" % (fname,dataset)
                continue

            try:
                var_raw=hdf5_load_images(imfname)
            except IOError:
                var_raw=read_raw_olshausen10(show=False)
                save(var_raw,imfname,overwrite=False)
                
        elif dataset=='vanhateren':
            base='vanhateren100'
            imfname='hdf5/'+base+".hdf5"

            fnames=glob.glob('original/vanhateren_iml/*.iml')
            if not fnames:
                print "Could not find any vanhateren_iml files. Need to download the database.  Skipping %s" % (dataset)
                continue
            try:
                var_raw=hdf5_load_images(imfname)
            except IOError:
                var_raw=read_raw_vanhateren100(show=False)
                save(var_raw,imfname,overwrite=False)
                
        else:
            raise ValueError,"Unknown dataset %s" % dataset
        
        if False:
            view(var_raw,[1,2,3,4,5,6,7,8,9,10,11,12],figure=imfname)
    
        
        for proc in processing:
            imfname='hdf5/'+base+"_"+proc+".hdf5"
            if os.path.exists(imfname):
                print "%s exists...skipping" % imfname
                # comment this line if you only want to view new files
                if False:
                    var=hdf5_load_images(imfname)
                    view(var,[1,2,3,4,5,6,7,8,9,10,11,12],figure=imfname)
            else:                
                if proc=='norm':
                    var=make_norm(var_raw)
                elif proc=='dog_rot13':
                    var_rot=make_rot(var_raw,range(0,180,14))
                    var=make_dog(var_rot)
                elif proc=='white':
                    var_rot=make_rot(var_raw,range(0,180,14))
                    var=make_white(var_rot)
                    
                set_resolution(var,'uint16')
                save(var,imfname)
                
                
                view(var,[1,2,3,4,5,6,7,8,9,10,11,12],figure=imfname)
