import time
from src.drone import Drone

drone = Drone()

drone.arm()
drone.takeoff(5)
drone.land()