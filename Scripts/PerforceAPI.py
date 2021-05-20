import os, sys
if sys.version[0] == "3":
    pVersion = 3
else:
    pVersion = 2

try:
    import P4
except:
    modulePath = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "external_modules/p4_api{}".format(pVersion))
    if not modulePath in sys.path:
        sys.path.append(modulePath)
    import P4

import P4Publish


class P4Connection:
    connected = "Connected"
    disconnected = "Disconnected"

class Perforce(P4.P4):
    def __init__(self):
        super().__init__()
        self.p4 = P4.P4()

    # def __getattribute__(self, name):
    #     if hasattr(self.p4, name):
    #         return self.p4.__getattribute__(name)
    #     return super().__getattribute__(name)

    def connectToPerforce(self, retry=3):
        # if (
        #     not hasattr(self, "p4")
        #     or not hasattr(self, "sgPrjId")
        #     or (user and not hasattr(self, "sgUserId"))
        # ):
        is_connected_p4 = False
        try:
            self.p4.disconnect()
        except:
            pass
        self.p4.port = self.core.getConfig("perforce", "port", configPath = self.core.prismIni)
        self.p4.user = self.core.getConfig("perforce", "p4username")
        self.p4.client = self.core.getConfig("perforce", "p4userworkspacename")
        self.p4.password = self.core.getConfig("perforce", "p4userpassword")
        try:
            self.p4.connect()
        except P4.P4Exception as why:
            raise P4.P4Exception("Failed to connect to p4. {}".format(why))
        try:
            self.p4.run_login('-s')
            is_connected_p4 = True
        except P4.P4Exception as why:
            try:
                self.p4.run_login()
                is_connected_p4 = True
            except P4.P4Exception as why:
                raise P4.P4Exception("Failed to login to p4. {}".format(why))
        while not is_connected_p4 and retry != 0:
            is_connected_p4 = self.connectToPerforce(retry-1)
        return is_connected_p4