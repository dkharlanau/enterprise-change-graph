import json
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).parents[1]


def test_example_matches_json_schema():
    schema = json.loads(
        (ROOT / "schema" / "enterprise-change-graph.schema.json").read_text()
    )
    example = yaml.safe_load(
        (ROOT / "examples" / "customer-country-change.yaml").read_text()
    )

    jsonschema.validate(example, schema)
