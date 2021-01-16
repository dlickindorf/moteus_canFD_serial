from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math
from kinematics_3D import Kinematics



def main():
    controller_knee = Controller(controller_ID = 1)
    controller_hip = Controller(controller_ID = 2)
    controller_abad = Controller(controller_ID=3)

    kinematics = Kinematics()
    filter = 20



    freq=200
    period =1.5
    robot_knee_torque=0
    robot_hip_torque = 0
    robot_abad_torque = 0
    homing_speed = 2



    while 1:
        freq_measure_time = time.time()

        if (robot_hip_torque < 0.4):

            response_data_hip = controller_hip.set_position(position=math.nan, velocity=homing_speed, max_torque=0.5,
                                                            kd_scale=0.2,
                                                            get_data=True, print_data=False)
            robot_hip_rot_org = response_data_hip[MoteusReg.MOTEUS_REG_POSITION]
            robot_hip_torque = (response_data_hip[MoteusReg.MOTEUS_REG_TORQUE] + filter * robot_hip_torque) / (
                    filter + 1)

        else:
            hip_home_offset = robot_hip_rot_org
            print("hip:", hip_home_offset)
            break

        sleep = (1 / freq) - (time.time() - freq_measure_time)
        if sleep < 0: sleep = 0
        time.sleep(sleep)

    while 1:
        freq_measure_time = time.time()

        if (robot_knee_torque > -0.4):
            response_data_knee = controller_knee.set_position(position=math.nan, velocity=-homing_speed, max_torque=0.5,
                                                            kd_scale=0.2,
                                                            get_data=True, print_data=False)
            controller_hip.set_position(position=math.nan, velocity=0.1, max_torque=0.8,
                                        kd_scale=0.2)

            robot_knee_rot_org = response_data_knee[MoteusReg.MOTEUS_REG_POSITION]
            robot_knee_torque = (response_data_knee[MoteusReg.MOTEUS_REG_TORQUE] + filter * robot_knee_torque) / (
                    filter + 1)

        else:
            knee_home_offset = robot_knee_rot_org
            print("knee:", knee_home_offset)
            break

    while 1:
        freq_measure_time = time.time()

        if (robot_abad_torque > -0.3):
            response_data_abad = controller_abad.set_position(position=math.nan, velocity=-homing_speed, max_torque=0.4,
                                                              kd_scale=0.2,
                                                              get_data=True, print_data=False)
            controller_hip.set_position(position=hip_home_offset-1, max_torque=0.5,
                                        kd_scale=1)
            controller_knee.set_position(position=math.nan, velocity=math.nan, max_torque=0.8,
                                        kd_scale=0.2)
            robot_abad_rot_org = response_data_abad[MoteusReg.MOTEUS_REG_POSITION]
            robot_abad_torque = (response_data_abad[MoteusReg.MOTEUS_REG_TORQUE] + filter * robot_abad_torque) / (
                    filter + 1)

        else:
            abad_home_offset = robot_abad_rot_org
            print("abad:", abad_home_offset)
            break

    while 1:
        freq_measure_time = time.time()

        controller_hip.set_position(position=hip_home_offset - 1.3, max_torque=0.3, kd_scale=1)
        controller_knee.set_position(position=knee_home_offset +0.19, max_torque=0.3, kd_scale=0.7)
        controller_abad.set_position(position=abad_home_offset + 1.4, max_torque=0.3, kd_scale=0.7)


        sleep = (1 / freq) - (time.time() - freq_measure_time)
        if sleep < 0: sleep = 0
        time.sleep(sleep)










if __name__ == '__main__':
    main()