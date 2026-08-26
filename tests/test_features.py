from pathlib import Path
import pytest

from enterprise_change_graph.analysis import analyze_impact
from enterprise_change_graph.composition import compose_graphs
from enterprise_change_graph.coverage import assess_coverage
from enterprise_change_graph.evidence import ObservedChange, compare_prediction, find_similar_changes
from enterprise_change_graph.importers import import_catalog_csv, import_interface_as_code, import_mapping_as_code
from enterprise_change_graph.model import EnterpriseGraph, GraphValidationError
from enterprise_change_graph.policy import GatePolicy, load_policy
from enterprise_change_graph.quality import analyze_quality
from enterprise_change_graph.release import analyze_release
from enterprise_change_graph.report import render_impact_report
from enterprise_change_graph.review import analyze_diff_impact

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "examples" / "customer-country-change.yaml"


def load_example():
    from enterprise_change_graph.io import load_graph
    return load_graph(EXAMPLE)


def test_relation_rules_change_semantics():
    graph = EnterpriseGraph.from_dict({"version": 1, "nodes": [{"id":"a","type":"data"},{"id":"b","type":"process"}], "edges": [{"source":"a","target":"b","relation":"depends-on"}], "relation_rules": {"depends-on":{"default":"forward","change_kinds":{"decommission":"both"}}}})
    assert {n.id for n in analyze_impact(graph, seeds=["b"], change_kind="schema-change").impacted} == {"b"}
    assert {n.id for n in analyze_impact(graph, seeds=["b"], change_kind="decommission").impacted} == {"a","b"}


def test_filters_are_traversal_barriers():
    graph = EnterpriseGraph.from_dict({"version":1,"nodes":[{"id":"a","type":"data"},{"id":"b","type":"interface"},{"id":"c","type":"test"}],"edges":[{"source":"a","target":"b","relation":"x"},{"source":"b","target":"c","relation":"verified-by"}]})
    result = analyze_impact(graph, seeds=["a"], exclude_node_types=["interface"])
    assert {n.id for n in result.impacted} == {"a"}
    assert result.filtered


def test_composition_allows_cross_file_edges_and_preserves_provenance(tmp_path):
    a=tmp_path/'a.yaml'; b=tmp_path/'b.yaml'
    a.write_text('version: 1\nnodes:\n  - {id: a, type: data}\nedges:\n  - {source: a, target: b, relation: used-by}\n', encoding='utf-8')
    b.write_text('version: 1\nnodes:\n  - {id: b, type: process}\nedges: []\n', encoding='utf-8')
    graph=compose_graphs([a,b])
    assert set(graph.nodes)=={'a','b'}
    assert graph.edges[0].target=='b'
    assert a.as_posix() in graph.nodes['a'].provenance


def test_composition_conflict_requires_namespace(tmp_path):
    a=tmp_path/'a.yaml'; b=tmp_path/'b.yaml'
    a.write_text('version: 1\nnodes:\n  - {id: x, type: data}\nedges: []\n', encoding='utf-8')
    b.write_text('version: 1\nnodes:\n  - {id: x, type: process}\nedges: []\n', encoding='utf-8')
    with pytest.raises(GraphValidationError): compose_graphs([a,b])
    assert set(compose_graphs([a,b], namespaces={str(b):'team2'}).nodes)=={'x','team2.x'}


def test_csv_import(tmp_path):
    nodes=tmp_path/'nodes.csv'; edges=tmp_path/'edges.csv'; changes=tmp_path/'changes.csv'
    nodes.write_text('id,type,name,criticality\na,data,A,high\nb,test,B,medium\n',encoding='utf-8')
    edges.write_text('source,target,relation\na,b,verified-by\n',encoding='utf-8')
    changes.write_text('id,title,seeds,kind\nC1,Change,a,schema-change\n',encoding='utf-8')
    graph=import_catalog_csv(nodes,edges_path=edges,changes_path=changes)
    assert set(graph.nodes)=={'a','b'} and graph.changes['C1'].kind=='schema-change'


