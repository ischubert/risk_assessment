default: setup

# setup
Pipfile.lock: Pipfile
	pipenv install

setup: Pipfile.lock
