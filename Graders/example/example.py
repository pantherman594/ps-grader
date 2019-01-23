import subprocess
import os


class Grader:
    def __init__(self):
        self.process = subprocess.Popen("echo Example grader running from {}".format(os.getcwd()), shell=True)

    def cleanup(self):
        self.process.kill()
