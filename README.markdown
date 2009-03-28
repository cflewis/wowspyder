WoWSpyder
==================
![WoWSpyder image](http://www.planetwarcraft.com/wow/worldinfo/monster/spider.jpg)

WoWSpyder is an API for the [World of Warcraft Armory](http://www.wowarmory.com) written in Python.

Status
======

WoWSpyder is a pre-alpha, work-in-progress product.

License
=======

WoWSpyder is released under the [BSD license](http://creativecommons.org/licenses/BSD/), copyright of the Regents of the University of California. Please pay special attention to the non-endorsement clause. Like all tools, it is possible to abuse WoWSpyder. This license means that I, nor the university where I research, takes any responsibility for your use of WoWSpyder.

*Use WoWSpyder responsibly*. If you don't, Blizzard might pull the plug on XML access, which is bad for everyone.

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

WoWSpyder uses SQLAlchemy to save to a database. That database can be anything SQLAlchemy supports, including MySQL, Oracle and PostgreSQL. By default, it creates an SQLite in-memory database, but doing this means you lose persistence. Persistence will speed up your response time drastically. 


To Do
=====
* Actually finishing to an alpha stage
* Better hiding of private methods
* Better documentation

By better... I mean actually started.

--
[Chris Lewis](http://chris.to)