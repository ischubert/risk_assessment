# Risk Assessment of stock investments using historic data

This projects aims at estimating the risk of investments into a share by histogramming historic value data as a function of the duration of the investment.

![Alt text](thumbnail.png?raw=true "Histogram of return as function of duration")

## Folders

- data: Folder containing data, e.g. downloads of historical stock value data downloaded from the alpha vantage API
- output: Folder for generated figures and other output
- code: Folder containing the python modules
- notebooks: Folder containing example Jupyter notebooks with data vizualizations

## Setup

Make sure you have https://github.com/kennethreitz/pipenv installed.

Setup project

    $ make setup # setup virtualenv
    $ cp dotenv_example .env

And save your alpha vantage key in `.env`.
Activate the pipenv environment

    $ source .env

and within the now activated environment shell, install it as Jupyter kernel

    $ ipython kernel install --user --name=risk_assessment

Install more dependencies via

    $ pipenv install ...

# Run

Activate pipenv environment using

    $ source .env

Start your Jupyter notebook session

    $ jupyter notebook

and choose `risk_assessment` as kernel
