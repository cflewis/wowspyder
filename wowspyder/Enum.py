#!/usr/bin/env python
# encoding: utf-8
"""
Enum.py

Created by Chris Lewis on 2009-03-28.
Copyright (c) 2009 Chris Lewis. All rights reserved.
"""

from sqlalchemy import types, exceptions

class Enum(types.TypeDecorator):
    impl = types.Unicode
    
    def __init__(self, values, empty_to_none=False, strict=False):
        """Emulate an Enum type.

        values:
           A list of valid values for this column
        empty_to_none:
           Optional, treat the empty string '' as None
        strict:
           Also insist that columns read from the database are in the
           list of valid values.  Note that, with strict=True, you won't
           be able to clean out bad data from the database through your
           code.
        """

        if values is None or len(values) is 0:
            raise AssertionError('Enum requires a list of values')
        self.empty_to_none = empty_to_none
        self.strict = strict
        self.values = values[:]

        # The length of the string/unicode column should be the longest string
        # in values
        size = max([len(v) for v in values if v is not None])
        super(Enum, self).__init__(size)        
        
        
    def process_bind_param(self, value, dialect):
        if self.empty_to_none and value is '':
            value = None
        if value not in self.values:
            raise AssertionError('"%s" not in Enum.values' % value)
        return value
        
        
    def process_result_value(self, value, dialect):
        if self.strict and value not in self.values:
            raise AssertionError('"%s" not in Enum.values' % value)
        return value
        
if __name__ == '__main__':
    from sqlalchemy import *
    t = Table('foo', MetaData('sqlite:///'),
              Column('id', Integer, primary_key=True),
              Column('e', Enum([u'foobar', u'baz', u'quux', None])))
    t.create()

    t.insert().execute(e=u'foobar')
    t.insert().execute(e=u'baz')
    t.insert().execute(e=u'quux')
    t.insert().execute(e=None)

    try:
        t.insert().execute(e=u'lala')
        assert False
    except AssertionError:
        pass    

    print list(t.select().execute())