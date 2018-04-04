from tkinter import *
from tkinter import filedialog
from nidaqmx.task import Task
from nidaqmx import constants
import numpy as np
from numpy import pi
from nmr_pulses import pulse_interpreter
import matplotlib as mpl
mpl.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from time2freq import time2freq
from zero_padded_signal import zero_pad_sig

SMALL_FONT = ('Helvetica', 16)
SMALL_FONT = ('Helvetica', 12)
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
    file_name = file_name_entry.get()

    pulse_data = pulse_interpreter(pulse_file_path, samp_rate, iteration)
    samp_num = len(pulse_data)


    '''
    configure the ao/ai tasks
    '''
    for current_iter in range(iteration):
        # note: displayed iteration starts with index of 1 while the iteration used in program starts with index of 0
        '''
        run, display and stored files
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
            time_data = np.linspace(0, (samp_num/samp_rate), samp_num)
            time_data = np.reshape(time_data,(1,samp_num))
            sig_data = np.zeros((3,samp_num))
            for current_avg in range(average):
                current_avg_label.config(text = f'Current Iteration: {current_avg+1}')

                sig_task.start()
                pulse_task.start()
                sig_task.wait_until_done()
                pulse_task.wait_until_done()
                sig_data =(current_avg*sig_data + np.array(sig_task.read(number_of_samples_per_channel  = samp_num)))/(current_avg+1)
                sig_task.stop()
                pulse_task.stop()

                np.save(file_path+'\\'+file_name+str(current_iter), np.concatenate((time_data, sig_data)))
                '''
                plot the data
                '''
                tcl_v = float(tcl_entry.get())
                tcl_i = np.argmin(np.abs(time_data-tcl_v))
                tch_v = float(tch_entry.get())
                tch_i = np.argmin(np.abs(time_data-tch_v))

                nmr_freq_sig = zero_pad_sig(sig_data[0,tcl_i:tch_i], 1)
                nsor_freq_sig = zero_pad_sig(sig_data[1,tcl_i:tch_i], 1)
                freq_axis = time2freq(time_data[0,tcl_i:tch_i],1)

                nmr_time_ax.clear()
                nmr_time_ax.plot(time_data[0,:],sig_data[0,:])
                nmr_freq_ax.clear()
                nmr_freq_ax.plot(freq_axis,nmr_freq_sig)
                nsor_time_ax.clear()
                nsor_time_ax.plot(time_data[0,:],sig_data[1,:])
                nsor_freq_ax.clear()
                nsor_freq_ax.plot(freq_axis,nsor_freq_sig)

                '''
                set axis limit
                '''
                txlim = (float(txliml_entry.get()),float(txlimh_entry.get()))
                tylim = (float(tyliml_entry.get()),float(tylimh_entry.get()))
                fxlim = (float(fxliml_entry.get()),float(fxlimh_entry.get()))
                fylim = (float(fyliml_entry.get()),float(fylimh_entry.get()))
                nmr_time_ax.set_xlim(txlim)
                nmr_time_ax.set_ylim(tylim)
                nmr_freq_ax.set_xlim(fxlim)
                nmr_freq_ax.set_ylim(fylim)
                if var_tx.get():
                    nmr_time_ax.autoscale(axis = 'x')
                if var_ty.get():
                    nmr_time_ax.autoscale(axis = 'y')
                if var_fx.get():
                    nmr_freq_ax.autoscale(axis = 'x')
                if var_fy.get():
                    nmr_freq_ax.autoscale(axis = 'y')

                nmr_time_ax.axvline(float(tcl_entry.get()), c = 'red')
                nmr_time_ax.axvline(float(tch_entry.get()), c = 'red')
                nmr_freq_ax.axvline(float(fcl_entry.get()), c = 'red')
                nmr_freq_ax.axvline(float(fch_entry.get()), c = 'red')

                figs_canvas.draw()
                avg_intensity_label.configure(text = f'Laser Intensity: {np.average(sig_data[2,:])}')





window = Tk()  #create a window
window.geometry('1600x1024') #specify the size of the window


'''
create menus
'''
menu_bar = Menu(window) #create a menu
file_menu = Menu(menu_bar) # create a sub-menu
file_menu.add_command(label = 'Choose File Path', command = open_path) # add items to the sub menu
file_menu.add_command(label = 'Choose Pulse Path', command = open_pulse_sequence)
menu_bar.add_cascade(label = 'File', menu = file_menu) #add submenu to the menu
window.config(menu = menu_bar) # display the menu

'''
create frames to  group things
'''
file_frame = Frame(window)
parameter_frame  = Frame(window)
status_frame = Frame(window)
figure_frame = Frame(window)
'''
file path and file name
'''
file_path_entry = Entry(file_frame, font = SMALL_FONT)
file_path_entry.insert(0,r'C:\Users\Hilty\Desktop\python\nsor_measurement\test_data')
file_name_entry = Entry(file_frame, font = SMALL_FONT)
file_path_label = Label(file_frame,text = 'File Path:', font = SMALL_FONT)
file_name_label = Label(file_frame,text = 'File Name:', font = SMALL_FONT)
file_name_entry.insert(0,'test')
'''
pulse file selection
'''
pulse_label = Label(file_frame,text = 'Pulse:', font = SMALL_FONT)
pulse_entry = Entry(file_frame, font = SMALL_FONT)
pulse_entry.insert(0,r'C:\Users\Hilty\Desktop\python\nsor_measurement\pulse_sequences\sin_wave.txt')

'''
parameter set up for ao and ai
'''
samp_rate_label = Label(parameter_frame,text = 'Sampling rate (MS/s):', font = SMALL_FONT)
samp_rate_entry = Entry(parameter_frame, font = SMALL_FONT, width = 5)
samp_rate_entry.insert(0,'0.33')

iteration_label = Label(parameter_frame,text = 'Iteration:', font = SMALL_FONT)
iteration_entry = Entry(parameter_frame, font = SMALL_FONT, width = 3)
iteration_entry.insert(0,'1')

avg_label = Label(parameter_frame,text = 'Average:', font = SMALL_FONT)
avg_entry = Entry(parameter_frame, font = SMALL_FONT, width = 3)
avg_entry.insert(0,'1')

pulse_channel_label = Label(parameter_frame,text = 'Pulse Channel:', font = SMALL_FONT)
pulse_channel_entry = Entry(parameter_frame, font = SMALL_FONT, width = 8)
pulse_channel_entry.insert(0,'Dev1/ao1')

nmr_channel_label = Label(parameter_frame,text = 'NMR Channel:', font = SMALL_FONT)
nmr_channel_entry = Entry(parameter_frame, font = SMALL_FONT, width = 8)
nmr_channel_entry.insert(0,'Dev1/ai1')

nsor_channel_label = Label(parameter_frame,text = 'NSOR Channel:', font = SMALL_FONT)
nsor_channel_entry = Entry(parameter_frame, font = SMALL_FONT, width = 8)
nsor_channel_entry.insert(0,'Dev1/ai4')

laser_intensity_channel_label = Label(parameter_frame,text = 'Laser Intensity Channel:', font = SMALL_FONT)
laser_intensity_channel_entry = Entry(parameter_frame, font = SMALL_FONT, width = 8)
laser_intensity_channel_entry.insert(0,'Dev1/ai7')

'''
current_status
'''
current_iter_label = Label(status_frame, text = 'Current Iteration: 1', font = SMALL_FONT)

current_avg_label = Label(status_frame, text = 'Current Average: 1', font = SMALL_FONT)


'''
run the program
'''
run_button = Button(window, text = 'Start',font = SMALL_FONT, command = start_acquistion,width = 10, height = 2)


'''
matplotlib figure configration
'''
signal_figures = Figure(figsize = (14,6), dpi = 100, tight_layout=True)
nmr_time_ax  = signal_figures.add_subplot(221)
nmr_freq_ax = signal_figures.add_subplot(222)



nsor_time_ax = signal_figures.add_subplot(223, sharex = nmr_time_ax)
nsor_freq_ax = signal_figures.add_subplot(224, sharex = nmr_freq_ax)

figs_canvas = FigureCanvasTkAgg(signal_figures,master = figure_frame)
figs_canvas.show()
tool_frame = Frame(window)
toolbar = NavigationToolbar2TkAgg(figs_canvas, tool_frame)
toolbar.update()
avg_intensity_label =  Label(figure_frame, text = 'Laser Intensity: 0', font = SMALL_FONT)
'''
axis limit setup
'''
var_tx = IntVar()
var_ty = IntVar(value = 1)
var_fx = IntVar()
var_fy = IntVar(value = 1)
auto_scale_check_tx = Checkbutton(figure_frame, text = 'Time auto scale x', variable = var_tx, font = SMALL_FONT)
auto_scale_check_ty = Checkbutton(figure_frame, text = 'Time auto scale y', variable = var_ty, font = SMALL_FONT)
auto_scale_check_fx = Checkbutton(figure_frame, text = 'Freq auto scale x', variable = var_fx, font = SMALL_FONT)
auto_scale_check_fy = Checkbutton(figure_frame, text = 'Freq auto scale y', variable = var_fy, font = SMALL_FONT)
txlim_label = Label(figure_frame, text = 'Time x limit:', font = SMALL_FONT)
tylim_label = Label(figure_frame, text = 'Time y limit:', font = SMALL_FONT)
fxlim_label = Label(figure_frame, text = 'Freq x limit:', font = SMALL_FONT)
fylim_label = Label(figure_frame, text = 'Freq y limit:', font = SMALL_FONT)
txliml_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
txliml_entry.insert(0,'0')
txlimh_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
txlimh_entry.insert(0,'0.6')
tyliml_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
tyliml_entry.insert(0,'-1')
tylimh_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
tylimh_entry.insert(0,'1')
fxliml_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
fxliml_entry.insert(0,'31100')
fxlimh_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
fxlimh_entry.insert(0,'31300')
fyliml_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
fyliml_entry.insert(0,'0')
fylimh_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
fylimh_entry.insert(0,'1')

'''
cursor used for calculation
'''
time_cursor_label = Label(figure_frame, text = 'Time cursor:', font = SMALL_FONT)
freq_cursor_label = Label(figure_frame, text = 'Freq cursor:', font = SMALL_FONT)
tcl_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
tcl_entry.insert(0,'0')
tch_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
tch_entry.insert(0,'1')
fcl_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
fcl_entry.insert(0,'31150')
fch_entry = Entry(figure_frame, font = SMALL_FONT, width = 5)
fch_entry.insert(0,'31250')


'''
arrangement of the widgets
'''
file_frame.grid(row = 0,column = 0)
file_path_entry.grid(row = 0, column = 1, ipadx = 160, sticky = W)
file_path_label.grid(row = 0, column = 0, sticky = W)
file_name_entry.grid(row = 1, column = 1, sticky = W)
file_name_label.grid(row = 1, column = 0, sticky = W)
pulse_label.grid(row = 2, column = 0, sticky = W)
pulse_entry.grid(row = 2, column = 1, ipadx = 200, sticky = W)

parameter_frame.grid(row = 0,column = 1)
samp_rate_label.grid(row = 0, column = 0, sticky = W)
samp_rate_entry.grid(row = 0, column = 1, sticky = W)
iteration_label.grid(row = 0, column = 2, sticky = W)
iteration_entry.grid(row = 0, column = 3, sticky = W)
avg_label.grid(row = 0, column = 4, sticky = W)
avg_entry.grid(row = 0, column = 5, sticky = W)
pulse_channel_label.grid(row = 1, column = 0, sticky = W)
pulse_channel_entry.grid(row = 1, column = 1, sticky = W)
nmr_channel_label.grid(row = 1, column = 2, sticky = W)
nmr_channel_entry.grid(row = 1, column = 3, sticky = W)
nsor_channel_label.grid(row = 2, column = 0, sticky = W)
nsor_channel_entry.grid(row = 2, column = 1, sticky = W)
laser_intensity_channel_label.grid(row = 2, column = 2, sticky = W)
laser_intensity_channel_entry.grid(row = 2, column = 3, sticky = W)

figure_frame.grid(row = 2, column = 0, columnspan = 2)
figs_canvas.get_tk_widget().grid(row = 0,column = 0, columnspan = 12, sticky = 'NEWS')
figs_canvas._tkcanvas.grid(row=0, column=0, columnspan = 12, sticky = 'NEWS')
auto_scale_check_tx.grid(row = 1, column = 0, columnspan = 3, sticky = W)
auto_scale_check_ty.grid(row = 1, column = 3, columnspan = 3, sticky = W)
auto_scale_check_fx.grid(row = 1, column = 6, columnspan = 3, sticky = W)
auto_scale_check_fy.grid(row = 1, column = 9, columnspan = 3, sticky = W)
txlim_label.grid(row = 2, column = 0, sticky = W)
txliml_entry.grid(row = 2, column = 1, sticky = W)
txlimh_entry.grid(row = 2, column = 2, sticky = W)
tylim_label.grid(row = 2, column = 3, sticky = W)
tyliml_entry.grid(row = 2, column = 4, sticky = W)
tylimh_entry.grid(row = 2, column = 5, sticky = W)
fxlim_label.grid(row = 2, column = 6, sticky = W)
fxliml_entry.grid(row = 2, column = 7, sticky = W)
fxlimh_entry.grid(row = 2, column = 8, sticky = W)
fylim_label.grid(row = 2, column = 9, sticky = W)
fyliml_entry.grid(row = 2, column = 10, sticky = W)
fylimh_entry.grid(row = 2, column = 11, sticky = W)
time_cursor_label.grid(row = 3, column = 0, sticky = W)
tcl_entry.grid(row = 3, column = 1, sticky = W)
tch_entry.grid(row = 3, column = 2, sticky = W)
freq_cursor_label.grid(row = 3, column = 6, sticky = W)
fcl_entry.grid(row = 3, column = 7, sticky = W)
fch_entry.grid(row = 3, column = 8, sticky = W)
avg_intensity_label.grid(row = 4, column = 0, columnspan = 2, sticky = W)

status_frame.grid(row = 3,column = 0, sticky = W)
current_iter_label.grid(row = 0, column = 0, sticky = W)
current_avg_label.grid(row = 0, column = 1, sticky = W)

tool_frame.grid(row = 3, column =1)

run_button.grid(row = 4,column = 0, sticky = W)


'''
mainloop
'''
window.mainloop()
