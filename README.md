# Project Template

This is a project template. It contains a starting point for a typical report-like project.

To use it press the plus on the left, then select "**Fork** this repository"

## Folders

- data: Folder for static data. In git. Maybe using git lfs.
- download: Folder for downloadable files. Gitignored.
- output: Folder for generated files. Gitignored.
- output/figs: Folder for generated figures. Gitignored.
- code: Folder for python files and modules.

## Setup

Make sure you have https://github.com/kennethreitz/pipenv installed.

Setup project

    $ make setup # setup virtualenv
    $ cp dotenv.example .env # and edit if necessary
    $ source .env
    $ docker-compose up
    $ make data # download data and ...

Install more dependencies via

    $ pipenv install ...

# Run

Start docker machine (like above) and then

    $ source .env
    $ docker-compose up

Then connect to Postgres in container with your favorite tool.

Reminder: `docker-machine ip default` for the ip & user & port in dotenv file

## And now?

Look at the data!
