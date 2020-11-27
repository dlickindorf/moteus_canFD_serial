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
    period = 1.5
    ground_duration = 0.45*period
    lift_duration = 0.45*period # 0.35

    ground_start_x = 80
    ground_start_z = 220
    ground_end_x = -160
    ground_end_z = 220
    air_x = 90
    air_z = 160

    retract_duration = period - ground_duration - lift_duration
    begin_time=time.time()

    while True:
        freq_measure_time = time.time()
        phase = (time.time()-begin_time+lift_duration+ground_duration) % period

        if phase <= ground_duration:
            ground_phase = phase/ground_duration


            x=ground_start_x+(ground_end_x-ground_start_x)*ground_phase
            z=ground_start_z+(ground_end_z-ground_start_z)*ground_phase


            if kinematics.if_ik_possible(x, z):
                robot_hip_rot, robot_knee_rot = kinematics.ik(x, z)

                controller_hip.set_position(position=robot_hip_rot, max_torque=0.4, kd_scale=0.8, kp_scale=1)
                controller_knee.set_position(position=robot_knee_rot, max_torque=0.4, kd_scale=0.8, kp_scale=1)
            else:
                print(x,z)

        if (period - retract_duration) > phase >= ground_duration:
            lift_phase = (phase - ground_duration) / lift_duration  # normalize to 0-1

            x = ground_end_x + (air_x - ground_end_x) * lift_phase
            z = ground_end_z +(air_z - ground_end_z) * lift_phase**0.7


            if kinematics.if_ik_possible(x, z):
                robot_hip_rot, robot_knee_rot = kinematics.ik(x, z)

                controller_hip.set_position(position=robot_hip_rot, max_torque=0.4, kd_scale=0.6, kp_scale=1)
                controller_knee.set_position(position=robot_knee_rot, max_torque=0.4, kd_scale=0.6, kp_scale=1)
            else:
                print(x,z)


        if phase > (period-retract_duration):

            down_phase = (phase - ground_duration-lift_duration) / retract_duration # normalize to 0-1

            x = air_x + (ground_start_x - air_x) * down_phase
            z = air_z + (ground_start_z - air_z) * down_phase**0.4

            if kinematics.if_ik_possible(x, z):
                robot_hip_rot, robot_knee_rot = kinematics.ik(x, z)

                controller_hip.set_position(position=robot_hip_rot, max_torque=0.4, kd_scale=1, kp_scale=0.3)
                controller_knee.set_position(position=robot_knee_rot, max_torque=0.4, kd_scale=1, kp_scale=0.3)
            else:
                print(x,z)








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