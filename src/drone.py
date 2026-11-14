import requests

class DroneError(Exception):
    """ Every wrapper error will be based on this class """

class DroneConnectionError(DroneError):
    """ It wasn't possible to communicate with uav-api """

class DroneCommandError(DroneError):
    """ uav-api answeredd, but a fail occured """

class Drone():
    def __init__(self, base_url="http://localhost:8000", default_timeout=5.0):
        self.base_url = base_url
        self.default_timout = default_timeout
        self._session = requests.Session()

    def _request(self, method, path, *, params = None, json = None, timeout = None):
        url = f"{self.base_url}{path}"
        try:
            response = self._session.request(
                method,
                url,
                params = params,
                json = json,
                timeout = timeout or self.default_timeout,
            )
        except requests.exceptions.RequestException as e:
            raise DroneConnectionError(f"Fail to access {path}: {e}")

        if response.status_code != 200:
            try: 
                detail = response.json().get("detail", response.text)
            except ValueError:
                raise DroneCommandError(f"{path} -> HTTP {response.status_code}: {detail}")
        return response.json()

    def arm(self):
        self._request("GET", "/command/arm", timeout = 60)

    def takeoff(self, alt):
        if not isinstance(alt, int) or not (0 < alt < 500):
            raise DroneCommandError(f"Height = {alt} is unsupported. The value should be between 0 and 500")
        self._request("GET", "/command/takeoff", params = {"alt": alt}, timeout = 60)

    def land(self):
        self._request("GET", "/command/land", timeout = 60)