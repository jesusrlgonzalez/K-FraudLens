"""Read-only summary endpoints. No PII, token, transaction detail or risk decisions."""
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException

app=FastAPI(title='I29 Synthetic Fraud Data Quality Observatory',version='0.1.0')
REPORT=Path('outputs/demo/quality_report.json')

@app.get('/health')
def health(): return {'status':'demo','payment_controls':'DISABLED','read_only':True}

@app.get('/quality/summary')
def summary():
    if not REPORT.exists(): raise HTTPException(status_code=503,detail='Demo not built')
    x=json.loads(REPORT.read_text(encoding='utf-8'))
    return {k:x[k] for k in ('source_type','input_rows','candidate_rows','review_rows','quarantine_rows','conservation_check','no_payment_authority')}
