import requests
import json
import re
import editdistance

import config


class Students:
    def __init__(self, usernames):
        self.usernames = usernames

        try:
            with open(config.STUDENTS_FILE, "r") as f:
                self.students = json.load(f)
                semi_manual = False
        except IOError:
            print("Students file doesn't exist. Will create.")
            self.students = {}
            semi_manual = True

        gradeable_students = {r['id']: r for r in self.get_gradeable_students()}

        canvas_students = {row['id']: False for row in gradeable_students.values()}

        to_delete = []
        for username, student in self.students.items():
            if student['id'] not in canvas_students:
                to_delete.append(username)
        for username in to_delete:
            del self.students[username]

        for user, data in self.students.items():
            canvas_students[data['id']] = True

        self.unmatched = []
        for username in self.usernames:
            if username['login'] in self.students:
                continue

            if username['name'] is None:
                name = username['login']
            else:
                name = username['name']

            matches = self.get_closest_names(name, gradeable_students.values())

            closest = matches[0]
            if closest['distance'] < 3:
                self.students[username['login']] = {
                    "name": closest['name'],
                    "id": closest['id']
                }
                canvas_students[closest['id']] = True
            username["matches"] = matches

        for username in self.usernames:
            if username['login'] in self.students:
                continue

            if not semi_manual:
                self.unmatched.append(username)
                continue

            if username['name'] is None:
                name = username['login']
                full_name = name
            else:
                name = username['name']
                full_name = "{} ({})".format(name, username['login'])

            matches = username['matches']
            num = min(5, len(matches))

            if num is 0:
                self.unmatched.append(username)
                continue

            print()
            print('0: No match.')

            for i in range(num, 0, -1):
                match = matches[i - 1]
                print('{}: {} ({})'.format(i, match['name'], match['distance']))

            index = self.input_closest('Closest to', num, full_name) - 1

            if index < 0:
                self.unmatched.append(username)
                continue

            self.students[username['login']] = {
                "name": matches[index]['name'],
                "id": matches[index]['id']
            }
            canvas_students[matches[index]['id']] = True

            with open(config.STUDENTS_FILE, "w") as f:
                json.dump(self.students, f)

        unmatched_canvas = [s for s, v in canvas_students.items() if v is False]

        for username in self.unmatched:
            if username['name'] is None:
                name = username['login']
                full_name = name
            else:
                name = username['name']
                full_name = "{} ({})".format(name, username['login'])

            print()
            print('0: No match.')

            for i in range(len(unmatched_canvas), 0, -1):
                unmatch = gradeable_students[unmatched_canvas[i - 1]]
                print('{}: {}'.format(i, unmatch['name']))

            index = self.input_closest('Manual match for', len(unmatched_canvas), full_name) - 1

            if index < 0:
                continue

            manual_match = gradeable_students[unmatched_canvas[index]]
            self.students[username['login']] = {
                "name": manual_match['name'],
                "id": manual_match['id']
            }

        with open(config.STUDENTS_FILE, "w") as f:
            json.dump(self.students, f)

    def input_closest(self, prefix, num, full_name):
        index = input('{} {}: '.format(prefix, full_name))
        try:
            index_int = int(index)
            if index_int >= 0 and index_int <= num:
                return index_int
        except ValueError:
            pass

        print("Please enter an integer between 0 and {}.".format(num))
        return self.input_closest(prefix, num, full_name)

    def get_gradeable_students(self):
        auth_header = {'Authorization': 'Bearer {}'.format(config.CANVAS_TOKEN)}
        r = requests.get(url="{}users?per_page=1000&enrollment_type[]=student".format(config.CANVAS_API), headers=auth_header)

        if r.status_code is not 200:
            print("Request errored.")
            raise SystemExit

        data = json.loads(r.text)
        return data

    def get_closest_names(self, name, orig_students):
        students = []

        for orig_student in orig_students:
            student = dict(orig_student)  # Modify the cloned student
            student['distance'] = editdistance.eval(name, student['name'])
            students.append(student)

        return sorted(students, key=self.get_distance)[:5]

    def get_distance(self, student):
        return student['distance']
