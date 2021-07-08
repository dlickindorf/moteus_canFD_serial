from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math


def main():
    ###############################################  SETABLE PARAMETERS   #############################################
    rod_length = 500  # rod length from center of motor to the center of the bearing in meters
    max_torque = 1  # range of commanded torques will be from zero to this value
    step_count = 10  # how many measurements you want to do
    ramp_up_time = 0.5  # no to create a hard hit torque will ramp up to the max value over this amount of time
    hold_time = 1  # if no user input is provided motor will turn off after this time to prevent overheating
    safety_max_velocity = 1 #if rotational velocity gets higher than this the machine stops commanding torque
    ###################################################################################################################

    # don't know how to do it yet but we need functionality to redo a measurement

    c = Controller(controller_ID = 1)
    c.command_stop()

    print("Welcome to Motor Cracker")
    print("Please set all the settable parameters in code. You will be asked to perform a series of measurements. "
          "To start a easurement you will click Enter. Than the motor will start exerting force on the scale, it will "
          "quickly ramp it up (over ramp_up_time) instead of instantly turning it on to avoid a sudden hit. "
          "It will hold torque for some time (hold_time) and than release. You need to read out the value shown by the "
          "scale during the time when the motor holds (in grams)  and input it into this program, and click enter to go "
          "to next measurement. If you already read the value and want the motor to releace before hold_time passes - click Space")

    for i in range(1,step_count+1):
        c.command_stop()
        print("click enter to start measurement")
        #wait for user to start the test


        torque_reached_in_this_cycle = (max_torque/step_count)*i #torque that will be commanded in this measurement step
        print(torque_reached_in_this_cycle)

        #code to ramp up torque from 0 to torque_reached_in_this_cycle  over ramp_up_time
        time_before_ramp_start = time.time()
        while time.time() <= time_before_ramp_start + ramp_up_time:
            commanded_torque = ((time.time()-time_before_ramp_start)/ramp_up_time)*torque_reached_in_this_cycle
            measurement = c.set_position(position=0, max_torque=max_torque, ff_torque=-commanded_torque, kp_scale=0,
                                         kd_scale=0, get_data=True, print_data=False)
            if abs(measurement[MoteusReg.MOTEUS_REG_VELOCITY]) > safety_max_velocity:
                c.command_stop() #this will disable the motor fi it reaches a velocity over safety_max_velocity
                break

         #code to hold the  torque_reached_in_this_cycle over the hold_time
        time_before_measurement = time.time()
        while time.time() <= time_before_measurement + hold_time:
            commanded_torque = torque_reached_in_this_cycle
            measurement = c.set_position(position=0, max_torque=max_torque, ff_torque=-commanded_torque, kp_scale=0,
                                         kd_scale=0, get_data=True, print_data=False)
            if abs(measurement[MoteusReg.MOTEUS_REG_VELOCITY]) > safety_max_velocity:
                c.command_stop()  # this will disable the motor fi it reaches a velocity over safety_max_velocity
                break
            #if "user clicks space" : break


        print("please input the redout from the kitchen scale (in grams!) and click enter")
        #code to take the user input and put it in a new line in a CSV vile next to the  torque_reached_in_this_cycle value

        scale_redout = 10 #change to value given by user
        real_torque = scale_redout*rod_length/100000 #calculation and unit conversion
        commanded_torque = torque_reached_in_this_cycle #real_torque and commanded_torque should be added to the CSV


        time.sleep(torque_reached_in_this_cycle*2) # wait between measurements to let the motor cool down to minimise the importance of thermal effects - this is not what we are measuring in this test



if __name__ == '__main__':
    main()