# ps-grader
_Download and grade problem sets_

## Config

Copy `config.py.template` to `config.py` and fill in the required values.


## Usage

Run `python3 Grader.py <problem set number> "[additional filters]"`

The search string is, by default, `ps{num}-`

Additional filters is a regex string that is appended to the search string.


## Graders

Graders go in `{project root}/Graders/ps{mum}/ps{num}.py`

To make your own, copy the template. The grader doesn't actually grade it for you (though it could), but rather quickly open up and setup the repository to allow you to grade.
