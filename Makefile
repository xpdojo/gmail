all: install
.PHONY: all

.PHONY: install
install:
	@# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
	pip install -r requirements.txt

.PHONY: run
run:
	python3 gmail.py
