from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math
from kinematics import Kinematics


def main():
    controller_knee = Controller(controller_ID = 1)
    controller_hip = Controller(controller_ID = 2)
    controller_abad = Controller(controller_ID=3)

    response_data_c1 = controller_knee.get_data()
    robot_knee_rot = response_data_c1[MoteusReg.MOTEUS_REG_POSITION]
    response_data_c2 = controller_hip.get_data()
    robot_hip_rot = response_data_c2[MoteusReg.MOTEUS_REG_POSITION]
    kinematics = Kinematics(robot_knee_rot, robot_hip_rot)

    freq=300
    period =1

    jump_duration = 0.1
    idle_duration = 0.2 # 0.35


    jump_torque = 2
    land_torque = 1.4

    jump_stance_low = 70
    jump_stance_high = 280
    x_pos = 0

    retract_duration = period - jump_duration - idle_duration
    begin_time=time.time()


    while True:
        freq_measure_time = time.time()
        phase = (time.time()-begin_time+idle_duration+jump_duration) % (period)

        if phase <= jump_duration:
            jump_phase = phase/jump_duration
            x = -x_pos
            z = jump_stance_low + (jump_stance_high-jump_stance_low)*jump_phase


            if kinematics.if_ik_possible(x, z):
                robot_hip_rot, robot_knee_rot = kinematics.ik(x, z)

                controller_hip.set_position(position=robot_hip_rot, max_torque=jump_torque, kd_scale=0.4, kp_scale=1)
                controller_knee.set_position(position=robot_knee_rot, max_torque=jump_torque, kd_scale=0.4, kp_scale=1)

        if (period - retract_duration) > phase >= jump_duration:
            idle_phase = (phase - jump_duration) / idle_duration  # normalize to 0-1

            x = -x_pos-0*idle_phase
            z = jump_stance_high

            # z = jump_stance_high - 10 - 40 * idle_phase
            # if idle_phase<0.25:
            #     x=-60*(idle_phase*4) -15
            # elif idle_phase<0.5:
            #     x=60-120*(idle_phase*2-0.5) -15
            # else:
            #     x=-60+60* (idle_phase * 4 - 3) -15


            if kinematics.if_ik_possible(x, z):
                robot_hip_rot, robot_knee_rot = kinematics.ik(x, z)

                controller_hip.set_position(position=robot_hip_rot, max_torque=jump_torque, kd_scale=0.2, kp_scale=1)
                controller_knee.set_position(position=robot_knee_rot, max_torque=jump_torque, kd_scale=0.2, kp_scale=1)
            else:
                print(x,z)

        if phase > (period-retract_duration):

            retract_phase = (phase - jump_duration-idle_duration) / retract_duration # normalize to 0-1
            x = -x_pos + 0*(1-retract_phase)
            z = jump_stance_high - (jump_stance_high-jump_stance_low) * retract_phase

            if kinematics.if_ik_possible(x, z):
                robot_hip_rot, robot_knee_rot = kinematics.ik(x, z)

                controller_hip.set_position(position=robot_hip_rot, max_torque=land_torque, kd_scale=1, kp_scale=0.3)
                controller_knee.set_position(position=robot_knee_rot, max_torque=land_torque, kd_scale=1, kp_scale=0.3)








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