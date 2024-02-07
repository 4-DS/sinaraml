all: clean format wheel sdist
	ls -lah dist

sdist:
	python3 -m build . --sdist

wheel:
	python3 -m build . --wheel

format:
	python3 -m black .
	python3 -m isort --profile black .
	$(MAKE) linter

linter:
	python3 -m black . --check --diff
	python3 -m isort --profile black . --check --diff
	flake8 .

clean:
	rm -rf sinaraml/_version.py
	rm -rf build
	rm -rf *.egg-info
	rm -rf dist