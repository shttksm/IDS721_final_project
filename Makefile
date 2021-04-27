setup:
	python3 -m venv ~/.IDS721_final_project

install:
	pip install --upgrade pip &&\
	pip install -r requirements.txt

test:
	#python -m pytest -vv --cov=myrepolib test/*.py
	#python -m pytest --nbval notebook.ipynb

# validate-circleci:
# 	circleci config process .circleci/config.yml

# run-circleci-local:
# 	circleci local execute

lint:
	hadolint Dockerfile
	pylint --disable=R,C,W1203 app.py

all: install lint test
