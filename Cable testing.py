from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time

def main():
    #############################################   SETUP PARAMETERS   ################################################
    pull_duration = 0.07 # First part of the cycle - over this amount of time the motor pulls the cable with full Troque
    release_duration = 0.15 # next part of the cycle - a gradual release starting at max torque ending at standby_torque
    duty_cycle = 0.8 #duty cycle of the test
    max_torque = 3 #maximum torque exerted by the motor
    standbay_torque = 0.05 #between pulls the motor still exerts some torque - to keep the cable tight
    ###################################################################################################################

    c = Controller(controller_ID=1) #create controller object
    c.command_stop() #comand_stop cleares anny errors/faults in the controller
    max_measured_velocity = 0 #this variable stores the max measured rotational velocity of the motor and is used for safety and can be observed as an erformance indicator
    counter = 0 #if you had to interrupt testing and need to start again but not count from 0 - input the number starting number you want here.
    time_zero = time.time()
    previous_phase = 0 #variable used to detect switching from one cycle to the next
    while True:
        phase = (time.time()-time_zero) % (duty_cycle) #what is happening during the cycle depends on the phase value. Phase is in seconds

        #below - the behaviour of the system is dependent on the value of phase - in different value ranges different behaviours are triggered
        if phase < pull_duration:
            #initiall full torque pull
            measurements = c.set_position(position = 0, max_torque=4, ff_torque=max_torque, kp_scale=0, kd_scale=0,
                                          get_data=True, print_data=False) #measurements are collected to extract velocity - which if too high stops the system (safety)
        elif phase >= pull_duration and phase <= pull_duration+release_duration:
            #gradual release
            release_phase = ((pull_duration+release_duration-phase)/release_duration) #value normalized from 1 to 0.
            torque = standbay_torque+(max_torque-standbay_torque)*release_phase #torque ges from max_torque to standby_torque
            measurements = c.set_position(position = 0, max_torque=4, ff_torque=torque, kp_scale=0, kd_scale=0,
                                          get_data=True, print_data=False) #measurements are collected to extract velocity - which if too high stops the system (safety)
        else:
            measurements = c.set_position(position = 0, max_torque=4, ff_torque=standbay_torque , kp_scale=0,
                                          kd_scale=0.1, get_data=True, print_data=False) #measurements are collected to extract velocity - which if too high stops the system (safety)

        if max_measured_velocity < abs(measurements[MoteusReg.MOTEUS_REG_VELOCITY]): #for diagnostics
            max_measured_velocity = abs(measurements[MoteusReg.MOTEUS_REG_VELOCITY])
            print("Max velocity that occured so far: " + str(abs(measurements[MoteusReg.MOTEUS_REG_VELOCITY])))
        if max_measured_velocity>25: break;

        if (previous_phase > phase): #code for counting phase cycles
            counter = counter + 1
            print("Temperature = " + str(measurements[MoteusReg.MOTEUS_REG_TEMP_C]) + "  Counter = " + str(counter))
        previous_phase = phase


    c.set_position(position=0, velocity=0, max_torque=1, ff_torque=0, kp_scale=0, kd_scale=1,
                   get_data=True, print_data=False) #if there is a break in the loop above - the velocity limit is exceeded - this command stops the rotr

if __name__ == '__main__':
    main()