def test_interface_adapter(tmp_path):
    source=tmp_path/'interface.yaml'
    source.write_text("""version: '1.0'\ninterface:\n  id: ORDER-API-01\n  name: Orders\n  source: {system: Commerce, object: Order}\n  target: {system: S4, object: SalesOrder}\n  criticality: critical\nownership: {technical: Integration Team}\nmapping: {profile: order-create}\ntests: [{id: accepted, description: Accepted order}]\n""",encoding='utf-8')
    graph=import_interface_as_code(source)
    assert 'interface.order-api-01' in graph.nodes
    assert any(n.type=='owner' for n in graph.nodes.values()) and any(n.type=='test' for n in graph.nodes.values()) and any(n.type=='mapping' for n in graph.nodes.values())


def test_mapping_adapter(tmp_path):
    source=tmp_path/'mapping.yaml'
    source.write_text("""version: 1\nmapping:\n  id: customer-country\n  source: {system: MDG, object: Customer}\n  target: {system: S4, object: BusinessPartner}\n  fields:\n    - {id: country, source: LAND1, target: COUNTRY}\n""",encoding='utf-8')
    graph=import_mapping_as_code(source)
    assert 'mapping.customer-country' in graph.nodes and any(n.type=='mapping-rule' for n in graph.nodes.values())


def test_removal_aware_review_uses_before_graph():
    before=EnterpriseGraph.from_dict({'version':1,'nodes':[{'id':'a','type':'interface'},{'id':'p','type':'process'},{'id':'t','type':'test'}],'edges':[{'source':'a','target':'p','relation':'supports'},{'source':'p','target':'t','relation':'verified-by'}]})
    after=EnterpriseGraph.from_dict({'version':1,'nodes':[{'id':'p','type':'process'},{'id':'t','type':'test'}],'edges':[{'source':'p','target':'t','relation':'verified-by'}]})
    review=analyze_diff_impact(before,after)
    assert review.before_impact is not None and {n.id for n in review.before_impact.impacted}=={'a','p','t'} and 't' in review.regression_tests


def test_coverage_gaps_and_minimal_tests():
    graph=load_example(); impact=analyze_impact(graph,change_id='CR-142'); coverage=assess_coverage(graph,impact)
    assert 'test.otc-tax' in coverage.minimal_regression_tests and coverage.test_coverage_ratio > 0


def test_policy_loader_and_coverage_limits(tmp_path):
    path=tmp_path/'policy.yaml'; path.write_text('policy:\n  max_affected_nodes: 20\n  min_tests: 2\n  max_untested_nodes: 10\n  require_complete_traversal: true\n',encoding='utf-8')
    policy=load_policy(path)
    assert policy.min_tests==2 and policy.require_complete_traversal
    with pytest.raises(GraphValidationError): GatePolicy.from_dict({'wat':1})


def test_quality_diagnostics_find_orphan_and_missing_coverage():
    graph=EnterpriseGraph.from_dict({'version':1,'nodes':[{'id':'a','type':'data','criticality':'critical'},{'id':'orphan','type':'system'}],'edges':[]})
    quality=analyze_quality(graph)
    assert set(quality.orphan_nodes)=={'a','orphan'} and 'a' in quality.high_criticality_without_tests


def test_release_collision_detection():
    graph=EnterpriseGraph.from_dict({'version':1,'nodes':[{'id':'a','type':'data'},{'id':'shared','type':'process'},{'id':'b','type':'data'}],'edges':[{'source':'a','target':'shared','relation':'used-by'},{'source':'b','target':'shared','relation':'used-by'}],'changes':[{'id':'C1','title':'1','seeds':['a']},{'id':'C2','title':'2','seeds':['b']}]})
    assert analyze_release(graph,['C1','C2']).collisions['shared']==('C1','C2')


def test_evidence_comparison_and_similarity():
    impact=analyze_impact(load_example(),change_id='CR-142'); observed=[n.id for n in impact.impacted][:-1]+['production.extra']; comparison=compare_prediction(impact,observed)
    assert comparison.missed_nodes==('production.extra',)
    matches=find_similar_changes(impact,[ObservedChange('OLD',tuple(observed),incidents=('INC1',),outcome='incident')])
    assert matches and matches[0].change_id=='OLD'


def test_report_contains_actionable_sections():
    graph=load_example(); impact=analyze_impact(graph,change_id='CR-142'); coverage=assess_coverage(graph,impact); report=render_impact_report(impact,coverage=coverage)
    assert '## Regression scope' in report and '## Ownership and approvals' in report
