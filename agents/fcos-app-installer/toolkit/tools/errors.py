"""The one SpecError class. It lives apart from gen_service.py because that file also runs as a script
(then Python loads it as __main__, and a class defined in it would not match the one other modules raise)."""


class SpecError(Exception):
    pass
