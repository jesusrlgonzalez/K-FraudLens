from fastapi.testclient import TestClient
from i29.api import app
from i29.gates import gate_status

client=TestClient(app)

def test_health_readonly():
    r=client.get('/health');assert r.status_code==200 and r.json()['read_only']

def test_no_payment_routes():
    routes={r.path for r in app.routes}
    assert not any('pay' in r or 'block' in r or 'chargeback' in r for r in routes)

def test_post_not_accepted():assert client.post('/health').status_code==405

def test_g1_without_approval_blocked():assert gate_status({'source_admitted':True,'independent_reviewer':False})=='BLOCK'

def test_g1_missing_real_source_blocked():assert gate_status({'source_admitted':False,'independent_reviewer':True})=='BLOCK'

def test_g1_without_evidence_blocked():assert gate_status({'source_admitted':True,'independent_reviewer':True})=='BLOCK'

def test_g1_all_simulated_not_verified():
    assert gate_status({'source_admitted':True,'independent_reviewer':True,'evidence_sha256':'a'*64})=='PENDING_EXTERNAL_VERIFICATION'
