from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time

def main():
    c = Controller(controller_ID = 1)
    c.command_stop()


    freq=200
    time_zero = time.time()
    base_pos = 1.25
    pull_duration = 0.05 #0.25 #0.05
    release_duration = 0.05 #0.1 #0.05
    duty_cycle = 0.8 # 4 #0.5
    max_torque = 3 # 5 #3
    standbay_torque = 0.05 #0.1 #0.05
    previous_phase = 0
    max_measured_velocity = 0
    counter = 21000
    while True:
        freq_measure_time = time.time()
        phase = (time.time()-time_zero) % (duty_cycle)

        if phase < pull_duration:
            torque =max_torque
            measurements = c.set_position(position = 0, max_torque=4, ff_torque=max_torque, kp_scale=0, kd_scale=0, get_data=True, print_data=False)
        elif phase >= pull_duration and phase <= pull_duration+release_duration:
            release_phase = ((pull_duration+release_duration-phase)/release_duration) #goes from 1 to 0
            torque = standbay_torque+(max_torque-standbay_torque)*release_phase
            measurements = c.set_position(position = 0, max_torque=4, ff_torque=torque, kp_scale=0, kd_scale=0, get_data=True, print_data=False)
        else:
            measurements = c.set_position(position = 0, max_torque=4, ff_torque=standbay_torque , kp_scale=0, kd_scale=0.1, get_data=True, print_data=False)

        if max_measured_velocity < abs(measurements[MoteusReg.MOTEUS_REG_VELOCITY]):
            max_measured_velocity = abs(measurements[MoteusReg.MOTEUS_REG_VELOCITY])
            print(abs(measurements[MoteusReg.MOTEUS_REG_VELOCITY]))
        if max_measured_velocity>25: break;

        if (previous_phase > phase):
            counter = counter + 1
            print("Temperature = " + str(measurements[MoteusReg.MOTEUS_REG_TEMP_C]) + "  Counter = " + str(counter))
        previous_phase = phase

        sleep = (1/freq)-(time.time()-freq_measure_time)
        if sleep < 0: sleep = 0
        time.sleep(sleep)
        #print(f'freq: {1 / (time.time() - freq_measure_time):.1f}')

    c.set_position(position=0, velocity=0, max_torque=1, ff_torque=max_torque, kp_scale=0, kd_scale=1, get_data=True, print_data=False)

if __name__ == '__main__':
    main()