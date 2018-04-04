import numpy as np

def time2freq(time_data, pad_power):
    x = np.ceil(np.log2(len(time_data)))
    n = 2**(pad_power-1)
    l = 2**x*n
    dt = time_data[1]-time_data[0]
    f_max =1/(2*dt)
    return np.linspace(0, f_max, int(l/2)+1)
