.PHONY:	test

test:
	TEST=1 nosetests --logging-level=DEBUG && flake8
