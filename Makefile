#!make

.PHONY: docs test dist

docs:
	@$(MAKE) -C docs html

test:
	pytest --cov --flake8 .

dist: 	test docs
	python setup.py build build_sphinx
