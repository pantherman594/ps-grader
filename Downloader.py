import requests
import json
import re
import os
import errno
import subprocess

import config


class Downloader:
    def __init__(self, pset_num, additional_filters=""):
        self.pset_num = pset_num
        self.usernames = []
        self.repositories = []
        self.download(additional_filters)

    def download(self, additional_filters):
        print("Downloading problem set {}".format(self.pset_num))

        pset_name = "ps{}".format(self.pset_num)
        prefix = pset_name + "-" + additional_filters
        match_filter = re.compile(prefix)

        try:
            os.makedirs(pset_name)
        except OSError as e:
            """
            errno.EEXIST is raised if the directory already exists.
            If the error is not that, raise an exception
            """
            if e.errno != errno.EEXIST:
                raise

        try:
            with cd("./{}".format(pset_name)):
                self.repos = self.get_matching_repos(match_filter)

                print()
                try:
                    with cd("./{}".format(pset_name)):
                        print(pset_name, "already exists. Pulling changes...")
                        subprocess.call(['git', 'pull'])
                        subprocess.call(['git', 'reset', '--hard', 'origin/master'])
                        subprocess.call(['git', 'clean', '-f', '-d', '-x'])
                except OSError:
                    print("Cloning {}...".format(pset_name))
                    subprocess.call(['git', 'clone', 'git@github.com:BC-CSCI-1102-S19-TTh3/{}.git'.format(pset_name)])

                print()
                update_repos = input("Update repositories? [y/N] ").lower() == 'y'
                clean_repos = update_repos or input("Clean repositories? [y/N] ").lower() == 'y'
                for repo in self.repos:
                    self.repositories.append({
                        "name": repo['name'],
                        "collaborators": repo['collaborators']['nodes']
                    })
                    self.usernames.extend(repo['collaborators']['nodes'])

                    try:
                        with cd("./{}".format(repo['name'])):
                            if update_repos is True:
                                print()
                                print(repo['name'], "already exists. Pulling changes...")
                                subprocess.call(['git', 'pull'])

                            if clean_repos is True:
                                if update_repos is not True:
                                    print()
                                    print(repo['name'], "already exists. Resetting changes...")

                                subprocess.call(['git', 'reset', '--hard', 'origin/master'])
                                subprocess.call(['git', 'clean', '-f', '-d', '-x'])
                    except OSError:
                        print()
                        print("Cloning {}...".format(repo['name']))
                        subprocess.call(['git', 'clone', repo['sshUrl']])
        except OSError:
            raise

    def get_members(self):
        query = {'query': "\n".join([
            'query {',
            '  organization(login: "{}") {{'.format(config.ORGANIZATION),
            '    membersWithRole(first: 100) {',
            '      edges {',
            '        role',
            '        node {',
            '          login',
            '        }',
            '      }',
            '    }',
            '  }',
            '}'
            ])
        }
        auth_header = {'Authorization': 'bearer {}'.format(config.GITHUB_TOKEN)}

        r = requests.post(url=config.GITHUB_API, json=query, headers=auth_header)

        if r.status_code is not 200:
            print("Request errored.")
            raise SystemExit

        data = json.loads(r.text)

        if 'errors' in data:
            print("GraphQL error:")
            for error in data['errors']:
                print("  ", error['message'])
            raise SystemExit

        if 'data' not in data:
            print("No data returned")
            raise SystemExit

        return [edge['node']['login'] for edge in data['data']['organization']['membersWithRole']['edges'] if edge['role'] == 'ADMIN']

    def get_repos(self, after=None):
        """
        In descending order, so the larger psets are near the front (ps8 > ps4
        alphabetically). Unfortunately this won't be effective beyond 9
        """
        repo_args = 'first: 100, orderBy: {field: NAME, direction: DESC}'
        if after is not None:
            repo_args += ', after: "{}"'.format(after)

        query = {'query': "\n".join([
            'query {',
            ' organization(login: "{}") {{'.format(config.ORGANIZATION),
            '   repositories({}) {{'.format(repo_args),
            '     edges {',
            '       node {',
            '         name',
            '         sshUrl',
            '         collaborators(first: 100) {',
            '           nodes {',
            '             name',
            '             login',
            '           }',
            '         }',
            '       }',
            '       cursor',
            '     }',
            '   }',
            ' }',
            '}'
            ])
        }
        auth_header = {'Authorization': 'bearer {}'.format(config.GITHUB_TOKEN)}

        r = requests.post(url=config.GITHUB_API, json=query, headers=auth_header)

        if r.status_code is not 200:
            print("Request errored.")
            raise SystemExit

        data = json.loads(r.text)

        if 'errors' in data:
            print("GraphQL error:")
            for error in data['errors']:
                print("  ", error['message'])
            raise SystemExit

        if 'data' not in data:
            print("No data returned")
            raise SystemExit

        return data['data']['organization']['repositories']['edges']

    def get_matching_repos(self, match_filter):
        members = self.get_members()
        complete = False
        after = None
        matching = False
        matching_repos = []

        while not complete:
            repos = self.get_repos(after)

            if len(repos) is 0:
                break

            for repo in repos:
                name = repo['node']['name']
                after = repo['cursor']

                for i in range(len(repo['node']['collaborators']['nodes']) - 1, -1, -1):
                    if repo['node']['collaborators']['nodes'][i]['login'] in members:
                        del repo['node']['collaborators']['nodes'][i]

                if len(repo['node']['collaborators']['nodes']) == 0:
                    continue

                if match_filter.match(name) is not None:
                    matching = True
                    matching_repos.append(repo['node'])
                else:
                    if matching:
                        matching = False
                        complete = True
                        break

        # switch back to regular alphabetical order (see note under get_repos)
        return matching_repos[::-1]


class cd:
    # Context manager for changing the current working directory
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
