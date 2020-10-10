from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math

def main():
    controller_1 = Controller(controller_ID = 1)
    while True:
        phase = (time.time()*8) % (2. * math.pi);
        angle_deg = 200.0 / 360 * math.sin(phase)
        velocity_dps = 200/ 360 * math.cos(phase)
        torque_Nm=0.1*math.cos(phase)

        #controller_1.command_position(position=angle_deg, velocity=velocity_dps, max_torque=0.3, get_data=True, print_data=False)

        response_data=controller_1.get_data()
        devider = 360
        pos_deg = response_data[MoteusReg.MOTEUS_REG_POSITION]*360
        pos_set=(pos_deg-((pos_deg)%(360/devider)-(360/devider/2)))
        print(pos_set)
        print(response_data[MoteusReg.MOTEUS_REG_POSITION]*360)
        controller_1.command_position(position=pos_set/360,  max_torque=0.6, kd_scale=0.1, kp_scale=4)

        #controller_1.command_velocity(velocity=velocity_dps, max_torque=0.5)

        #controller_1.command_torque(torque=torque_Nm)

if __name__ == '__main__':
    main()