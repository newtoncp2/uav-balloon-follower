import time
import requests
url = "http://127.0.0.1:8000"

print("armando motores")
res_arm = requests.get(f"{url}/command/arm")
time.sleep(3)

print("enviando comando de decolagem")
res_takeoff = requests.get(f"{url}/command/takeoff", params={"alt": 3})
time.sleep(8)

print("enviando comando de pouso")
res_land = requests.get(f"{url}/command/land")