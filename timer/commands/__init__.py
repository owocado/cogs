from abc import ABC

from ..abc import CompositeMetaClass
from .timers import TimerCommands
from .timerset import TimerSetCommands


class Commands(
    TimerCommands, TimerSetCommands, ABC, metaclass=CompositeMetaClass
):
    """Class joining all command subclasses"""
