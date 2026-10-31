import json
import pytest
from i29.experiments import evaluate,feature
from i29.audit import read_csv

@pytest.fixture(scope='module')
def res(sample,tmp_path_factory):
    inp,out,_=sample;tmp=tmp_path_factory.mktemp('exp')
    return evaluate(out/'candidate_transactions.csv',inp/'outcomes_SYNTHETIC_EVALUATION_ONLY.csv',tmp/'ml.json')

def test_ml_exploratory_status(res):assert res['status']=='EXPLORATORY_SYNTHETIC_ONLY'

def test_time_holdout(res):assert res['holdout_gap']=='2025-09-01 to 2025-10-01'

def test_temporal_train_and_test(res):assert res['train']>500 and res['test']>200

def test_pr_auc_bounded(res):assert 0<=res['average_precision']<=1

def test_roc_auc_bounded(res):assert 0<=res['roc_auc']<=1

def test_precision_bounded(res):assert 0<=res['precision_at_capacity']<=1

def test_recall_bounded(res):assert 0<=res['recall_at_capacity']<=1

def test_capacity_nonzero(res):assert res['review_count']>0

def test_score_not_decision(res):assert res['fraud_or_payment_authority']=='NONE'

def test_exclude_label_as_feature(res):assert 'chargeback_outcome' in res['excluded_features']

def test_unmatured_labels_excluded_when_early(sample,tmp_path):
    inp,out,_=sample
    r=evaluate(out/'candidate_transactions.csv',inp/'outcomes_SYNTHETIC_EVALUATION_ONLY.csv',tmp_path/'early.json',asof='2025-01-05T00:00:00Z')
    assert r['status'].startswith('BLOCKED')

def test_legacy_truth_not_merged(sample):
    _,out,_=sample; row=read_csv(out/'candidate_transactions.csv')[0]
    assert 'decision' not in row and len(feature(row))==6
