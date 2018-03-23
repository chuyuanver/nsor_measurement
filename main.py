from tkinter import *
from tkinter import filedialog
from nidaqmx.task import Task
from nidaqmx import constants
import numpy as np
from numpy import pi
from nmr_pulses import pulse_interpreter
import matplotlib.pyplot as plt

'''
A gui for NSOR measurement and data processing
'''

def open_path():
    file_path = filedialog.askdirectory(parent = window,
        initialdir = r'C:\Users\Hilty\Desktop\python\nsor_measurement',
        title = 'Choose file path to save the file')
    l = len(file_path_entry.get())
    file_path_entry.delete(0,l)
    file_path_entry.insert(0,file_path)

def open_pulse_sequence():
    pulse_name = filedialog.askopenfilename(parent = window,
        initialdir = r'C:\Users\Hilty\Desktop\python\nsor_measurement\pulse_sequences',
        filetypes =(("Text File", "*.txt"),("All Files","*.*")),
        title = "Choose a file.")
    l = len(pulse_entry.get())
    pulse_entry.delete(0,l)
    pulse_entry.insert(0,pulse_name)

def start_acquistion():
    '''
    set necessary constants
    '''
    samp_rate = int(float(samp_rate_entry.get())*1000000)
    iteration = int(iteration_entry.get())
    average = int(avg_entry.get())
    pulse_chan = pulse_channel_entry.get()
    nmr_chan = nmr_channel_entry.get()
    nsor_chan = nsor_channel_entry.get()
    laser_intensity_chan = laser_intensity_channel_entry.get()
    pulse_file_path = pulse_entry.get()
    file_path = file_path_entry.get()

    pulse_data = pulse_interpreter(pulse_file_path, samp_rate, iteration)
    samp_num = len(pulse_data)
    '''
    configure the ao/ai tasks
    '''
    for current_iter in range(iteration):
        # note: displayed iteration starts with index of 1 while the iteration used in program starts with index of 0
        '''
        need to think of a way of arrange stored files
        '''
        current_iter_label.config(text = f'Current Iteration: {current_iter+1}')
        with Task('signal_task') as sig_task, Task('pulse_task') as pulse_task:
            for sig_chan in [nmr_chan, nsor_chan, laser_intensity_chan]:
                sig_task.ai_channels.add_ai_voltage_chan(physical_channel = sig_chan,
                        terminal_config = constants.TerminalConfiguration.DIFFERENTIAL)
            pulse_task.ao_channels.add_ao_voltage_chan(pulse_chan)
            pulse_task.timing.cfg_samp_clk_timing(rate =samp_rate,
                            samps_per_chan = samp_num,
                            sample_mode=constants.AcquisitionType.FINITE)
            sig_task.timing.cfg_samp_clk_timing(rate = samp_rate,
                         source = '/Dev1/ao/SampleClock',
                         samps_per_chan = samp_num,
                         sample_mode=constants.AcquisitionType.FINITE)
            pulse_task.write(pulse_data)
            for current_avg in range(average):
                sig_task.start()
                pulse_task.start()
                sig_task.wait_until_done()
                pulse_task.wait_until_done()
                sig_data = np.array(sig_task.read(number_of_samples_per_channel  = samp_num))
                sig_task.stop()
                pulse_task.stop()
                plt.plot(sig_data[1,:])
                plt.show()


window = Tk()  #create a window
window.geometry('1440x960') #specify the size of the window


'''
create menus
'''
menu_bar = Menu(window) #create a menu
file_menu = Menu(menu_bar) # create a sub-menu
file_menu.add_command(label = 'File Path', command = open_path) # add items to the sub menu
menu_bar.add_cascade(label = 'File', menu = file_menu) #add submenu to the menu
window.config(menu = menu_bar) # display the menu

'''
create frames to  group things
'''
file_frame = Frame(window, height = 30, width = 200, bd = 1, bg ='#99ffcc')
pulse_frame = Frame(window, height = 30, width = 200, bd = 1, bg ='#ccccff')
parameter_frame  = Frame(window, height = 200, width = 200, bd = 1)
status_frame = Frame(window, height = 200, width = 200, bd = 1, bg ='red')

'''
file path and file name
'''
file_path_entry = Entry(file_frame, font = ('Helvetica', 16))
file_path_entry.insert(0,'C:\\')
file_name_entry = Entry(file_frame, font = ('Helvetica', 16))
file_path_label = Label(file_frame,text = 'File Path:', font = ('Helvetica', 16))
file_name_label = Label(file_frame,text = 'File Name:', font = ('Helvetica', 16))

'''
pulse file selection
'''
pulse_label = Label(pulse_frame,text = 'Pulse:', font = ('Helvetica', 16))
pulse_entry = Entry(pulse_frame, font = ('Helvetica', 16))
pulse_button = Button(pulse_frame, text = 'Choose Pulse', font = ('Helvetica', 16), command = open_pulse_sequence)
pulse_entry.insert(0,r'C:\Users\Hilty\Desktop\python\nsor_measurement\pulse_sequences\sin_wave.txt')

