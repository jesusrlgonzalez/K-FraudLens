import json
import pytest
from i29.graph_experiment import run

def test_graph_created(sample,tmp_path):
    r=run(sample[1]/'candidate_transactions.csv',tmp_path/'graph.json')
    assert r['source_rows']==sample[2]['candidate_rows'] and r['nodes']>0

def test_graph_has_links(sample,tmp_path):
    r=run(sample[1]/'candidate_transactions.csv',tmp_path/'graph.json')
    assert r['edges']>0 and r['connected_components']>0

def test_graph_not_fraud_accusation(sample,tmp_path):
    r=run(sample[1]/'candidate_transactions.csv',tmp_path/'graph.json')
    assert r['identification_of_fraud_by_graph']=='NONE' and not r['graph_features_used_in_ml']

def test_graph_no_account_identifiers_exported(sample,tmp_path):
    p=tmp_path/'graph.json'; run(sample[1]/'candidate_transactions.csv',p)
    assert 'acct_0001' not in p.read_text()
