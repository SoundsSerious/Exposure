# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 19:47:53 2016

@author: Cabin
"""

from json import JSONEncoder
from datetime import datetime
from time import mktime


class DynamicJSONEncoder(JSONEncoder):
    """ JSON encoder for custom classes:
        Uses __json__() method if available to prepare the object.
        Especially useful for SQLAlchemy models
    """

    def default(self, o):
        # Custom JSON-encodeable objects
        print o
        if isinstance(o, datetime):
            return int(mktime(o.timetuple()))
        elif hasattr(o, '__json__'):
            return o.__json__()

        # Default
        return super(DynamicJSONEncoder, self).default(o)


#region SqlAlchemy Tools

try:
    from sqlalchemy import inspect
    from sqlalchemy.orm.state import InstanceState
except ImportError as e:
    def __nomodule(*args, **kwargs): raise e
    inspect = __nomodule
    InstanceState = __nomodule

###############################################################################
#JSON Encoding
###############################################################################


def get_entity_propnames(entity):
    """ Get entity property names
        :param entity: Entity
        :type entity: sqlalchemy.ext.declarative.api.DeclarativeMeta
        :returns: Set of entity property names
        :rtype: set
    """
    ins = entity if isinstance(entity, InstanceState) else inspect(entity)
    return set(
        ins.mapper.column_attrs.keys() +  # Columns
        ins.mapper.relationships.keys()  # Relationships
    )


def get_entity_loaded_propnames(entity):
    """ Get entity property names that are loaded (e.g. won't produce new queries)
        :param entity: Entity
        :type entity: sqlalchemy.ext.declarative.api.DeclarativeMeta
        :returns: Set of entity property names
        :rtype: set
    """
    ins = inspect(entity)
    keynames = get_entity_propnames(ins)

    # If the entity is not transient -- exclude unloaded keys
    # Transient entities won't load these anyway, so it's safe to include all columns and get defaults
    if not ins.transient:
        keynames -= ins.unloaded

    # If the entity is expired -- reload expired attributes as well
    # Expired attributes are usually unloaded as well!
    if ins.expired:
        keynames |= ins.expired_attributes

    # Finish
    return keynames


class JsonSerializableBase(object):
    """ Declarative Base mixin to allow objects serialization
        Defines interfaces utilized by :cls:ApiJSONEncoder
    """

    def __json__(self, exluded_keys=set()):
        return {name: getattr(self, name)
                for name in get_entity_loaded_propnames(self) - exluded_keys}

    @property
    def asjson(self):
        return json.dumps(u, cls=DynamicJSONEncoder)
#endregion