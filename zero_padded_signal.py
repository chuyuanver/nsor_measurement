import numpy as np

def zero_pad_sig(np_array, pad_power):
    x = np.ceil(np.log2(len(np_array)))
    n = 2**(pad_power-1)
    l = int(2**x*n)
    print(l)
    time_sig = np.pad(np_array,(0,l-len(np_array)),'constant')
    return np.abs(np.fft.rfft(time_sig,norm = "ortho"))
