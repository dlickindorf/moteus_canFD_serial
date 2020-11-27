from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math
from kinematics_3D import Kinematics
import random

#for y -60~110 for x -105~50


def main():
    controller_knee = Controller(controller_ID = 1)
    controller_hip = Controller(controller_ID = 2)
    controller_abad = Controller(controller_ID=3)

    kinematics = Kinematics()



    freq=200
    period =1.5

    jump_duration = 0.15
    idle_duration = 0.2 # 0.35

    jump_torque = 2
    land_torque = 1.2

    jump_stance_low = 110
    jump_stance_high = 310

    retract_duration = period - jump_duration - idle_duration
    begin_time=time.time()
    x=0
    y=0
    x_rand_prev = 0
    y_rand_prev = 0

    while True:
        while True:
            y_rand =random.randrange(-12, 98)
            x_rand =random.randrange(-60, 30)
            if ((y_rand-y_rand_prev)**2+(x_rand-x_rand_prev)**2)**(1/2)>60:
                print(f't: {time.time():.2f} x: {x_rand:.2f} x_prev {x_rand_prev:.2f} y: {x_rand:.2f} y_prev {x_rand_prev:.2f}')
                break

        phase=0
        print('NEW')
        while phase<(period-1/freq):
            #print(phase)
            freq_measure_time = time.time()
            phase = (time.time()-begin_time) % (period)

            if phase <= jump_duration:
                jump_phase = phase/jump_duration
                x = x_rand_prev
                y = y_rand_prev
                z = (jump_stance_low+(30/150*(128-y))) + ((jump_stance_high-40/150*((y**2+x**2)**(1/2)))-(jump_stance_low+(30/150*(128-y))))*jump_phase



                knee, hip, abad= kinematics.ik(x, y, z)

                controller_knee.set_position(position=knee, max_torque=jump_torque, kd_scale=0.1, kp_scale=1)
                controller_hip.set_position(position=hip, max_torque=jump_torque*0.9, kd_scale=0.1, kp_scale=1)
                controller_abad.set_position(position=abad, max_torque=jump_torque*0.8, kd_scale=0.1, kp_scale=1)

            if (period - retract_duration) > phase >= jump_duration:
                idle_phase = (phase - jump_duration) / idle_duration  # normalize to 0-1

                x = x_rand_prev + (x_rand - x_rand_prev)*idle_phase
                y = y_rand_prev +  (y_rand - y_rand_prev)*idle_phase
                z = (jump_stance_high-40/150*(((y_rand)**2+x_rand**2)**(1/2)))

                knee, hip, abad = kinematics.ik(x, y, z)

                controller_knee.set_position(position=knee, max_torque=jump_torque, kd_scale=0.4, kp_scale=1)
                controller_hip.set_position(position=hip, max_torque=jump_torque*0.9, kd_scale=0.4, kp_scale=1)
                controller_abad.set_position(position=abad, max_torque=jump_torque*0.8,kd_scale=0.4, kp_scale=1)

            if phase > (period-retract_duration):

                retract_phase = (phase - jump_duration-idle_duration) / retract_duration # normalize to 0-1
                x = x_rand
                y = y_rand
                z = (jump_stance_high-40/150*(((y_rand)**2+x_rand**2)**(1/2))) - ((jump_stance_high-40/150*(((y_rand)**2+x_rand**2)**(1/2)))-(jump_stance_low+(30/150*(128-y))))* retract_phase

                knee, hip, abad = kinematics.ik(x, y, z)

                controller_knee.set_position(position=knee, max_torque=land_torque, kd_scale=0.8, kp_scale=0.4)
                controller_hip.set_position(position=hip, max_torque=land_torque, kd_scale=0.8, kp_scale=0.4)
                controller_abad.set_position(position=abad, max_torque=land_torque, kd_scale=0.8, kp_scale=1)


            sleep = (1/freq)-(time.time()-freq_measure_time)
            if sleep < 0: sleep = 0
            time.sleep(sleep)
            #print(f'freq: {1 / (time.time() - freq_measure_time):.1f}')
        x_rand_prev = x_rand
        y_rand_prev = y_rand


if __name__ == '__main__':
    main()