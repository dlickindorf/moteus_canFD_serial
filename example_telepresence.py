from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import numpy as np
from scipy.signal import butter, filtfilt
import time


def main():
    controller_1 = Controller(controller_ID=1)
    controller_2 = Controller(controller_ID=2)
    freq=300

    response_data_c1 = controller_1.get_data()
    pos_deg_c1 = response_data_c1[MoteusReg.MOTEUS_REG_POSITION]
    vel_dps_c1 = response_data_c1[MoteusReg.MOTEUS_REG_VELOCITY]

    response_data_c2 = controller_2.get_data()
    pos_deg_c2 = response_data_c2[MoteusReg.MOTEUS_REG_POSITION]
    vel_dps_c2 = response_data_c2[MoteusReg.MOTEUS_REG_VELOCITY]

    filter_pos = 0.2
    filter_vel = 5  # 4
    multiplyer = 4
    kp_scale = 0.2
    kd_scale = 0.8
    max_torque = 0.7

    while True:


        # response_data_c1 = controller_1.get_data()
        # pos_deg_c1 = response_data_c1[MoteusReg.MOTEUS_REG_POSITION]*360
        # vel_dps_c1 = response_data_c1[MoteusReg.MOTEUS_REG_VELOCITY] * 360
        #
        # response_data_c2 = controller_2.get_data()
        # pos_deg_c2 = -response_data_c2[MoteusReg.MOTEUS_REG_POSITION] * 360-110
        # vel_dps_c2 = -response_data_c2[MoteusReg.MOTEUS_REG_VELOCITY] * 360
        #
        #
        # controller_1.set_position(position=(pos_deg_c2)/ 360, velocity=vel_dps_c2/360,  max_torque=0.5, kd_scale=0.2, kp_scale=1)
        # controller_2.set_position(position=(-pos_deg_c1-110) / 360, velocity=-vel_dps_c1/360, max_torque=0.5, kd_scale=0.2, kp_scale=1)

        freq_measure_time = time.time()

        response_data_c1 = controller_1.get_data()
        pos_deg_c1 = (pos_deg_c1*filter_pos + response_data_c1[MoteusReg.MOTEUS_REG_POSITION])/(filter_pos+1)
        vel_dps_c1 = (vel_dps_c1*filter_vel + response_data_c1[MoteusReg.MOTEUS_REG_VELOCITY])/(filter_vel+1)

        response_data_c2 = controller_2.get_data()
        pos_deg_c2 = (pos_deg_c2*filter_pos + response_data_c2[MoteusReg.MOTEUS_REG_POSITION])/(filter_pos+1)
        vel_dps_c2 = (vel_dps_c2*filter_vel + response_data_c2[MoteusReg.MOTEUS_REG_VELOCITY])/(filter_vel+1)


        controller_1.set_position(position=(pos_deg_c2/multiplyer), velocity=vel_dps_c2/multiplyer,  max_torque=max_torque, kd_scale=kd_scale, kp_scale=kp_scale)
        controller_2.set_position(position=(multiplyer*pos_deg_c1) , velocity=vel_dps_c1*multiplyer, max_torque=max_torque, kd_scale=kd_scale, kp_scale=kp_scale)

        print(f'pos c1: {pos_deg_c1:.1f} pos c2: {pos_deg_c2:.1f}')

        sleep = (1/(freq))-(time.time()-freq_measure_time)
        if(sleep<0): sleep = 0
        time.sleep(sleep)


if __name__ == '__main__':
    main()