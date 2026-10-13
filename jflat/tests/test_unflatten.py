import unittest

from jflat import flatten, unflatten


class TestUnflatten(unittest.TestCase):
    def test_flat(self):
        """Test unflattening a simple flat dictionary"""
        flattened = {"$.a": "foo", "$.b": 2, "$.c": True}
        expected = {"a": "foo", "b": 2, "c": True}
        self.assertEqual(unflatten(flattened), expected)

    def test_flat_with_none(self):
        """Test unflattening a flat dictionary with None values"""
        flattened = {"$.a": "foo", "$.b": None, "$.c": True}
        expected = {"a": "foo", "b": None, "c": True}
        self.assertEqual(unflatten(flattened), expected)

    def test_slice(self):
        """Test unflattening a dictionary with list notation"""
        flattened = {"$.a": "foo", "$.b[0]": "bar", "$.b[1]": 2}
        expected = {"a": "foo", "b": ["bar", 2]}
        self.assertEqual(unflatten(flattened), expected)

    def test_nested_map(self):
        """Test unflattening a dictionary with nested notation"""
        flattened = {"$.a": "foo", "$.b.c": "bar", "$.b.d": 2}
        expected = {"a": "foo", "b": {"c": "bar", "d": 2}}
        self.assertEqual(unflatten(flattened), expected)

    def test_slice_with_nested_maps(self):
        """Test unflattening a dictionary with list and nested dictionary notation"""
        flattened = {"$.a": "foo", "$.b[0].c": "bar", "$.b[0].d": 2, "$.b[1].c": "baz", "$.b[1].d": 3}
        expected = {"a": "foo", "b": [{"c": "bar", "d": 2}, {"c": "baz", "d": 3}]}
        self.assertEqual(unflatten(flattened), expected)

    def test_slice_with_nested_maps_with_nested_slice(self):
        """Test unflattening a complex structure with nested lists"""
        flattened = {
            "$.a": "foo",
            "$.b[0].c": "bar",
            "$.b[0].d[0]": 2,
            "$.b[0].d[1]": True,
            "$.b[1].c": "baz",
            "$.b[1].d[0]": 3,
            "$.b[1].d[1]": False,
        }
        expected = {"a": "foo", "b": [{"c": "bar", "d": [2, True]}, {"c": "baz", "d": [3, False]}]}
        self.assertEqual(unflatten(flattened), expected)

    def test_slice_with_nested_maps_with_nested_slice_with_nested_map(self):
        """Test unflattening a highly complex nested structure"""
        flattened = {
            "$.a": "foo",
            "$.b[0].c": "bar",
            "$.b[0].d[0].e": 2,
            "$.b[0].d[1]": True,
            "$.b[1].c": "baz",
            "$.b[1].d[0].e": 3,
            "$.b[1].d[1]": False,
        }
        expected = {"a": "foo", "b": [{"c": "bar", "d": [{"e": 2}, True]}, {"c": "baz", "d": [{"e": 3}, False]}]}
        self.assertEqual(unflatten(flattened), expected)

    def test_top_level_list(self):
        """Test unflattening a top-level list"""
        flattened = {"$[0]": "foo", "$[1]": 2, "$[2]": {"a": "bar"}}
        expected = ["foo", 2, {"a": "bar"}]
        self.assertEqual(unflatten(flattened), expected)

    def test_nested_slice(self):
        """Test unflattening a list directly nested in a list"""
        flattened = {"$.a[0][0]": 1, "$.a[0][1]": 2, "$.a[1][0]": 3}
        expected = {"a": [[1, 2], [3]]}
        self.assertEqual(unflatten(flattened), expected)

    def test_top_level_nested_slice(self):
        """Test unflattening a top-level list of lists"""
        flattened = {"$[0][0]": 1, "$[0][1]": 2, "$[1][0]": 3}
        expected = [[1, 2], [3]]
        self.assertEqual(unflatten(flattened), expected)

    def test_deeply_nested_slice(self):
        """Test unflattening lists nested in lists multiple levels deep"""
        flattened = {"$[0][0][0]": 1, "$[0][0][1]": 2, "$[0][1][0]": 3}
        expected = [[[1, 2], [3]]]
        self.assertEqual(unflatten(flattened), expected)

    def test_nested_slice_with_nested_maps(self):
        """Test unflattening dictionaries in a list nested in a list"""
        flattened = {"$[0][0].a": 1, "$[0][1].b": 2, "$[1][0].a": 3}
        expected = [[{"a": 1}, {"b": 2}], [{"a": 3}]]
        self.assertEqual(unflatten(flattened), expected)

    def test_key_named_like_internal_marker(self):
        """Test unflattening a dictionary with a key that was formerly used as an internal marker"""
        flattened = {"$.a.isSlice": True, "$.a.b": 1}
        expected = {"a": {"isSlice": True, "b": 1}}
        self.assertEqual(unflatten(flattened), expected)

    def test_empty(self):
        """Test unflattening an empty dictionary"""
        self.assertEqual(unflatten({}), {})

    def test_conflicting_types(self):
        """Test that using a path as both a list and a dictionary raises an error"""
        with self.assertRaises(ValueError):
            unflatten({"$[0][0].a": 1, "$[0].b": 2})

    def test_conflicting_values(self):
        """Test that using a path as both a value and a container raises an error"""
        with self.assertRaises(ValueError):
            unflatten({"$.a": 1, "$.a.b": 2})
        with self.assertRaises(ValueError):
            unflatten({"$.a.b": 2, "$.a": 1})

    def test_roundtrip(self):
        """Test that flattening and unflattening yields the original structure"""
        cases = [
            {"a": "foo", "b": [1, {"c": [True, None]}], "d": {"e": []}, "f": {}, "g": [{}, {"h": {}}]},
            [[1, 2], [3]],
            [[[1]], [[2, 3], []]],
            [[{"a": 1}, {"b": 2}], [{"a": 3}]],
            {"a": [[{"b": [[1], [2]]}]]},
            {"": 1, "isSlice": True},
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(unflatten(flatten(case)), case)


if __name__ == "__main__":
    unittest.main()
