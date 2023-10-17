#BatteryTester202304_CLI
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.widgets import Slider
from matplotlib.widgets import Button
from matplotlib.widgets import TextBox
import numpy as np
import random
import serial
from serial.tools import list_ports
import datetime
import time
import tkinter as tk
from tkinter import simpledialog
from threading import Lock
from threading import Thread
#import PySimpleGUI as sg
import sys

argc = len(sys.argv)
name_of_script = sys.argv[0]
if argc > 1:
    testseconds = 60*(int(sys.argv[1]))
else:
    testseconds = 120
#sample = sys.argv[2]

dt_curr = datetime.datetime.now()
 
print(dt_curr.strftime("%A, %d %b %y"))
filename = dt_curr.strftime("DRAIN%Y%m%d%H%M.csv")
print(filename)

#  contructors
ser = ''
lock = Lock()
#fig = ''

def prnt(s):
    global print_on
    sys.stdout.write(s)
    sys.stdout.flush()

# Show the window
def show(awindow):
    awindow.deiconify()
 
# Hide the window
def hide(awindow):
    awindow.withdraw()

# globals set at start of main    
#disp_height = 0
#disp_width = 0

def port_setup():
    global ser
    # Set default of None for com port
    com_port = None

    # Call list_ports to get com port info 
    ports_available = list(list_ports.comports())

    # Loop on all available ports to find Arduino
    for temp in ports_available:
        print(str(temp))
        if "USB Serial" in str(temp) or "Arduino" in str(temp): 
            print('Found: ' + str(temp))
            if com_port == None: # always chooses the 1st found
                com_port=str(temp[0])

    if com_port == None:
        print("USB Serial not found")
        #port = serial.Serial("/dev/serial0", baudrate=57600, timeout=30.0)
        sys.exit(1)
    else:
        # Try to setup and open the comport, program will abort if not found
        try:
            ser = serial.Serial(port=com_port,baudrate=9600,timeout=2) # timeout float sec
        except Exception as e:
            print(type(e))
            if debug: print('Port Not Usable!')
            if debug: print('Do you have permissions set to read ' + com_port + ' ?')
            prnt('~')
            raise
        
    # Print which port we're using
    print('Using com port: ' + str(com_port))
    print('==================================================\n')

    # Open the serial port if it isn't open
    try:
        if ser.isOpen() == False:
            ser.open()
            prnt('{')
    except serial.serialutil.SerialException:
        raise
    except Exception as e:
        print(type(e))
        raise

    # This clears the receive buffer so we aren't using buffered data
    ser.flushInput() 

######### WAVEFORM DRAWING  ####################################################################
color_list = ['black','red','green','blue','indigo','orange','violet','cyan',
              'magenta','goldenrod','purple','darkblue','darkred',
              'black','black','black','black','black',
              'black','black','black','black','black','black',]
# declare booleans for status of test system
#RUNNING         = False
#RUNTEXT = ["IDLE   ","RUNNING"]
#LINK_STATUS_LED = False
#TEST_SWITCH1    = False
#TEST_SWITCH2    = False
#BUZZED          = False
#STOPSWITCH     = False
#RAINRELAY      = False
#CHARGERELAY     = False

def startLine(): ser.write(b'G')      #index=1 starts the Arduino test service
def stopLine():  ser.write(b'I')      #doReset stops  the Arduino test service
def setLEDon():  ser.write(b'L')      #setLEDon stops  the Arduino test service
def setLEDoff():  ser.write(b'K')     #setLEDoff stops  the Arduino test service
def setDrainOn():  ser.write(b'D')    #setDrainOn stops  the Arduino test service
def setChargeOn():  ser.write(b'C')   #setChargeOn stops  the Arduino test service
def setRelaysOff():  ser.write(b'-')  #setRelaysOff stops  the Arduino test service
def buzz():      ser.write(b'B')      #buzz stops  the Arduino test service
def HELP():      ser.write(b'H')      #HELP stops  the Arduino test service

#CMDs:Go,Interrupt,L/K LED on/off,Drain,Charge,-Drain&Charge off,Buzz");
#Stat:Idle/Running,L/l led on/off,DIP 1/2,Buzzed,Microswitch,Drain,Charge");

                
need_next_label = True




