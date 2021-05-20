import sys
import os

modulePath = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "UserInterfaces")
if not modulePath in sys.path:
    sys.path.append(modulePath)

# from perforce import *