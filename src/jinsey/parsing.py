"""Reject ambiguous mappings and nonstandard numbers at input boundaries."""
import json
import math
from typing import Any

import yaml


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON property {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number {value!r} is not allowed")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        _reject_constant(value)
    return number


def strict_json_loads(source: str) -> Any:
    return json.loads(source, object_pairs_hook=unique_pairs,
                      parse_constant=_reject_constant, parse_float=_finite_float)


class UniqueSafeLoader(yaml.SafeLoader):
    """Safe YAML construction without silently overwritten duplicate fields."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict:
        self.flatten_mapping(node)
        keys = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                if key in keys:
                    raise yaml.constructor.ConstructorError(
                        "while loading a mapping", node.start_mark,
                        f"duplicate YAML property {key!r}", key_node.start_mark,
                    )
                keys.add(key)
            except TypeError as exc:
                raise yaml.constructor.ConstructorError(
                    "while loading a mapping", node.start_mark,
                    "mapping keys must be hashable", key_node.start_mark,
                ) from exc
        return super().construct_mapping(node, deep=deep)


def strict_yaml_load(source: str) -> Any:
    loader = UniqueSafeLoader(source)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()
