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

    freq=200
    knee = math.nan
    hip = math.nan
    abad = math.nan
    velocity_knee = 0
    velocity_hip = 0
    velocity_abad = 0

    tq=0
    while True:

        freq_measure_time = time.time()

        x = 0
        y = 0
        z = 0

        data_knee = controller_knee.set_position(position=knee, velocity = velocity_knee/2, max_torque=1*tq, kd_scale=0.2*tq, kp_scale = 1.4*tq, get_data= True)
        data_hip = controller_hip.set_position(position=hip, velocity = velocity_hip/2,  max_torque=1*tq, kd_scale=0.2*tq, kp_scale=1.4*tq, get_data= True)
        data_abad = controller_abad.set_position(position=abad, velocity = velocity_abad/2,  max_torque=2*tq, kd_scale=0.2*tq, kp_scale=1.4*tq, get_data= True)
        tq=0



        x, y, z = kinematics.fk(data_knee[MoteusReg.MOTEUS_REG_POSITION], data_hip[MoteusReg.MOTEUS_REG_POSITION], data_abad[MoteusReg.MOTEUS_REG_POSITION])

        if z > 250:
            z = -((z - 250))*1.5 + z
            tq = 1
        if z < 160:
            z = -((z - 160))*1.5 + z
            tq = 1
        if y > 150:
            y = -((y - 150))*1.5 + y
            tq = 1
        if y < -5:
            y = -((y + 5))*1.5 + y
            tq = 1
        if x > 80:
            x = -((x - 80))*1.5 + x
            tq = 1
        if x < -100:
            x = -((x +100))*1.5 + x
            tq = 1

        knee, hip, abad = kinematics.ik(x, y, z)
        velocity_knee= data_knee[MoteusReg.MOTEUS_REG_VELOCITY]
        velocity_hip = data_hip[MoteusReg.MOTEUS_REG_VELOCITY]
        velocity_abad = data_abad[MoteusReg.MOTEUS_REG_VELOCITY]





        sleep = (1/freq)-(time.time()-freq_measure_time)
        if sleep < 0: sleep = 0
        time.sleep(sleep)
        #print(f'freq: {1 / (time.time() - freq_measure_time):.1f}')


if __name__ == '__main__':
    main()