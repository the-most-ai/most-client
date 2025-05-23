

deps:
	pip install -r requirements.txt

lint:
	isort --profile black most
	black most/ --line-length 64

wheel:
	python setup.py build_ext -j 8 && python setup.py bdist_wheel && rm -rf build *.egg-info

publish:
	python3 -m twine upload dist/*
