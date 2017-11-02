TEST_FOLDERS = tests
PYTHON_INIT_FILES = __init__.py
FILTER_OUT = $(foreach v,$(2),$(if $(findstring $(1),$(v)),,$(v)))
.PHONY: clean-pyc clean-build docs clean

#Build test objects
TEST_OBJECTS = $(foreach dir, $(TEST_FOLDERS), $(wildcard $(dir)/*.py))
TEST_OBJECTS := $(call FILTER_OUT,$(PYTHON_INIT_FILES), $(TEST_OBJECTS))

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	
clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	
test: $(TEST_OBJECTS)
	$(foreach var, $(TEST_OBJECTS), pipenv run pytest $(var)&)
	
init:
	# python setup.py install 
	pipenv install
	
init-dev:
	pipenv install --dev
run:
	pipenv run python __main__.py
docs:
	cd docs && make html
man:
	cd docs && make man
	
help:
	@echo "clean       - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc   - remove Python file artifacts"
	@echo "clean-test  - remove test and coverage artifacts"
	@echo "test        - run all tests located in $Tests and all subfolders"
	@echo "init    	   - Installs the python requirements and sets up virtual envoinment"
	@echo "run    	   - Runs the given server"
	