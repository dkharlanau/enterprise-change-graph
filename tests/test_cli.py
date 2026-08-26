from pathlib import Path

from enterprise_change_graph.cli import main

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "examples" / "customer-country-change.yaml"


def test_validate_cli(capsys):
    assert main(["validate", str(EXAMPLE)]) == 0
    assert "OK: version=1" in capsys.readouterr().out


def test_diff_cli_accepts_before_and_after_without_graph_argument(tmp_path, capsys):
    before = tmp_path / "before.yaml"
    after = tmp_path / "after.yaml"
    before.write_text(
        """version: 1
nodes:
  - id: a
    type: data
edges: []
""",
        encoding="utf-8",
    )
    after.write_text(
        """version: 1
nodes:
  - id: a
    type: data
    criticality: high
  - id: b
    type: process
edges:
  - source: a
    target: b
    relation: used-by
""",
        encoding="utf-8",
    )

    assert main(["diff", str(before), str(after)]) == 0
    output = capsys.readouterr().out
    assert "Graph diff" in output
    assert "Impact seeds in after graph: a, b" in output
