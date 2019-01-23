import subprocess
import os


class Grader:
    def __init__(self, repo):
        self.repo = repo

        # self.process = subprocess.Popen("echo Example grader running from {}".format(os.getcwd()), shell=True)
        self.process = subprocess.Popen(["atom", "."])

    def get_output(self):
        return "Starting atom..."

    def cleanup(self):
        self.process.kill()
