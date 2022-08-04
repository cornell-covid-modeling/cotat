test:
	coverage run -m pytest

cov:
	coverage report --include=cotat/*

cov-html:
	coverage html
	open htmlcov/index.html

lint:
	flake8 cotat

.PHONY: dist
dist:
	rm -rf dist/*
	python3 -m build
	twine upload dist/*