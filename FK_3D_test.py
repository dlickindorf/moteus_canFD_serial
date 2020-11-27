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

    freq=20

    while True:
        freq_measure_time = time.time()

        response_data_knee = controller_knee.get_data()
        robot_knee_rot_org = response_data_knee[MoteusReg.MOTEUS_REG_POSITION]
        knee_deg = kinematics.rad_to_deg(kinematics.robot_to_rad_for_knee(robot_knee_rot_org))

        response_data_hip = controller_hip.get_data()
        robot_hip_rot_org= response_data_hip[MoteusReg.MOTEUS_REG_POSITION]
        hip_deg = kinematics.rad_to_deg(kinematics.robot_to_rad_for_hip(robot_hip_rot_org))

        response_data_abad = controller_abad.get_data()
        robot_abad_rot_org = response_data_abad[MoteusReg.MOTEUS_REG_POSITION]
        abad_deg = kinematics.rad_to_deg(kinematics.robot_to_rad_for_abad(robot_abad_rot_org))

        x, y, z = kinematics.fk(robot_knee_rot_org, robot_hip_rot_org, robot_abad_rot_org)
        robot_knee_rot_proc, robot_hip_rot_proc, robot_abad_rot_proc = kinematics.ik(x,y,z)


        print(f'X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}')
        #print(f'knee: {knee_deg:.2f}, hip: {hip_deg:.2f}, abad: {abad_deg:.2f} ')
        # print(f'knee: {kinematics.rad_to_deg(kinematics.robot_to_rad_for_knee(robot_knee_rot_org)):.2f} / '
        #       f'{kinematics.rad_to_deg(kinematics.robot_to_rad_for_knee(robot_knee_rot_proc)):.2f}, '
        #       f'hip: {kinematics.rad_to_deg(kinematics.robot_to_rad_for_hip(robot_hip_rot_org)):.2f} / '
        #       f'{kinematics.rad_to_deg(kinematics.robot_to_rad_for_hip(robot_hip_rot_proc)):.2f}, '
        #       f'abad: {kinematics.rad_to_deg(kinematics.robot_to_rad_for_abad(robot_abad_rot_org)):.2f} / '
        #       f'{kinematics.rad_to_deg(kinematics.robot_to_rad_for_abad(robot_abad_rot_proc)):.2f}')


        # print(kinematics.if_ik_possible(x, z))
        # robot_hip_rot_processed, robot_knee_rot_processed = kinematics.ik(x, z)
        #
        # knee_deg_processed = kinematics.rad_to_deg(kinematics.robot_to_rad_for_knee(robot_knee_rot_processed))
        # hip_deg_processed = kinematics.rad_to_deg(kinematics.robot_to_rad_for_hip(robot_hip_rot_processed))
        #
        # print(f'knee: {knee_deg_org:.2f} / {knee_deg_processed:.2f}, hip: {hip_deg_org:.2f} / {hip_deg_processed:.2f}, X: {x:.2f}, Z: {z:.2f}')



        sleep = (1 / freq) - (time.time() - freq_measure_time)
        if sleep < 0: sleep = 0
        time.sleep(sleep)
        # print(f'freq: {1 / (time.time() - freq_measure_time):.1f}')

if __name__ == '__main__':
    main()