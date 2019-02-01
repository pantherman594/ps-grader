import subprocess
import random
import os


class Grader:
    def __init__(self, repo):
        self.repo = repo

        self.sugg_points = 10
        self.explanations = []

        rand = random.randint(0, 5)
        self.sugg_points -= rand
        self.explanations.append("-{}: Example deduction of points".format(rand))

        # self.process = subprocess.Popen("echo Example grader running from {}".format(os.getcwd()), shell=True)
        self.process = subprocess.Popen(["atom", "."])

    def get_output(self):
        return "Starting atom..."

    def cleanup(self):
        self.process.kill()
