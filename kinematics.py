import math

homin_hip = 0.3649365234375
homing_knee = 0.083289794921875
homing_abad= -1.65106201171875


class Kinematics:

    def __init__(self, current_position_knee, current_position_hip, Femur = 160, Tibia = 150, Radius = 35,
                 Hip_Home_Angle_Deg = homin_hip*60 - 75, Knee_Home_Angle_Deg = homing_knee * 60 + 11, reduction = 6., range = 130):
        self.Hip_Home_Angle_in_Cad_Deg = 42.5
        self.Knee_Home_Angle_in_Cad_Deg = 110
        self.f=Femur
        self.t=Tibia
        self.reduction = reduction
        self.range = range
        self.Knee_Home_Angle_Deg = Knee_Home_Angle_Deg
        self.Hip_Home_Angle_Deg = Hip_Home_Angle_Deg
        self.Hip_Offset = 180 - (Hip_Home_Angle_Deg + self.Hip_Home_Angle_in_Cad_Deg)
        self.Knee_Offset = 180 - (Knee_Home_Angle_Deg + self.Knee_Home_Angle_in_Cad_Deg)
        self.current_position_knee = current_position_knee
        self.current_position_hip = current_position_hip


    def rad_to_deg(self, rad):
        return rad*57.2957795

    def deg_to_rad(self, deg):
        return deg/57.2957795

    def rot_to_rad(self, rot):
        return rot * 360 / 57.2957795

    def rad_to_rot(self, rad):
        return rad / 360 * 57.2957795

    def robot_to_rad_for_knee(self, robot_knee_rot):
        return self.deg_to_rad(robot_knee_rot*360/self.reduction+self.Knee_Offset)

    def robot_to_rad_for_hip(self, robot_hip_rot):
        return self.deg_to_rad(robot_hip_rot * 360 / self.reduction + self.Hip_Offset)

    def rad_to_robot_for_knee(self, rad_knee):
        return (self.rad_to_deg(rad_knee) - self.Knee_Offset) / 360 * self.reduction

    def rad_to_robot_for_hip(self, rad_hip):
        return (self.rad_to_deg(rad_hip) - self.Hip_Offset) / 360 * self.reduction

    def fk(self, robot_knee_rot, robot_hip_rot):
        knee_rad = self.robot_to_rad_for_knee(robot_knee_rot)
        hip_rad = self.robot_to_rad_for_hip(robot_hip_rot)

        x = math.cos(knee_rad) * self.t + math.cos(hip_rad) * self.f
        z = math.sin(knee_rad) * self.t + math.sin(hip_rad) * self.f

        return x, z

    def if_ik_possible(self, x, z):

        if x == 0: x = 0.0000001
        try:
            l = math.sqrt(x ** 2 + z ** 2)
            delta = math.acos((self.f ** 2 + l ** 2 - self.t ** 2) / (2 * self.f * l))
            gamma = math.atan(z / x)
            if gamma < 0:
                gamma = self.deg_to_rad(180) + gamma
            hip_rad = delta + gamma
            knee_rad = math.atan((z-self.f*math.sin(hip_rad))/(x-self.f*math.cos(hip_rad)))
        except:
            return False

        if knee_rad < 0:
            knee_rad = self.deg_to_rad(180) + knee_rad
        if self.limits(self.rad_to_deg(hip_rad), self.rad_to_deg(knee_rad)):
            return True
        else:
            return False

    def ik(self, x, z):

        if x == 0: x = 0.0000001
        l = math.sqrt(x**2+z**2)
        delta = math.acos((self.f ** 2 + l ** 2 - self.t ** 2) / (2 * self.f * l))
        gamma = math.atan(z / x)

        if gamma < 0:
            gamma = self.deg_to_rad(180) + gamma

        hip_rad = delta + gamma
        knee_rad = math.atan((z-self.f*math.sin(hip_rad))/(x-self.f*math.cos(hip_rad)))
        if knee_rad < 0:
            knee_rad = self.deg_to_rad(180) + knee_rad

        return self.rad_to_robot_for_hip(hip_rad), self.rad_to_robot_for_knee(knee_rad)



    def limits(self, hip_deg, knee_deg):
        if 150 > hip_deg-knee_deg > 42 and \
                (180-self.Hip_Home_Angle_in_Cad_Deg -self.range/2) < hip_deg < (180-self.Hip_Home_Angle_in_Cad_Deg +self.range/2) and \
                (180-self.Knee_Home_Angle_in_Cad_Deg -self.range/2) < knee_deg < (180-self.Knee_Home_Angle_in_Cad_Deg +self.range/2):
            return True
        else:
            return False
