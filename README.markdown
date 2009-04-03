WoWSpyder
==================
![WoWSpyder image](http://www.planetwarcraft.com/wow/worldinfo/monster/spider.jpg)

WoWSpyder is an API for the [World of Warcraft Armory](http://www.wowarmory.com) written in Python.

Status
======

WoWSpyder is a pre-alpha, work-in-progress product.

License
=======

WoWSpyder's source code (and only source code) is released under the [BSD license](http://creativecommons.org/licenses/BSD/), copyright of the Regents of the University of California. Please pay special attention to the non-endorsement clause. Like all tools, it is possible to abuse WoWSpyder. This license means that I, nor the university where I research, takes any responsibility for your use of WoWSpyder.

Included in this distribution is Okoloth's Battlegroups XML file, which has a listing of battlegroups and realms for the US and EU. This is licensed separately under a [Creative Commons Attribution 3.0 License](http://creativecommons.org/licenses/by/3.0/). It can be parsed by using the BattlegroupParser.

*Use WoWSpyder responsibly*. If you don't, Blizzard might pull the plug on XML access, which is bad for everyone.

Setup
=====

Prerequisites
-------------
You'll need an install of [SQLAlchemy](http://www.sqlalchemy.org/) and [PyYaml](http://pyyaml.org/wiki/PyYAML), as well as Python 2.6. 2.5 won't cut it!

Other things
------------
Make a yaml file called ".wowspyder.yaml" in the wowspyder/ directory with
a "Database_url" key, with your Database URL.

Architecture
============

Database
--------

WoWSpyder uses SQLAlchemy to save to a database. That database can be anything SQLAlchemy supports, including MySQL, Oracle and PostgreSQL. By default, it creates an SQLite in-memory database, but doing this means you lose persistence. Persistence will speed up your response time drastically. 


To Do
=====
* Actually finishing to an alpha stage.
* Better documentation, both for users and docstrings for developers.
* Handle all the character sheet things.
* <strike>Work on preventing bad use of the script... is it possible to add related stuff lazily, so it doesn't cascade through? Perhaps this is achieved my moving the cascading calls (like Team->Character->Guild) to repeated calls via the actual object instead. team.get_guild which would do the DB check and downloading itself.</strike> This is really trying to prevent using the Arena access... downloading teams, characters is OK. Downloading guilds is iffy, so it has the get\_characters clause on it. I should just put that on the arena.
* Replace caching to get_team, get_guild, get_character

--
[Chris Lewis](http://chris.to)