#  main routine runs once to set up continuus animation and operation
def main():
    #global xaxis, need_next_label, new_label, fig
    #global line_index, list_of_Vlines, list_of_Alines, list_of_xaxis, ax1, ax2, axmaxcount,maxcount_slider
    #global disp_height, disp_width
    #global RUNNING,LINK_STATUS_LED,TEST_SWITCH1,TEST_SWITCH2,BUZZED,ESTOPSWITCH,DRAINRELAY,CHARGERELAY
    #global RUNTEXT
    root = tk.Tk()
    root.withdraw()  #But make it invisible
    root.attributes('-fullscreen', True)
    root.overrideredirect(1)
    root.update_idletasks()
    #root.state('iconic')
    disp_height = root.winfo_screenheight()
    disp_width = root.winfo_screenwidth()

    testtype="________"
    devicename="devicename"
    teststatus='  IDLE  '

    # FLAG TO SIGNAL END OF TEST LINE   ######################
    signalToTerminateLine = False
    def stoplinenow(event):
        nonlocal signalToTerminateLine
        signalToTerminateLine = True

   
    #  DATA LISTS FOR SAMPLE LINES  #############################
    label_list = []
    list_of_Vlines = []    # store lines of trials here (n)
    list_of_Alines = []    # store lines of trials here (n)
    list_of_xaxis = []    # store index of trials here
    line_index = 0
    ax = []
    #INIT FIRST LINE
    label_list.append(" ")
    list_of_Vlines.append([])    #prepare listS for first line
    list_of_Alines.append([])
    list_of_xaxis.append([])
    line_index = 0

    #  LABEL DIALOG ##############################################
    #### global flow control
    need_next_label = True
    getting_new_label = True
    new_label = ""
    num = -1

    def dialogthread():
        #nonlocal line_index
        nonlocal need_next_label, getting_new_label, new_label, num
        #global disp_height, disp_width
        
        need_next_label = True
        time.sleep(2)  #allow return to main
        query_str = "start"
        # line label dialog    
        while 1:
            lock.acquire()
            if need_next_label:
                getting_new_label = True
                lock.release()
                # get labels for lines while animation waits
                newWin=tk.Tk()  #Create a new temporary "parent" to avoid error
                #newWin.withdraw()  #But make it invisible
                # center newWin On Top
                #newWin.title("Dialog Parent")
                newWin.wm_overrideredirect(True)
                newWin.geometry(f'1x1+{disp_width-400}+{disp_height-300}')
                newWin.tk.eval(f'tk::PlaceWindow {newWin._w} center')
                #newWin.update_idletasks()
                #newWin.lift()
                newWin.attributes("-topmost", True)
                query_str = "BAT"+str(line_index+1)   # line 0 is BAT '1'
                new_label = simpledialog.askstring(" Battery Number ",
                                                   " Enter Next Battery Number  ",
                                                    initialvalue = query_str, parent = newWin)
                #time.sleep(.5)
                lock.acquire()
                newWin.destroy()  #Destroy the temporary "parent"
                if new_label:
                    getting_new_label = False    #new label is set
                    num = -1
                    lock.release()
                    while need_next_label:
                        time.sleep(.1)
                else:
                    lock.release()
                    new_label = "ESC"
                    getting_new_label = False    #new label is set
                    plt.savefig(filename[:-4]+".png", format='png')
                    time.sleep(.3)
                    print("canceled")
                    plt.close()
                    return       #from thread
            else:
                lock.release()
            numnow = num
            if num == 10:
                setDrainOn()
                buzz()
            if num == testseconds+10:
                setRelaysOff()
                buzz()
            if num == testseconds+30:
                stoplinenow(True)
                buzz()
                time.sleep(0.2)
                buzz()
            #if num == 10:
            #if num == 10:
            #time.sleep(.9)
            for n in range(10):
                if numnow == num:
                    time.sleep(.1)  #wait up to 1 sec or until num changes
        # End Of While

    # Create figure for plotting
    fig = plt.figure('Team 341 Battery Testing, Voltage and Amps',
                     figsize=[14.0, 8.0])
    ax1 = fig.add_subplot(1, 1, 1)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    plt.subplots_adjust(bottom=0.20, right=0.9)
    
    # GUI stop button #################################
    axstop = plt.axes([0.81, 0.005, 0.1, 0.055])
    bstop = Button(axstop, 'Stop')
    bstop.on_clicked(stoplinenow)

    # SLIDER ############################################    
    maxsampledraw = 30
    maxsamplerange = 30
    maxcount_slider = ""

    # The function to be called anytime a slider's value changes
    def update(val):
        nonlocal maxsampledraw, maxsamplerange, maxcount_slider
        
        temp = int(maxcount_slider.val)
        if temp != maxsampledraw:
            maxsampledraw = temp
            maxcount_slider.val = temp
            maxcount_slider.canvas.draw_idle()

    # Make a horizontal slider to control the frequency.
    axmaxcount = fig.add_axes([0.15, 0.1, 0.75, 0.02])
    maxcount_slider = Slider(
        ax=axmaxcount,
        label='Max Count',
        valmin=0,
        valmax=maxsamplerange,
        valinit=maxsampledraw,
        valstep=1
    )
    # register the update function with each slider
    maxcount_slider.on_changed(update)
    
    # create instances of status displays  #################
    #RUNSTATE,LEDSTATE,SW1STATE,SW2STATE,BZDSTATE,STPSTATE,DRASTATE,CHGSTATE
    runlabel = fig.text(0.02, 0.05,"STATUS", size=14, color='b')
    ledlabel = fig.text(0.11, 0.05, "LED", size=10, color='b')
    sw1label = fig.text(0.25, 0.05,"SW1", size=10, color='b')
    sw2label = fig.text(0.31, 0.05, "SW2", size=10, color='b')
    bzdlabel = fig.text(0.41, 0.05, "BUZZER", size=10, color='b')
    stplabel = fig.text(0.51, 0.05, "STOPSW", size=10, color='b')
    dralabel = fig.text(0.61, 0.05, "DRAIN", size=10, color='b')
    chglabel = fig.text(0.71, 0.05, "CHARGE", size=10, color='b')

    runtext = fig.text(0.01, 0.005, "--------", size=24)
    ledtext = fig.text(0.1, 0.005, "--------", size=20)
    sw1text = fig.text(0.24, 0.005, "--------", size=20)
    sw2text = fig.text(0.3, 0.005, "--------", size=20)
    bzdtext = fig.text(0.4, 0.005, "--------", size=16)
    stptext = fig.text(0.5, 0.005, "--------", size=16)
    dratext = fig.text(0.6, 0.005, "--------", size=16)
    chgtext = fig.text(0.7, 0.005, "--------", size=16)

    voltlabel =fig.text(.18, .05, "VOLTS", size=10)
    volttext = fig.text(.18, .005, "------", size=20)
    
