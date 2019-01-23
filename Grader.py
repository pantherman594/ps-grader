import requests
import json
import os
import errno
import random
import sys

from Students import Students
from Downloader import Downloader
import config


class Grader:
    def __init__(self, pset_num, additional_filters=""):
        self.pset_num = pset_num
        self.downloader = Downloader(pset_num, additional_filters)
        self.students = Students(self.downloader.usernames)
        self.assignment = self.get_assignment()

        grades = self.grade_psets()
        print("Look over grades before submitting:")
        for canvas_id, data in grades.items():
            grade = data['grade']
            comments = data['comments']
            print(canvas_id)
            print("Grade:", grade)
            print("Comments:", comments)
            print()

        if self.input_submit():
            for canvas_id, data in grades.items():
                grade = data['grade']
                comments = data['comments']
                self.upload_grade(canvas_id, grade, comments)

    def input_submit(self):
        ready = input("Are you ready to submit? [y/N] ").lower()
        if ready == "y":
            return True
        elif ready == "n":
            print("Submission cancelled. Quitting..")
            raise SystemExit

        return self.input_submit()

    def upload_grade(self, canvas_id, grade, comments):
        auth_header = {'Authorization': 'Bearer {}'.format(config.CANVAS_TOKEN)}
        payload = {'comment[text_comment]': comments, 'submission[posted_grade]': grade}
        r = requests.put(url="{}assignments/{}/submissions/{}".format(config.CANVAS_API, self.assignment['id'], canvas_id), headers=auth_header, data=payload)

        if r.status_code is not 200:
            print("Request errored.")
            raise SystemExit

    def get_assignment(self):
        auth_header = {'Authorization': 'Bearer {}'.format(config.CANVAS_TOKEN)}
        r = requests.get(url=config.CANVAS_API + "assignments", headers=auth_header)

        if r.status_code is not 200:
            print("Request errored.")
            raise SystemExit

        data = json.loads(r.text)

        last_pset_num = 0
        last_pset_index = -1
        for i, row in enumerate(data):
            if not row['name'].lower().startswith("problem set"):
                continue
            try:
                pset_num = int(row['name'].split(' ')[-1])
            except ValueError:
                continue

            if self.pset_num is not None:
                if pset_num == self.pset_num:
                    last_pset_num = pset_num
                    last_pset_index = i
                    break
            elif pset_num > last_pset_num:
                last_pset_num = pset_num
                last_pset_index = i

        return data[last_pset_index]

    def store_grades(self, grades, repo, grade, comments):
        for collaborator in repo['collaborators']:
            if collaborator['login'] in self.students.students:
                student = self.students.students[collaborator['login']]['id']
                grades[student] = {'grade': grade,
                                   'comments': comments}
            else:
                print("Unable to save because this student hasn't been matched to Canvas.")

    def input_feedback(self, repo, max_points, grades):
        ready = input("Do you wish to submit feedback? [Y/n] ").lower()
        if ready == "y" or ready == "":
            grade = self.input_grade(max_points)
            if grade == max_points:
                comments = self.input_comments(random.choice(config.GOOD_JOB))
            else:
                comments = self.input_comments()

            confirm = input("Does the above look OK? [Y/n] ").lower()
            if confirm == "y" or confirm == "":
                self.store_grades(grades, repo, grade, comments)
            else:
                self.input_feedback(repo, max_points, grades)

    def input_grade(self, max_points):
        grade = input("Grade (out of {}): ".format(max_points))
        try:
            grade_int = int(grade)
            if grade_int >= 0 and grade_int <= max_points:
                return grade_int
        except ValueError:
            pass

        print("Please enter an integer between 0 and {}.".format(max_points))
        return self.input_grade(max_points)

    def input_comments(self, default=""):
        comments = input("Comments [{}]: ".format(default))
        if comments != "":
            return comments
        if default != "":
            return default

        print("Please provide comments.")
        return self.input_comments()

    def grade_psets(self):
        pset_name = "ps{}".format(self.pset_num)

        try:
            os.makedirs(pset_name)
            raise Exception("Directory did not exist, did repositories download?")
        except OSError as e:
            """
            errno.EEXIST is raised if the directory already exists.
            If the error is not that, raise an exception
            """
            if e.errno != errno.EEXIST:
                raise

        try:
            sys.path.insert(0, '{}/Graders/{}'.format(os.getcwd(), pset_name))
            PSGrader = __import__("ps1", globals(), locals(), ["Grader"], 0)
            with cd("./{}".format(pset_name)):
                assignment_name = self.assignment['name']
                assignment_id = self.assignment['id']
                max_points = int(self.assignment['points_possible'])

                grades = {}

                for repo in self.downloader.repositories:
                    try:
                        with cd("./{}".format(repo['name'])):
                            # Clear terminal screen
                            print('\x1b[2J\x1b[H')

                            print("Assignment: {} ({})".format(assignment_name, assignment_id))
                            print("Grading: {}".format(repo['name']))
                            print()
                            grader = PSGrader.Grader(repo)
                            print(grader.get_output())
                    except OSError:
                        raise Exception("Directory did not exist, did repositories download?")

                    self.input_feedback(repo, max_points, grades)

                    # Kill the grader process, if it's still running
                    grader.cleanup()
        except OSError:
            raise
        return grades


class cd:
    # Context manager for changing the current working directory
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


if __name__ == "__main__":
    # get_assignments()
    # additional_filters (optional) accepts a regex string
    # Grader(1, additional_filters="bau")
    # Grader(1, additional_filters="[a-eA-E]")
    # Grader(1, additional_filters="(?!MikeOh6)")

    if len(sys.argv) is 1:
        print("python3 Grader.py <problem set number> [additional filters]")
        raise SystemExit
    elif len(sys.argv) is 2:
        additional_filters = ""
    else:
        additional_filters = sys.argv[2]

    pset_num = int(sys.argv[1])
    Grader(pset_num, additional_filters)
