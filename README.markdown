WoWSpyder
==================
WoWSpyder is an API for the [World of Warcraft Armory](http://www.wowarmory.com) written in Python. It's not perfect, and if you're not prepared to head into the code once in a while, I don't recommend it's use. I no longer intend to release patches for this.

Status
======

WoWSpyder is a work-in-progress product, but it should work OK. It's been flaky on me recently, so your milage may vary. I'm not all that proud of the code's actual operation (but the code is nice).

License
=======

WoWSpyder's source code (and only source code) is released under the [BSD license](http://creativecommons.org/licenses/BSD/), copyright of the Regents of the University of California. Please pay special attention to the non-endorsement clause! Like all tools, it is possible to abuse WoWSpyder. This license means that I, nor the University of California, takes any responsibility for your use of WoWSpyder, nor endorses any use or derivation of it.

Included in this distribution is Okoloth's Battlegroups XML file, which has a listing of battlegroups and realms for the US and EU. This is licensed separately under a [Creative Commons Attribution 3.0 License](http://creativecommons.org/licenses/by/3.0/). It can be parsed by using the BattlegroupParser.

*Use WoWSpyder responsibly*. If you don't, Blizzard might pull the plug on XML access, which is bad for everyone.

Setup
=====

Prerequisites
-------------
You'll need an install of [SQLAlchemy](http://www.sqlalchemy.org/) and [PyYaml](http://pyyaml.org/wiki/PyYAML), as well as Python 2.5 or higher.

Other things
------------
Make a yaml file called `.wowspyder.yaml` in the `wowspyder/` directory with
a `database_url` key, with your database URL, specified in an SQLAlchemy format. For example, mine looks like:
	
	database_url: mysql://USERNAME:PASSWORD@SERVER:PORT/DB_NAME?charset=utf8&use_unicode=0

Architecture
============

Database
--------

WoWSpyder uses SQLAlchemy to save to a database. That database can be anything SQLAlchemy supports, including MySQL, Oracle and PostgreSQL. The easiest thing is an SQLite in-memory database (specify `database_url: sqlite:///:memory:` in .wowspyder.yaml), but doing this means you lose persistence. Persistence will speed up your response time drastically. 

--
[Chris Lewis](http://cflewis.com)