##################################################################### local function #########
    # This localfunction is called periodically from FuncAnimation
    def animate(i, xs, ysV, ysA):
        nonlocal need_next_label, getting_new_label, new_label, fig, num
        nonlocal line_index, list_of_Vlines, list_of_Alines, list_of_xaxis, ax, maxsampledraw, maxsamplerange
        #global RUNNING,LINK_STATUS_LED,TEST_SWITCH1,TEST_SWITCH2,BUZZED,ESTOPSWITCH,DRAINRELAY,CHARGERELAY
        #global RUNTEXT
        nonlocal signalToTerminateLine
                    
        #Aquire and parse data from serial port
        data = b'X'    
        while data == b'X':    
          data=ser.readline()      #ascii
          
          if data == b'': #this is a timeout
            print("!",end="")
            data = b'X'
            break
        ## process STATUS data
        data_as_list = data.split(b',')
        statusword = data_as_list[0]
        if len(statusword)<8:
            print(data_as_list)
            return
        if len(data_as_list)<4:
            print(data_as_list)
            return
        
       ############################
       # Update the status variable displays 
        RUNSTATE = ["IDLE","RUN "][int(chr(statusword[0]) == 'R')]
        LEDSTATE = ["OFF","ON "][int(chr(statusword[1]) == 'L')]
        SW1STATE = ["OFF","ON "][int(chr(statusword[2]) == '1')]
        SW2STATE = ["OFF","ON "][int(chr(statusword[3]) == '2')]
        BZDSTATE = ["   -  ","BUZZED"][int(chr(statusword[4]) == 'B')]
        STPSTATE = ["   -  ","BUTTON"][int(chr(statusword[5]) == 'M')]
        DRASTATE = ["   -  ","DRAIN "][int(chr(statusword[6]) == 'D')]
        CHGSTATE = ["   -  ","CHARGE"][int(chr(statusword[7]) == 'C')]
        #print(statusword,RUNSTATE,LEDSTATE,SW1STATE,SW2STATE,BZDSTATE,STPSTATE,DRASTATE,CHGSTATE)

        runtext.set_text(RUNSTATE)
        ledtext.set_text(LEDSTATE)
        sw1text.set_text(SW1STATE)
        sw2text.set_text(SW2STATE)
        bzdtext.set_text(BZDSTATE)
        stptext.set_text(STPSTATE)
        dratext.set_text(DRASTATE)
        chgtext.set_text(CHGSTATE)
        volttext.set_text( float(data_as_list[2].decode())/100)

        if STPSTATE == "BUTTON":
            signalToTerminateLine = True #stoplinenow(True)
       ############################
        lock.acquire()
        if need_next_label:
            if data != b'X':
                theline = data.decode()
                print(theline[:-1]) #,end="")
            if getting_new_label:
                lock.release()
                return
            if new_label == "ESC":   #discontinue waiting for label
                need_next_label = False
                lock.release()
                return
            if new_label == "":   #continue waiting for label
                lock.release()
                return
            need_next_label = False
            label_list[line_index] = new_label
            new_label = ""
            #mngr = plt.get_current_fig_manager()
            #mngr.window.s.deiconify()
            lock.release()
            # This clears the receive buffer so we aren't using buffered data
            ser.reset_input_buffer()
            ser.write(b'G')      # starts the Arduino test service
            return
        lock.release()

        if (signalToTerminateLine): #finish a line
            signalToTerminateLine = False
            stopLine() #tell Arduino to go back to idle state
            print(label_list[line_index],end=" ")
            print(list_of_Vlines[line_index]) #show line data 
            print(list_of_Alines[line_index]) #show line data 
            sV = label_list[line_index] + "," + ",".join(map(str, list_of_Vlines[line_index]))
            sA = label_list[line_index] + "," + ",".join(map(str, list_of_Alines[line_index]))
            print(sV)
            print(sA)
            with open(filename, "a") as file:   # add to file
                file.write(sV + "\n")
                file.write(sA + "\n")
            #BEGIN THE NEXT LINE    
            label_list.append("")        #make room for next line
            list_of_Vlines.append([])    #make room for next line
            list_of_Alines.append([])    #make room for next line
            list_of_xaxis.append([])     #make room for next line
            line_index += 1           #point to it
            #mngr = plt.get_current_fig_manager()
            #mngr.window.s.withdraw()
            need_next_label = True
            return
           
        if data == b'X':
            return    #it's not data
        ## process lines of measurement data
        temp = data_as_list[1]
        if temp == b'' or temp == b'\x000' or temp == b'\x00': 
            num = 0    #sometimes Arduino sends nulls? correct it to '0'
        else:
            num = int(temp)
        volt = int(data_as_list[2])
        amp = int(data_as_list[3])
        absamp = abs(amp)
        print(num,volt,amp,data_as_list[5])         ####### REPORT  value to host
        list_of_Vlines[line_index].append(volt)  #save value to drawing list
        list_of_Alines[line_index].append(amp)  #save value to drawing list
        list_of_xaxis[line_index].append(num)
        if num > maxsamplerange:
            if maxsampledraw == maxsamplerange:
                maxsampledraw =num
            maxsamplerange = num
            maxcount_slider.valmax=maxsamplerange
            maxcount_slider.set_val(maxsampledraw)
            maxcount_slider.ax.set_xlim((maxcount_slider.valmin, maxcount_slider.valmax));    # rescale slider
            maxcount_slider.canvas.draw_idle()
        
        # Draw x and y lists,  refresh plot with new value
        ax1.clear() 
        ax2.clear() 
        for thisline in range(line_index+1):   # last item is range - 1, [line_index] is active
            ax1.plot(list_of_xaxis[thisline][0:maxsampledraw], list_of_Vlines[thisline][0:maxsampledraw],
                          label=label_list[thisline], color=color_list[thisline], linewidth=2 )
            ax2.plot(list_of_xaxis[thisline][0:maxsampledraw], list_of_Alines[thisline][0:maxsampledraw],
                          label=label_list[thisline], color=color_list[thisline],
                          linestyle='dashed' )
        # Format plot
        plt.xticks(rotation=45, ha='right')
        ax1.set_xlabel('time (s)')
        ax1.set_ylabel('Voltage(hundreths)')   #, color=color)
        ax2.set_ylabel('Amps(hundreths)')      #, color=color)
        # plt.ylabel('Charging  Voltage')
        ax1.legend(bbox_to_anchor=(0.02,1.19), ncol=6, loc="upper left")
        #plt.axis([0, None, -50, 750]) #Use None for arbitrary number of trials
        plt.axis([0, None, None, None]) #Use None for arbitrary number of trials
        plt.grid(visible=True)
        # exit animation routine, called again after interval
##################################################################### local function #########
    
    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig, animate, fargs=(list_of_xaxis[0],
                            list_of_Vlines[0], list_of_Alines[0]), interval=700)
    
    askthread = Thread(target = dialogthread)
    askthread.start()

    #time.sleep(3)
    plt.show()    #DEFAULT block=False

    print("EXIT Main")
    root.destroy() # for safety, not needed, Exit event above is the real tk end
    # End Of Main    

##############  beginning of execution  ##########
if (__name__ == '__main__'):
    port_setup()
    time.sleep(3) #create a short delay since opening serial resets the Arduino
    main()
    time.sleep(.3)
    ser.close()

