from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time

def main():
    controller_1 = Controller(controller_ID = 1)
    freq=300
    devider = 80
    while True:

        freq_measure_time = time.time()
        response_data_c1=controller_1.get_data()
        pos_deg_c1 = response_data_c1[MoteusReg.MOTEUS_REG_POSITION]*360
        pos_set_c1=(pos_deg_c1-((pos_deg_c1)%(360/devider)-(360/devider/2)))
        controller_1.set_position(position=pos_set_c1 / 360, max_torque=0.6, kd_scale=0., kp_scale=1)

        sleep = (1/(freq))-(time.time()-freq_measure_time)
        if(sleep<0): sleep = 0
        time.sleep(sleep)


if __name__ == '__main__':
    main()