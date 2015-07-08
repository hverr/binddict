class BindException(Exception):
    """Base exception class"""
    def __init__(self, path, msg=None):
        """Initialize a base exception


        - path (list):
            A list of strings leading to the location of the value in the
            dictionary which caused the exception.

        - msg (str):
            A message
        """
        self.path = path
        self.msg = msg

    def __repr__(self):
        return 'BindException(%s, %s)' % (repr(self.path), repr(self.msg))

    def __str__(self):
        return repr(self)

class InvalidTypeException(BindException):
    """Raised when the type of a value does not mach the expected type."""
    def __init__(self, path, found_type, expected_type, value, strict):
        """Initialize a new exception

        - path (list):
            A list of strings leading to the location of the value in the
            dictionary which caused the exception.

        - found_type (type):
            The python type of the value in the data dictionary

        - expected_type (type):
            The expected type as specified in the mapping

        - value (obj):
            The value as found in the data dictionary

        - strict (bool):
            Whether or not strict type checking was being used when this
            exception occurred
        """
        self.path = path
        self.found_type = found_type
        self.expected_type = expected_type
        self.value = value
        self.strict = strict

    def __repr__(self):
        fmt = 'InvalidTypeException(%s, %s, %s, %s, %s)'
        fmt = fmt % (repr(self.path), repr(self.found_type),
                     repr(self.expected_type), repr(self.value),
                     repr(self.strict))
        return fmt

    def __str__(self):
        return repr(self)

class InvalidStringLengthException(BindException):
    """Raised when the length of a string value is too long or too short."""
    def __init__(self, path, value, constraint):
        """Initialize a new exception

        - path (list):
            A list of strings leading to the location of the value in the
            dictionary which caused the exception.

        - value (str):
            The value that caused the exception.

        - constraint (str):
            The constraint that wasn't satisfied (e.g. ">= 5")
        """
        self.path = path
        self.value = value
        self.constraint = constraint

        def __repr__(self):
            fmt = 'InvalidStringLengthException(%s, %s, %s))'
            fmt = fmt % (repr(self.path), repr(self.value),
                         repr(self.constraint))
            return fmt

        def __str__(self):
            return repr(self)

class RequiredValueMissingException(BindException):
    def __init__(self, path, key):
        """Initialize a new exception

        - path (list):
            A list of strings leading to the location of the value in the
            dictionary which caused the exception.

        - value (str):
            The key of the missing value
        """
        self.path = path
        self.key = key

    def __repr__(self):
        fmt = 'RequiredValueMissingException(%s, %s)'
        fmt = fmt % (repr(self.path), repr(self.key))
        return fmt

    def __str__(self):
        return repr(self)

def bind(data, mapping):
    """Type check and map dictionary values.

    This function traverses the mapping dictionary and tries to extract the
    specified values from the data. The specified values are returned in a
    dictionary.

    The functions returns a flat dictionary of mapped values.

    data (dict, list, string, int, float)
    The data to be converted

    mapping (dict)
    A dictionary specifying how data must be converted. The dictionary should
    only have one value with key "root".

    Let a node be a dictionary with the following keys and values:

    - type (type): dict, list, int, str or float (required)
        The type of the value. See also InvalidTypeException.

    - strict (bool): True or False (default=True)
        If strict is set to True, strict type checking is done. If the type of
        the value in the dictionary does not mach, an error is raised. If
        strict is set to False, the value will be cast to the specified type.
        If the cast fails, and error will be raised.

    - optional (bool): True or False (default=False)
        If the value is optional, it doesn't have to be present. The resulting
        dictionary might not have the specified key.

    - destination (object): (optional)
        The key under which the mapped value is stored in the resulting
        dictionary. If the destination is not specified, the value will not be
        included in the final result dictionary.

    - max_len (int): (optional)
        If the type is str, this specifies the maximum string length. If the
        string length is larger an InvalidStringLengthException is raised.

    - min_len (int): (optional)
        If the type is str, this specifies the minimum string length. If the
        string length is larger an InvalidStringLengthException is raised.

    - children (dict): (optional)
        If the type is dict, this should be a dictionary with keys the
        expected keys of the dict and values dictionaries specifying a node.

    Example mapping:
    {
        "root" : {
            "type" : "dict",
            "children" : {
                "name" : {
                    "type" : "str",
                    "destination" : "name",
                    "min_len" : 1,
                    "max_len" : 10
                },
                "info" : {
                    "type" : "dict",
                    "children : {
                        "age" : {
                            "type" : "int",
                            "strict" : False,
                            "destination" : "age"
                        }
                    }
                }
            }
        }
    }

    Using input
    {
        "not_used" : 5,
        "name" : "John Doe",
        "info" : {
            "country" : "BE",
            "age" : "78"
        }
    }

    the result will be
    {
        "name" : "John Doe",
        "age" : 78
    }
    """
    out = {}
    root_mapping = mapping['root']
    __bind(data, root_mapping, ['root'], out)
    return out

def __bind(value, mapping, path, out):
    strict = mapping.get("strict", True)
    t = mapping["type"]
    if t not in [str, int, float, dict, list]:
        raise BindException(path, "Unknown expected type: " + str(t))

    if strict:
        if type(value) is not t:
            raise InvalidTypeException(path, type(value), t, value, True)
        final_value = value
    else:
        try:
            if t is str:
                final_value = str(value)
            elif t is int:
                final_value = int(value)
            elif t is float:
                final_value = float(value)
            elif t is dict:
                final_value = dict(value)
            elif t is list:
                final_value = list(value)
        except ValueError:
            raise InvalidTypeException(path, type(value), t, value, False)

    destination = mapping.get('destination', None)
    if destination:
        out[destination] = final_value

    if t is str:
        min_len = mapping.get('min_len', None)
        if min_len and len(final_value) < min_len:
            raise InvalidStringLengthException(path, value, '>= ' + str(min_len))

        max_len = mapping.get('max_len', None)
        if max_len and len(final_value) > max_len:
            raise InvalidStringLengthException(path, value, '<= ' + str(max_len))
    elif t is dict:
        children = mapping.get('children', {})
        for key, node in children.items():
            path = list(path)
            path.append(key)

            optional = node.get('optional', False)
            if key not in final_value:
                if not optional:
                    raise RequiredValueMissingException(path, key)
            else:
                __bind(final_value[key], node, path, out)
