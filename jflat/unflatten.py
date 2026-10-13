import re


def unflatten(flattened):
    """
    Takes a flattened dictionary with JSONPath-style keys and converts it back to a nested structure.

    Args:
        flattened (dict): A flattened dictionary with JSONPath-style keys

    Returns:
        dict | list: A nested dictionary (or list, if the keys describe a top-level list)

    Raises:
        ValueError: If the keys contradict each other (e.g., a path is used as both a list and a dictionary)
    """
    # First, collect all values in a tree of nodes (list or dict), tracking the type of each node
    root = _Node()
    for key, value in flattened.items():
        path = path_from(key)
        current = root
        for i, k in enumerate(path):
            if i == len(path) - 1:
                current.set(k, value, key)
            else:
                current = current.child(k, key)

    # Then, convert the tree to the nested structure
    if root.is_slice is None:
        return {}
    return root.build()


class _Node:
    """A container node (list or dict) of the structure being unflattened."""

    def __init__(self):
        self.is_slice = None  # Unknown until the first child is added
        self.children = {}

    def _check_type(self, k, key):
        if self.is_slice is None:
            self.is_slice = k.is_slice()
        elif self.is_slice != k.is_slice():
            raise ValueError(f"Conflicting types at key '{key}': element is used as both a list and a dictionary")

    def child(self, k, key):
        """Returns the child container node for the given path key, creating it if necessary."""
        self._check_type(k, key)
        child = self.children.setdefault(k.key(), _Node())
        if not isinstance(child, _Node):
            raise ValueError(f"Conflicting values at key '{key}': element is both a value and a container")
        return child

    def set(self, k, value, key):
        """Sets a leaf value for the given path key."""
        self._check_type(k, key)
        if k.key() in self.children:
            raise ValueError(f"Conflicting values at key '{key}': element is both a value and a container")
        self.children[k.key()] = value

    def build(self):
        """Recursively converts this node into a list or dict."""
        built = {k: v.build() if isinstance(v, _Node) else v for k, v in self.children.items()}
        if self.is_slice:
            return to_slice(built)
        return built


def to_slice(d):
    """
    Converts a dictionary with numeric keys to a list.

    Args:
        d (dict): Dictionary with numeric keys (as strings)

    Returns:
        list: List with values at the correct indices
    """
    # Find the largest index to determine the slice size
    max_idx = max(int(k) for k in d.keys())
    slice_result = [None] * (max_idx + 1)

    for k, v in d.items():
        idx = int(k)
        if idx < 0 or idx >= len(slice_result):
            raise ValueError(f"Index {idx} out of bounds")
        slice_result[idx] = v

    return slice_result


class PathKey:
    """Represents a component in a JSONPath."""

    def __init__(self, name="", index=-1):
        self.name = name
        self.index = index

    def is_slice(self):
        """Returns True if this path component refers to a list index."""
        return self.index != -1

    def key(self):
        """Returns the key name as a string."""
        if self.is_slice():
            return str(self.index)
        return self.name


def path_from(key):
    """
    Parses a JSONPath-style key into a list of PathKey objects.

    Args:
        key (str): JSONPath-style key (e.g., "$.users[0].name")

    Returns:
        list: List of PathKey objects
    """
    # Remove the leading $
    key = key.lstrip("$")

    # Split by . but handle the case where the key starts with a dot
    if key.startswith("."):
        key = key[1:]

    split = key.split(".")
    path = []

    for s in split:
        keys = path_keys_from(s)
        path.extend(keys)

    return path


# Matches a key component with an optional name followed by any number of indices, e.g. "users[0][1]"
_KEY_PATTERN = re.compile(r"^([^\[\]]*)((?:\[\d+\])*)$")


def path_keys_from(key):
    """
    Parses a single component of a JSONPath-style key.

    Args:
        key (str): Key component (e.g., "users[0]" or "matrix[0][1]")

    Returns:
        list: List of PathKey objects
    """
    match = _KEY_PATTERN.match(key)
    if not match:
        raise ValueError(f"Invalid key component '{key}'")

    name, indices = match.groups()
    path = []

    # If there's a name part before the brackets (an empty name is a valid key too, if not followed by indices)
    if name or not indices:
        path.append(PathKey(name=name))
    for index in re.findall(r"\[(\d+)\]", indices):
        path.append(PathKey(index=int(index)))

    return path
