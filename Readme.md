# QualysReporting
Tool to help with automation of Qualysguard scan report download and delivery.

Disclaimer: This is not associated with Qualys in any way, this is just the
skeleton of something I have created that fits my needs.

Apologies for the poor packaging and coding. I will be improving both in the future.

# Versions
## v 0.2.0
Stuff actually works now. Setup instructions and dockerfile/containers to come.

## v 0.1.0
This is really just a skeleton of something that I have gotten working with
specific configurations that I will not really outline here. I am expecting
this to be the jumping off point before I refactor everything and make this
much more user-friendly and manageable. The way I currently had it set up
is going to end up being a nightmare for me as I add more scans to the
scheduling.

That said, if there is any desire to get this setup before I have made this
easier to setup I can definitely provide instructions.

# Requirements
## Python Packages
* SQLAlchemy
* Requests
* Psycopg2

## Other requirements
* Some sort of database (only tested on postgresql for now).
* libpq-dev for psycopg2
* python-dev for psycopg2
* pip to install python packages


