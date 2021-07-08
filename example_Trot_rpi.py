from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math
from kinematics_3D import Kinematics
import random


def gait_engine(period, stride, direction_deg, phase=time.time(), ground_z = 250, lift_hight=70, y_zero = 58,
                time_proportions = { 'ground' : 15, 'ret' : 4, 'lift' : 4, 'descend' : 7},
                kp_scales = { 'ground' : 0.8, 'ret' : 0.8, 'lift' : 0.8, 'descend' : 0.8},
                kd_scales = { 'ground' : 0.8, 'ret' : 0.8, 'lift' : 0.8, 'descend' : 0.8}):
    # geometry - [mm]
    phase = phase % period
    air_z = ground_z - lift_hight

    if stride >= 30:
        sin_scaler = 0.76
    else:
        sin_scaler = stride / 45

    start_x = 0.5 * stride
    end_x = -stride + start_x

    #time
    sum = time_proportions['ground'] + time_proportions['lift'] + time_proportions['ret'] + time_proportions['descend']

    ground_end = (time_proportions['ground'] / sum) * period
    lift_end = ((time_proportions['ground'] + time_proportions['lift']) / sum) * period
    return_end = ((time_proportions['ground'] + time_proportions['lift'] + time_proportions['ret']) / sum) * period
    descend_end = ((time_proportions['ground'] + time_proportions['lift'] + time_proportions['ret'] + time_proportions['descend']) / sum) * period

    ground_duration = ground_end
    lift_duration = lift_end - ground_end
    return_duration = return_end - lift_end
    descend_duration = descend_end - return_end

    direction = direction_deg / 360 * math.pi * 2

    #ground
    if phase <= ground_end:
        ground_phase = phase / ground_duration

        x = math.cos(direction) * (start_x + (end_x - start_x) * ground_phase)
        y = y_zero + math.sin(direction) * (start_x + (end_x - start_x) * ground_phase)
        z = ground_z + (ground_z - ground_z) * ground_phase
        kp_scale = kp_scales['ground']
        kd_scale = kd_scales['ground']

    #lift
    if ground_end < phase <= lift_end:
        lift_phase = (phase - ground_end) / lift_duration  # normalize to 0-1

        x = math.cos(direction) * (end_x + (sin_scaler * (ground_z - air_z)) * (-math.sin(lift_phase * math.pi)))
        y = y_zero + math.sin(direction) * (
                    end_x + (sin_scaler * (ground_z - air_z)) * (-math.sin(lift_phase * math.pi)))
        z = ground_z + (air_z - ground_z) * (math.sin(lift_phase * math.pi - math.pi / 2) / 2 + 0.5)
        kp_scale = kp_scales['ground']
        kd_scale = kd_scales['ground']

    #return
    if lift_end < phase <= return_end:
        return_phase = (phase - lift_end) / return_duration  # normalize to 0-1

        x = math.cos(direction) * (end_x + (start_x - end_x) * return_phase)
        y = y_zero + math.sin(direction) * (end_x + (start_x - end_x) * return_phase)
        z = air_z
        kp_scale = kp_scales['ground']
        kd_scale = kd_scales['ground']

    #descend
    if return_end < phase <= descend_end:
        descend_phase = (phase - return_end) / descend_duration  # normalize to 0-1

        x = math.cos(direction) * (start_x + (sin_scaler * (ground_z - air_z)) * (math.sin(descend_phase * math.pi)))
        y = y_zero + math.sin(direction) * (
                    start_x + (sin_scaler * (ground_z - air_z)) * (math.sin(descend_phase * math.pi)))
        z = air_z + (ground_z - air_z) * (math.sin(descend_phase * math.pi - math.pi / 2) / 2 + 0.5)
        kp_scale = kp_scales['ground']
        kd_scale = kd_scales['ground']
    single_leg_xyz_positions_dict=dict()
    single_leg_xyz_positions_dict[x] = x
    single_leg_xyz_positions_dict[y] = y
    single_leg_xyz_positions_dict[z] = z

    return single_leg_xyz_positions_dict, kp_scale, kd_scale



def main():







    begin_time=time.time()

    phase_offsets = dict()
    phase_offsets['lf']=0
    phase_offsets['lb']=period/2
    phase_offsets['rf']=period/2
    phase_offsets['rb']=0


    while True:






        positions = dict()
        positions['lf'] = dict()
        positions['lb'] = dict()
        positions['rf'] = dict()
        positions['rb'] = dict()

        # carthesian
        positions['lf']['x'] = x
        positions['lf']['y'] = y
        positions['lf']['z'] = z

        positions['lb']['x'] = x
        positions['lb']['y'] = y
        positions['lb']['z'] = z

        positions['rf']['x'] = x
        positions['rf']['y'] = y
        positions['rf']['z'] = z

        positions['rb']['x'] = x
        positions['rb']['y'] = y
        positions['rb']['z'] = z





if __name__ == '__main__':
    main()