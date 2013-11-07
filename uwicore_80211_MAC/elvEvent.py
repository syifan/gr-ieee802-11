import time
from elvOptions import *


class ElvEvent(object):

    def __init__(self, event):
        self.time = time.time()
        self.event = event
        self.record()

    def record(self):
        if ElvOption.option.verbose:
            print "\n{0:10.2f}: {1}".format(self.time, self.event)

