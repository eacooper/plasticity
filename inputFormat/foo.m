input = repmat([zeros(1,100) ones(1,100)],1,10);

h5create('test_input.hdf5','/image0',size(input))
%h5create('test.hdf5','/image1',[1 100])
h5write('test_input.hdf5', '/image0', input)
%h5write('test.hdf5', '/image1', ones(1,100))

h5writeatt('test_input.hdf5','/','im_scale_shift',[1 0])

figure; 
plot(input);
saveas(gcf,'test_input.png')