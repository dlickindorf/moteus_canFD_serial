from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math
from kinematics import Kinematics


def main():
    controller_knee = Controller(controller_ID = 1)
    controller_hip = Controller(controller_ID = 2)
    response_data_c1 = controller_knee.get_data()
    robot_knee_rot = response_data_c1[MoteusReg.MOTEUS_REG_POSITION]
    response_data_c2 = controller_hip.get_data()
    robot_hip_rot = response_data_c2[MoteusReg.MOTEUS_REG_POSITION]
    kinematics = Kinematics(robot_knee_rot, robot_hip_rot)

    freq=300
    period = 1
    jump_duration = 0.25
    retract_duration = period - jump_duration
    begin_time=time.time()

    while True:
        freq_measure_time = time.time()
        phase = (time.time()-begin_time+jump_duration) % (period)

        if phase <= jump_duration:
            jump_phase = phase/jump_duration
            x = -15
            z = 90 + 190

            if kinematics.if_ik_possible(x, z):
                robot_hip_rot, robot_knee_rot = kinematics.ik(x, z)

                controller_hip.set_position(position=robot_hip_rot, max_torque=2, kd_scale=0.15, kp_scale=1.2)
                controller_knee.set_position(position=robot_knee_rot, max_torque=2, kd_scale=0.15, kp_scale=1.2)




        if phase > period-retract_duration:
            retract_phase = (phase - period + retract_duration) / retract_duration # normalize to 0-1
            x = -15
            z = 280 - 190 * retract_phase

            if kinematics.if_ik_possible(x, z):
                robot_hip_rot, robot_knee_rot = kinematics.ik(x, z)

                controller_hip.set_position(position=robot_hip_rot, max_torque=2, kd_scale=0.5, kp_scale=0.2)
                controller_knee.set_position(position=robot_knee_rot, max_torque=2, kd_scale=0.5, kp_scale=0.2)




        print(phase)

        # if kinematics.if_ik_possible(x, z):
        #     robot_hip_rot_calculated, robot_knee_rot_calculated = kinematics.ik(x, z)
        #
        #     response_data_c1 = controller_knee.get_data()
        #     robot_knee_rot_measured = response_data_c1[MoteusReg.MOTEUS_REG_POSITION]
        #     response_data_c2 = controller_hip.get_data()
        #     robot_hip_rot_measured = response_data_c2[MoteusReg.MOTEUS_REG_POSITION]
        #
        #     #print(robot_hip_rot_calculated, robot_hip_rot_measured, robot_knee_rot_calculated, robot_hip_rot_measured)
        #
        #     controller_hip.set_position(position=robot_hip_rot_calculated, max_torque=1.5, kd_scale=0.8, kp_scale=1.2)
        #     controller_knee.set_position(position=robot_knee_rot_calculated, max_torque=1.5, kd_scale=0.8, kp_scale=1.2)



        sleep = (1/freq)-(time.time()-freq_measure_time)
        if sleep < 0: sleep = 0
        time.sleep(sleep)
        #print(f'freq: {1 / (time.time() - freq_measure_time):.1f}')


if __name__ == '__main__':
    main()