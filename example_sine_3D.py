from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math
from kinematics_3D import Kinematics

torque = 1
radius = 70


def main():
    controller_knee = Controller(controller_ID = 1)
    controller_hip = Controller(controller_ID = 2)
    controller_abad = Controller(controller_ID=3)

    kinematics = Kinematics()

    freq=200

    while True:
        freq_measure_time = time.time()
        phase1 = (time.time()*10) % (2*math.pi)
        phase2 = (time.time()*0.5) % (2 * math.pi)




        x = radius*1.5 * math.cos(phase1)*math.cos(phase2) - 40
        y = radius* math.cos(phase1)*math.sin(phase2)+58
        z = 220 +radius * math.sin(phase1)


        knee, hip, abad = kinematics.ik(x, y, z)


        controller_knee.set_position(position=knee, max_torque=torque, kd_scale=0.5, kp_scale=1)
        controller_hip.set_position(position=hip, max_torque=torque, kd_scale=0.5, kp_scale=1)
        controller_abad.set_position(position=abad, max_torque=torque, kd_scale=0.5, kp_scale=1)



        sleep = (1/freq)-(time.time()-freq_measure_time)
        if sleep < 0: sleep = 0
        time.sleep(sleep)
        #print(f'freq: {1 / (time.time() - freq_measure_time):.1f}')


if __name__ == '__main__':
    main()