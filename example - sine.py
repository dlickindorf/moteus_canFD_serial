from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math

def main():
    controller_1 = Controller(controller_ID = 1)
    freq=300
    while True:
        freq_measure_time = time.time()


        phase = (time.time()*1) % (2. * math.pi)
        angle_deg = 100.0 / 360 * math.sin(phase)
        velocity_dps = 100.0/ 360 * math.cos(phase)

        controller_1.set_position(position=angle_deg, max_torque=0.3, kd_scale=0.2, get_data=True, print_data=False)

        # controller_1.set_velocity(velocity=velocity_dps, max_torque=0.5)

        # controller_1.set_torque(torque=torque_Nm)

        sleep = (1/(freq))-(time.time()-freq_measure_time)
        if(sleep<0): sleep = 0
        time.sleep(sleep)


if __name__ == '__main__':
    main()