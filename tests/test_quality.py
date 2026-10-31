import copy
import csv
import json
import hashlib
import pytest
from i29.audit import utc,validate_id,audit,read_csv,populate_sqlite
from i29.fixtures import FIELDS,generate,write_csv
from datetime import timezone

@pytest.mark.parametrize('stamp,valid',[('2025-01-01T00:00:00Z',True),('2025-01-01T00:00:00+02:00',True),('2025-01-01',False),('2025-01-01T00:00:00',False),('bad',False),('',False),('2025-13-01T00:00:00Z',False)])
def test_utc_rules(stamp,valid):assert (utc(stamp)is not None)==valid

def test_offset_conversion():assert utc('2025-01-01T02:00:00+02:00').hour==0

@pytest.mark.parametrize('token,valid',[('acct_0001',True),('acct_9999',True),('4111111111111111',False),('',False),('acct_1',False),('acct_00001',False),('4111-1111',False)])
def test_pseudonym_only(token,valid):assert validate_id(token)==valid

def test_conservation(sample):assert sample[2]['input_rows']==sum(sample[2][x] for x in ['candidate_rows','review_rows','quarantine_rows'])

def test_totals(sample):assert sample[2]['input_rows']==3200 and sample[2]['candidate_rows']>0 and sample[2]['quarantine_rows']>0

def test_quality_not_fraud(sample):
    assert sample[2]['fraud_decisions']=='NONE'
    assert not sample[2]['outcome_labels_accessed_by_audit']

def test_no_truth_column_in_outputs(sample):
    for f in ['candidate_transactions.csv','review_transactions.csv','quarantine_transactions.csv']:
        with open(sample[1]/f,encoding='utf-8') as h:
            header=next(csv.reader(h)); assert 'decision' not in header and 'fraud' not in header and 'decided_at' not in header

def test_labels_separate(sample):assert (sample[0]/'outcomes_SYNTHETIC_EVALUATION_ONLY.csv').exists()

def test_synth_only_ledger(sample):
    manifest=read_csv(sample[0]/'defect_injection_manifest_SYNTHETIC.csv')
    assert len(manifest)==144 and {x['expected_handling'] for x in manifest}=={'REVIEW','QUARANTINE'}

def test_every_injected_issue_flagged(sample):
    defects=read_csv(sample[0]/'defect_injection_manifest_SYNTHETIC.csv')
    flagged={x['event_id'] for f in ('review_transactions.csv','quarantine_transactions.csv') for x in read_csv(sample[1]/f)}
    assert all(x['event_id'] in flagged for x in defects)

def test_no_raw_pan_in_outputs(sample):
    for f in ['candidate_transactions.csv','review_transactions.csv','quarantine_transactions.csv','audit_issues.csv','quality_report.json']:
        text=(sample[1]/f).read_text(encoding='utf-8')
        assert '4111111111111111' not in text

def test_raw_source_immutable(sample):
    path=sample[0]/'transactions_dirty_SYNTHETIC.csv'
    h=hashlib.sha256(path.read_bytes()).hexdigest()
    audit(path,sample[0]/'merchant_reference_SYNTHETIC.csv',sample[1]/'rerun')
    assert h==hashlib.sha256(path.read_bytes()).hexdigest()

def test_issue_count_nonzero(sample):assert len(read_csv(sample[1]/'audit_issues.csv'))>=144

def test_report_parse_json(sample):
    assert json.loads((sample[1]/'quality_report.json').read_text())['conservation_check']

def test_sqlite_local(sample):
    import sqlite3
    db=populate_sqlite(sample[1])
    con=sqlite3.connect(db)
    assert con.execute('SELECT COUNT(*) FROM decisions').fetchone()[0]==3200
    assert con.execute('SELECT COUNT(*) FROM issues').fetchone()[0]>=144
    con.close()

def _change_run(sample,tmp_path,key,value):
    row=read_csv(sample[0]/'transactions_dirty_SYNTHETIC.csv')[2]
    row[key]=value
    write_csv(tmp_path/'events.csv',FIELDS,[row])
    return audit(tmp_path/'events.csv',sample[0]/'merchant_reference_SYNTHETIC.csv',tmp_path/'out')

@pytest.mark.parametrize('key,value,expected',[('amount','-3','QUARANTINE'),('amount','NaN','QUARANTINE'),('amount','0','QUARANTINE'),('event_at','later','QUARANTINE'),('event_at','2030-01-01T00:00:00Z','QUARANTINE'),('merchant_id','none','QUARANTINE'),('currency','BTC','QUARANTINE'),('event_type','SETTLEMENT','QUARANTINE'),('channel','UNK','QUARANTINE'),('account_token','4111111111111111','QUARANTINE'),('device_token','','REVIEW'),('customer_country','N/A','REVIEW'),('observed_at','2024-01-01T00:00:00Z','REVIEW'),('merchant_country','MX','REVIEW')])
def test_adversarial_cases(sample,tmp_path,key,value,expected):
    result=_change_run(sample,tmp_path,key,value)
    assert result['quarantine_rows']==1 if expected=='QUARANTINE' else result['review_rows']==1

def test_no_false_currency_conversion(sample,tmp_path):
    x=_change_run(sample,tmp_path,'currency','CAD')
    assert x['quarantine_rows']==1

def test_sql_no_payment_tables(sample):
    import sqlite3
    con=sqlite3.connect(sample[1]/'quality_evidence.sqlite')
    tables=[x[0] for x in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert tables==['decisions','issues']
    con.close()

def test_no_real_data_claim(sample):assert sample[2]['source_type']=='SYNTHETIC_DEMO'
