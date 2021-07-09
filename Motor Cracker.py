from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import numpy
import math


def main():
    ###############################################  SETUP PARAMETERS   ############################################
    rod_length = 500  # rod length from center of motor to the center of the bearing in meters
    max_torque = 4  # range of commanded torques will be from zero to this value
    step_count = 20  # how many measurements you want to do
    ramp_up_time = 0.2  # no to create a hard hit torque will ramp up to the max value over this amount of time
    hold_time = 1  # if no user input is provided motor will turn off after this time to prevent overheating
    safety_max_velocity = 1 #if rotational velocity gets higher than this the machine stops commanding torque
    direction_flip = True
    ###################################################################################################################

    # don't know how to do it yet but we need functionality to redo a measurement


    print("Welcome to Motor Cracker")
    print("Please set all the settable parameters in code. You will be asked to perform a series of measurements. \n"
          "To start a measurement you will click Enter. Than the motor will start exerting force on the scale, it will \n"
          "quickly ramp it up (over ramp_up_time) instead of instantly turning it on to avoid a sudden hit. \n"
          "It will hold torque for some time (hold_time) and than release. You need to read out the value shown by the \n"
          "scale during the time when the motor holds (in grams)  and input it into this program, and click enter to go \n"
          "to next measurement. If you already read the value and want the motor to releace before hold_time passes - click Space\n")


    # create multi-dim array by providing shape
    results = numpy.empty(shape=(step_count+1,2), dtype='object')
    results[0, 0] = 0
    results[0, 1] = 0
    if direction_flip: direction = -1
    else: direction = 1

    c = Controller(controller_ID=1)

    for i in range(1,step_count+1):
        c.command_stop() #comand_stop cleares anny errors/faults in the controller
        input("Start looking at the scale and click enter")
        #wait for user to start the test

        time.sleep(0.5) #to give user time to switch attention

        torque_reached_in_this_cycle = (max_torque/step_count)*i #torque that will be commanded in this measurement step

        #code to ramp up torque from 0 to torque_reached_in_this_cycle  over ramp_up_time
        time_before_ramp_start = time.time()
        while time.time() <= time_before_ramp_start + ramp_up_time:
            commanded_torque = ((time.time()-time_before_ramp_start)/ramp_up_time)*torque_reached_in_this_cycle
            measurement = c.set_torque(torque=direction*commanded_torque, get_data=True, print_data=False)
            if abs(measurement[MoteusReg.MOTEUS_REG_VELOCITY]) > safety_max_velocity:
                c.command_stop() #this will disable the motor fi it reaches a velocity over safety_max_velocity
                break

         #code to hold the  torque_reached_in_this_cycle over the hold_time
        time_before_measurement = time.time()
        while time.time() <= time_before_measurement + hold_time:
            commanded_torque = torque_reached_in_this_cycle
            measurement = c.set_torque(torque=direction*commanded_torque, get_data=True, print_data=False)
            if abs(measurement[MoteusReg.MOTEUS_REG_VELOCITY]) > safety_max_velocity:
                c.command_stop()  # this will disable the motor fi it reaches a velocity over safety_max_velocity
                break
            #if "user clicks space" : break


        scale_redout = input("commanded " +str(int(torque_reached_in_this_cycle*100)/100) + " Nm. \nPlease input the redout from the kitchen scale (in grams!) : ")


        real_torque = float(scale_redout)*rod_length/100000 #calculation and unit conversion

        # code to put those two values it in a new line in a CSV file

        results[i, 0] = torque_reached_in_this_cycle
        results[i, 1] = real_torque

        time.sleep(torque_reached_in_this_cycle*2) # wait between measurements to let the motor cool down to minimise the importance of thermal effects - this is not what we are measuring in this test

    print(results)



if __name__ == '__main__':
    main()