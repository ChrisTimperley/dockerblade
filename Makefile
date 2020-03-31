.PHONY: docs check init test tox

# installs pipenv and builds the project
init:
	sudo pip install pipenv --upgrade
	pipenv install -r requirements.dev.txt
	pipenv install --dev

# builds the documentation
docs:
	pipenv run python setup.py docs

# runs the unit test suite
test:
	pipenv run pytest

tox:
	pipenv run tox

# runs a series of checks on the project via tox
check: tox
