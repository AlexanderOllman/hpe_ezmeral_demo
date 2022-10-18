
import time
import math
import robomasterpy

class Robot:
    ip: str
    robo: robomasterpy.client.Commander

    def __init__(self):
        self.ip = robomasterpy.get_broadcast_ip()
        self.robo = robomasterpy.Commander(self.ip)
        print("Successfully connected to robot. IP Address: " + self.ip)


    def returnPosition(self):
        robo = self.robo
        x = robo.get_chassis_position()
        pos = []
        for attribute, value in x.__dict__.items():
            pos.append(value)
        return pos

    #---DRIVE---
    # robo.chassis_wheel(front left, rear left, rear right, front right)
    # robo.chassis_wheel(-forward, +forward, -forward, +forward)


    def stop(self):
        robo = self.robo
        robo.chassis_wheel(0, 0, 0, 0)

    def moveForward(self):
        robo = self.robo
        robo.chassis_wheel(-50, 50, -50, 50)

    def moveBackward(self):
        robo = self.robo
        robo.chassis_wheel(50, -50, 50, -50)

    def rotateRight(self):
        robo = self.robo
        robo.chassis_speed(z=90)
        robo.chassis_move(z=30)

    def rotateLeft(self):
        robo = self.robo
        robo.chassis_speed(z=90)
        robo.chassis_move(z=-30)

    def videoStream(self):
        robo = self.robo
        robo.stream(True)


