
from moteus_fdcan_adapter import Controller
from moteus_fdcan_adapter import MoteusReg
import time
import math


def main():
    controller_1 = Controller(controller_ID=2)
    # VitesseDeRotation = 0.5 #Vitesse de rotation (0.5 lent et 5 rapide)
    CoupleMoteur = 0.5
    position= 0

    while True:
        position = position + 0.01
        controller_1.set_position(position=position, max_torque=CoupleMoteur)
        time.sleep(0.01)



if __name__ == '__main__':
    main()