import subprocess
import random
from datetime import datetime
import os

DUE_DATE = datetime(2019, 1, 31, 23, 59)
DUE_STR = DUE_DATE.strftime("%c")

commit = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"


class Grader:
    def __init__(self, repo):
        self.repo = repo

        self.sugg_points = 10
        self.explanations = []

        self.editor_process = subprocess.Popen(["atom", "."])

        self.process = subprocess.Popen(["git", "log", "--color", "--name-status", "--until", DUE_STR, "-n", "3", "{}..HEAD".format(commit)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.process.wait()
        self.output.append(self._get_raw_output()[0])

        rand = random.randint(1, 7)
        self.sugg_points -= rand
        self.explanations.append("-{}: Example deduction of points".format(rand))

        # self.process = subprocess.Popen("echo Example grader running from {}".format(os.getcwd()), shell=True)

    def get_output(self):
        return "Starting atom..."

    def cleanup(self):
        self.editor_process.kill()
        self.process.kill()
