from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math
import pyautogui
from kinematics_3D import Kinematics
import random



def lim(arg, lower, upper):
    return min(upper, max(lower, arg))


def main():
    controller_knee = Controller(controller_ID=1)
    controller_hip = Controller(controller_ID=2)
    controller_abad = Controller(controller_ID=3)

    kinematics = Kinematics()

    freq = 200


    while True:
        freq_measure_time = time.time()

        x_in, y_in = pyautogui.position()

        MaxX = 80
        MaxY = 100 + 58
        MinX = -120
        MinY = -100 + 58



        y = (y_in-1440) / 8 + 80 +58
        x = -x_in / 8 +80
        z = 250  # -y_in/10+280

       # x = lim(x, MinX, MaxX)
       # y = lim(y, MinY, MaxY)

        print(x, y, z)

        knee, hip, abad = kinematics.ik(x, y, z)

        controller_knee.set_position(position=knee, max_torque=1, kd_scale=0.4, kp_scale=0.8)
        controller_hip.set_position(position=hip, max_torque=1, kd_scale=0.4, kp_scale=0.8)
        controller_abad.set_position(position=abad, max_torque=1, kd_scale=0.4, kp_scale=0.8)

        sleep = (1 / freq) - (time.time() - freq_measure_time)
        if sleep < 0: sleep = 0
        time.sleep(sleep)


if __name__ == '__main__':
    main()



