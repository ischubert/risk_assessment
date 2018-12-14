default: setup

# setup
Pipfile.lock: Pipfile
	pipenv install

setup: Pipfile.lock

# data

logo.png:
	wget --no-check-certificate --ftp-user='${EGNYTE_USER}' --ftp-password='${EGNYTE_PASSWORD}' 'ftps://ftp-idalab.egnyte.com/Shared/02 Material/10 Logo/idalab_black_150dpi.png' -O download/logo.png

data: logo.png

all: setup data

.PHONY: clean
clean:
	rm logo.png

# analyses
