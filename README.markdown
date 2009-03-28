WoWSpyder
==================
![WoWSpyder image](http://www.planetwarcraft.com/wow/worldinfo/monster/spider.jpg)

WoWSpyder is an API for the [World of Warcraft Armory](http://www.wowarmory.com) written in Python.

Status
======

WoWSpyder is a pre-alpha, work-in-progress product.

License
=======

WoWSpyder is released under the [BSD license](http://creativecommons.org/licenses/BSD/), copyright of the Regents of the University of California.

Setup
=====

Prerequisites
-------------
You'll need an install of [SQLAlchemy](http://www.sqlalchemy.org/) and [PyYaml](http://pyyaml.org/wiki/PyYAML).

Other things
------------
Make a yaml file called ".wowspyder.yaml" in the wowspyder/ directory with
a "database_url" key, with your database URL.

Architecture
============

Database
--------

WoWSpyder uses SQLAlchemy to save to an database. That database can be anything SQLAlchemy supports, including MySQL, Oracle and PostgreSQL. By default, it creates an SQLite in-memory database, but doing this means you lose persistence. Persistence will speed up your response time drastically. 


To Do
=====
* Actually finishing to an alpha stage
* The option of changing 

--
[Chris Lewis](http://chris.to)