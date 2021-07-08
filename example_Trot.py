from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math
from kinematics_3D import Kinematics
import random





def main():
    controller_knee = Controller(controller_ID = 1)
    controller_hip = Controller(controller_ID = 2)
    controller_abad = Controller(controller_ID=3)
    kinematics = Kinematics()
    freq = 300

    #PID
    kd_scale_air = 0.3 #D
    kp_scale_air = 1 #P

    kd_scale_ground = 0.6 # D
    kp_scale_ground =  0.6# P
    torque = 1    
    
    period = 1
    
    
    #time proportins
    ground = 15
    ret = 4
    lift = 8
    descend = 10

    #geometry - [mm]
    direction_deg = -45
    stride = 0

    
    
    ground_z = 250
    air_z = ground_z-70
    y_zero = 58



    begin_time=time.time()



    while True:

        stride = 130#math.sin(((time.time() * 0.5) % (2 * math.pi)))*50+50
        print(stride)

        if stride >= 30:
            sin_scaler = 0.76
        else:
            sin_scaler = stride / 45

        start_x = 0.5 * stride
        end_x = -stride + start_x

        sum = ground + lift + ret + descend

        ground_end = (ground / sum) * period
        lift_end = ((ground + lift) / sum) * period
        return_end = ((ground + lift + ret) / sum) * period
        descend_end = ((ground + lift + ret + descend) / sum) * period

        ground_duration = ground_end
        lift_duration = lift_end - ground_end
        return_duration = return_end - lift_end
        descend_duration = descend_end - return_end

        direction = direction_deg / 360 * math.pi * 2









        freq_measure_time = time.time()
        phase = (time.time()-begin_time+lift_duration+ground_duration) % period

        if phase <= ground_end:
            ground_phase = phase/ground_duration


            x= math.cos(direction)*(start_x+(end_x-start_x)*ground_phase)
            y = y_zero+math.sin(direction)*(start_x + (end_x - start_x) * ground_phase)
            z=ground_z+(ground_z-ground_z)*ground_phase


            if kinematics.if_ik_possible(x,y, z):
                knee, hip, abad = kinematics.ik(x, y, z)

                controller_knee.set_position(position=knee, max_torque=torque, kd_scale=kd_scale_ground, kp_scale=kp_scale_ground)
                controller_hip.set_position(position=hip, max_torque=torque, kd_scale=kd_scale_ground, kp_scale=kp_scale_ground)
                controller_abad.set_position(position=abad, max_torque=torque, kd_scale=kd_scale_ground, kp_scale=kp_scale_ground)
            else:
                print(x,z)

        if  ground_end < phase <= lift_end:
            lift_phase = (phase - ground_end) / lift_duration  # normalize to 0-1

            x= math.cos(direction)*(end_x + (sin_scaler *(ground_z - air_z)) * (-math.sin(lift_phase * math.pi)))
            y = y_zero + math.sin(direction)* (end_x + (sin_scaler *(ground_z - air_z)) * (-math.sin(lift_phase * math.pi)))
            z = ground_z + (air_z - ground_z) * (math.sin(lift_phase * math.pi - math.pi / 2) / 2 + 0.5)


            if kinematics.if_ik_possible(x,y, z):
                knee, hip, abad = kinematics.ik(x, y, z)

                controller_knee.set_position(position=knee, max_torque=torque, kd_scale=kd_scale_ground-(kd_scale_ground-kd_scale_air)*lift_phase, kp_scale=kp_scale_ground-(kp_scale_ground-kp_scale_air)*lift_phase)
                controller_hip.set_position(position=hip, max_torque=torque, kd_scale=kd_scale_ground-(kd_scale_ground-kd_scale_air)*lift_phase, kp_scale=kp_scale_ground-(kp_scale_ground-kp_scale_air)*lift_phase)
                controller_abad.set_position(position=abad, max_torque=torque, kd_scale=kd_scale_ground-(kd_scale_ground-kd_scale_air)*lift_phase, kp_scale=kp_scale_ground-(kp_scale_ground-kp_scale_air)*lift_phase)
            else:
                print(x,z)
                
        if lift_end < phase <= return_end:
            return_phase = (phase - lift_end) / return_duration  # normalize to 0-1

            x= math.cos(direction)*(end_x + (start_x - end_x) * return_phase)
            y = y_zero + math.sin(direction)* (end_x + (start_x - end_x) * return_phase)
            z = air_z


            if kinematics.if_ik_possible(x,y, z):
                knee, hip, abad = kinematics.ik(x, y, z)

                controller_knee.set_position(position=knee, max_torque=torque, kd_scale=kd_scale_air, kp_scale=kp_scale_air)
                controller_hip.set_position(position=hip, max_torque=torque, kd_scale=kd_scale_air, kp_scale=kp_scale_air)
                controller_abad.set_position(position=abad, max_torque=torque, kd_scale=kd_scale_air, kp_scale=kp_scale_air)
            else:
                print(x,z)


        if return_end < phase <= descend_end:

            descend_phase = (phase - return_end) / descend_duration # normalize to 0-1

            x = math.cos(direction) * (start_x + (sin_scaler *(ground_z - air_z)) * (math.sin(descend_phase*math.pi)))
            y = y_zero + math.sin(direction)* (start_x + (sin_scaler *(ground_z - air_z)) * (math.sin(descend_phase*math.pi)))
            z = air_z + (ground_z - air_z) * (math.sin(descend_phase*math.pi-math.pi/2)/2+0.5)

            if kinematics.if_ik_possible(x,y, z):
                knee, hip, abad = kinematics.ik(x, y, z)

                controller_knee.set_position(position=knee, max_torque=torque, kd_scale=kd_scale_air+(kd_scale_ground-kd_scale_air)*descend_phase, kp_scale=kp_scale_air+(kp_scale_ground-kp_scale_air)*descend_phase)
                controller_hip.set_position(position=hip, max_torque=torque, kd_scale=kd_scale_air+(kd_scale_ground-kd_scale_air)*descend_phase, kp_scale=kp_scale_air+(kp_scale_ground-kp_scale_air)*descend_phase)
                controller_abad.set_position(position=abad, max_torque=torque, kd_scale=kd_scale_air+(kd_scale_ground-kd_scale_air)*descend_phase, kp_scale=kp_scale_air+(kp_scale_ground-kp_scale_air)*descend_phase)
            else:
                print(x,z)

        sleep = (1/freq)-(time.time()-freq_measure_time)
        if sleep < 0: sleep = 0
        time.sleep(sleep)
        #print(f'freq: {1 / (time.time() - freq_measure_time):.1f}')


if __name__ == '__main__':
    main()