'''
parameter set up for ao and ai
'''
samp_rate_label = Label(parameter_frame,text = 'Sampling rate (MS/s):', font = ('Helvetica', 16))
samp_rate_entry = Entry(parameter_frame, font = ('Helvetica', 16), width = 3)
samp_rate_entry.insert(0,'0.33')

iteration_label = Label(parameter_frame,text = 'Iteration:', font = ('Helvetica', 16))
iteration_entry = Entry(parameter_frame, font = ('Helvetica', 16), width = 3)
iteration_entry.insert(0,'1')

avg_label = Label(parameter_frame,text = 'Average:', font = ('Helvetica', 16))
avg_entry = Entry(parameter_frame, font = ('Helvetica', 16), width = 3)
avg_entry.insert(0,'1')

pulse_channel_label = Label(parameter_frame,text = 'Pulse Channel:', font = ('Helvetica', 16))
pulse_channel_entry = Entry(parameter_frame, font = ('Helvetica', 16), width = 8)
pulse_channel_entry.insert(0,'Dev1/ao1')

nmr_channel_label = Label(parameter_frame,text = 'NMR Channel:', font = ('Helvetica', 16))
nmr_channel_entry = Entry(parameter_frame, font = ('Helvetica', 16), width = 8)
nmr_channel_entry.insert(0,'Dev1/ai1')

nsor_channel_label = Label(parameter_frame,text = 'NSOR Channel:', font = ('Helvetica', 16))
nsor_channel_entry = Entry(parameter_frame, font = ('Helvetica', 16), width = 8)
nsor_channel_entry.insert(0,'Dev1/ai4')

laser_intensity_channel_label = Label(parameter_frame,text = 'Laser Intensity Channel:', font = ('Helvetica', 16))
laser_intensity_channel_entry = Entry(parameter_frame, font = ('Helvetica', 16), width = 8)
laser_intensity_channel_entry.insert(0,'Dev1/ai7')

'''
current_status
'''
current_iter_label = Label(status_frame, text = 'Current Iteration: 1', font = ('Helvetica', 16))

current_avg_label = Label(status_frame, text = 'Current Average: 1', font = ('Helvetica', 16))


'''
run the program
'''
run_button = Button(window, text = 'Start',font = ('Helvetica', 16), command = start_acquistion,width = 10, height = 2)


'''
arrangement of the widgets
'''
file_frame.grid(row = 0,column = 0,columnspan = 3)
file_path_entry.grid(row = 0, column = 1, ipadx = 160, sticky = W, columnspan = 2)
file_path_label.grid(row = 0, column = 0, sticky = W)
file_name_entry.grid(row = 1, column = 1, sticky = W)
file_name_label.grid(row = 1, column = 0, sticky = W)

pulse_frame.grid(row = 0,column = 3,columnspan  = 3, sticky = W)
pulse_label.grid(row = 0, column = 0, sticky = W)
pulse_entry.grid(row = 0, column = 1, ipadx = 160, sticky = W, columnspan = 2)
pulse_button.grid(row = 1, column = 0)

parameter_frame.grid(row = 1,column = 0,rowspan  = 7, columnspan = 2, sticky = W)
samp_rate_label.grid(row = 0, column = 0, sticky = W)
samp_rate_entry.grid(row = 0, column = 1, padx = 10, sticky = W)
iteration_label.grid(row = 1, column = 0, sticky = W)
iteration_entry.grid(row = 1, column = 1, padx = 10, sticky = W)
avg_label.grid(row = 2, column = 0, sticky = W)
avg_entry.grid(row = 2, column = 1, padx = 10, sticky = W)
pulse_channel_label.grid(row = 3, column = 0, sticky = W)
pulse_channel_entry.grid(row = 3, column = 1, padx = 10, sticky = W)
nmr_channel_label.grid(row = 4, column = 0, sticky = W)
nmr_channel_entry.grid(row = 4, column = 1, padx = 10, sticky = W)
nsor_channel_label.grid(row = 5, column = 0, sticky = W)
nsor_channel_entry.grid(row = 5, column = 1, padx = 10, sticky = W)
laser_intensity_channel_label.grid(row = 6, column = 0, sticky = W)
laser_intensity_channel_entry.grid(row = 6, column = 1, padx = 10, sticky = W)

status_frame.grid(row = 1,column = 3, rowspan  = 2, columnspan = 2, sticky = W)
current_iter_label.grid(row = 0, column = 0, sticky = W)
current_avg_label.grid(row = 1, column = 0, sticky = W)


run_button.grid(row = 9,column = 0, sticky = W)

'''
mainloop
'''
window.mainloop()
