import math

homin_hip = 0.3688
homing_knee = 0.478
homing_abad= -1.6408

class Kinematics:

    def __init__(self,Femur = 160, Tibia = 150, Radius = 35, Abad_offset_in_Z=20, Abad_offset_in_Y=58,
                 Hip_Home_Angle_Deg = homin_hip*60 - 78, Knee_Home_Angle_Deg = homing_knee * 60 + 11,
                 Abad_Home_Angle_Deg = homing_abad*60+265, reduction = 6., range = 130):

        self.Hip_Home_Angle_in_Cad_Deg = 42.5
        self.Knee_Home_Angle_in_Cad_Deg = 110
        self.Abad_Home_Angle_in_Cad_Deg = 0

        self.f=Femur
        self.t=Tibia
        self.abadZ = Abad_offset_in_Z
        self.abadY = Abad_offset_in_Y
        self.reduction = reduction
        self.range = range

        self.Knee_Home_Angle_Deg = Knee_Home_Angle_Deg
        self.Hip_Home_Angle_Deg = Hip_Home_Angle_Deg
        self.Abad_Home_Angle_Deg =Abad_Home_Angle_Deg

        self.Hip_Offset = 180 - (Hip_Home_Angle_Deg + self.Hip_Home_Angle_in_Cad_Deg)
        self.Knee_Offset = 180 - (Knee_Home_Angle_Deg + self.Knee_Home_Angle_in_Cad_Deg)
        self.Abad_Offset = 180 - (Abad_Home_Angle_Deg + self.Abad_Home_Angle_in_Cad_Deg)





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

    def robot_to_rad_for_abad(self, robot_abad_rot):
        return self.deg_to_rad(robot_abad_rot * 360 / self.reduction + self.Abad_Offset)

    def rad_to_robot_for_knee(self, rad_knee):
        return (self.rad_to_deg(rad_knee) - self.Knee_Offset) / 360 * self.reduction

    def rad_to_robot_for_hip(self, rad_hip):
        return (self.rad_to_deg(rad_hip) - self.Hip_Offset) / 360 * self.reduction

    def rad_to_robot_for_abad(self, rad_abad):
        return (self.rad_to_deg(rad_abad) - self.Abad_Offset) / 360 * self.reduction

    def fk(self, robot_knee_robot, robot_hip_robot, robot_abad_robot):

        knee_rad = self.robot_to_rad_for_knee(robot_knee_robot)
        hip_rad = self.robot_to_rad_for_hip(robot_hip_robot)
        robot_abad_rot = self.robot_to_rad_for_abad(robot_abad_robot)

        x = math.cos(knee_rad) * self.t + math.cos(hip_rad) * self.f
        z = self.abadZ*math.cos(robot_abad_rot) + self.abadY*math.sin(robot_abad_rot) + (math.sin(knee_rad) * self.t + math.sin(hip_rad) * self.f)*math.cos(robot_abad_rot)
        y = self.abadY*math.cos(robot_abad_rot) - self.abadZ*math.sin(robot_abad_rot) -(math.sin(knee_rad) * self.t + math.sin(hip_rad) * self.f)*math.sin(robot_abad_rot)

        return x, y, z

    def if_ik_possible(self, x, y, z): #TODO add y
        abad_rad=0

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
        if self.limits(self.rad_to_deg(knee_rad), self.rad_to_deg(hip_rad), self.rad_to_deg(abad_rad)):
            return True
        else:
            return False

    def ik(self, x, y, z):
        if y == 0: y = 0.0000001
        if x == 0: x = 0.0000001
        try:
            zp=(y**2+z**2-self.abadY**2)**(1/2)-self.abadZ
            abad_rad=-self.deg_to_rad(90) + (math.atan2(z,y)+math.atan2(self.abadY, zp+self.abadZ))

            l = math.sqrt(x**2+zp**2)
            delta = math.acos((self.f ** 2 + l ** 2 - self.t ** 2) / (2 * self.f * l))
            gamma = math.atan2(zp, x)

            if gamma < 0:
                gamma = self.deg_to_rad(180) + gamma

            hip_rad = delta + gamma
            knee_rad = math.atan((zp-self.f*math.sin(hip_rad))/(x-self.f*math.cos(hip_rad)))
            if knee_rad < 0:
                knee_rad = self.deg_to_rad(180) + knee_rad
        except:
            print('inverse kinematics math error')
            return math.nan, math.nan, math.nan

        if self.limits(self.rad_to_deg(knee_rad), self.rad_to_deg(hip_rad), self.rad_to_deg(abad_rad)):
            return self.rad_to_robot_for_knee(knee_rad), self.rad_to_robot_for_hip(hip_rad), self.rad_to_robot_for_abad(abad_rad)
        else:
            print('inverse kinematics limits error')
            return math.nan, math.nan, math.nan



    def limits(self, knee_deg, hip_deg, abad_deg):
        if 150 > hip_deg-knee_deg > 42 and \
                (180 - self.Hip_Home_Angle_in_Cad_Deg - self.range / 2) < hip_deg < (180 - self.Hip_Home_Angle_in_Cad_Deg + self.range / 2) and \
                (self.Abad_Home_Angle_in_Cad_Deg - self.range / 2) < abad_deg < (self.Abad_Home_Angle_in_Cad_Deg + self.range / 2) and \
                (180 - self.Knee_Home_Angle_in_Cad_Deg - self.range / 2) < knee_deg < (180 - self.Knee_Home_Angle_in_Cad_Deg + self.range / 2):
            #print(f'knee: {knee_deg:.2f}, hip: {hip_deg:.2f}, abad: {abad_deg:.2f} ')
            return True
        else:
            #print(f'knee: {knee_deg:.2f}, hip: {hip_deg:.2f}, abad: {abad_deg:.2f} ')
            return False
