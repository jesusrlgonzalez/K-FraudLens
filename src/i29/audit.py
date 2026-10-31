"""Immutable-input quality audit; never permits payment or anti-fraud action."""
import csv
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from .fixtures import write_csv,FIELDS

CUTOFF=datetime(2026,6,30,tzinfo=timezone.utc)
CCY={'MXN','USD','EUR'}
COUNTRIES={'MX','US','DE'}
CHANNELS={'web','mobile','pos'}
CANDIDATE_FIELDS=FIELDS+['amount_decimal','observed_lag_seconds']
ISSUE_FIELDS=['row_index','event_id','transaction_id','severity','rule','explanation']

def utc(value):
    try:
        if not value or not (value.endswith('Z') or re.search(r'[+-]\d{2}:\d{2}$',value)):
            return None
        x=datetime.fromisoformat(value.replace('Z','+00:00'))
        return x.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None

def read_csv(path):
    with open(path,encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def validate_id(token):
    # Deliberately accept only pretokenized synthetic tokens. No PAN display in outputs.
    return bool(re.fullmatch(r'acct_\d{4}',token or ''))

def audit(transactions, merchants, output):
    """Return result summary and write separate decision files. No fraud labels loaded."""
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    rows=read_csv(transactions); mer=read_csv(merchants)
    merchant_map={x['merchant_id']:x for x in mer}
    counts=Counter(x.get('transaction_id','') for x in rows if x.get('transaction_id'))
    accepted=[];review=[];quarantine=[];issues=[];counts_reason=Counter()
    for i,r in enumerate(rows):
        row=dict(r)
        sid=r.get('event_id','')
        reasons=[]
        def mark(severity,rule,msg):
            reasons.append((severity,rule,msg));counts_reason[rule]+=1
            issues.append({'row_index':str(i),'event_id':sid,'transaction_id':r.get('transaction_id',''),
                           'severity':severity,'rule':rule,'explanation':msg})
        if not re.fullmatch(r'ev_\d{6}',sid): mark('QUARANTINE','BAD_EVENT_ID','Event identifier missing or malformed')
        txn=r.get('transaction_id','')
        if not re.fullmatch(r'tx_\d{6}',txn): mark('QUARANTINE','BAD_TRANSACTION_ID','Invalid transaction identifier')
        if counts[txn]>1: mark('QUARANTINE','DUPLICATE_TRANSACTION_ID','Transaction identifier collision; no automatic merge')
        ev=utc(r.get('event_at',''));obs=utc(r.get('observed_at',''))
        if ev is None: mark('QUARANTINE','INVALID_EVENT_TIME','Event time not a UTC-capable ISO8601 instant')
        if obs is None: mark('QUARANTINE','INVALID_OBSERVED_TIME','Observation time not a UTC-capable ISO8601 instant')
        lag=''
        if ev and ev>CUTOFF: mark('QUARANTINE','EVENT_IN_FUTURE','Event later than frozen audit cutoff')
        if obs and obs>CUTOFF: mark('QUARANTINE','OBSERVED_IN_FUTURE','Observation later than frozen audit cutoff')
        if ev and obs:
            delta=int((obs-ev).total_seconds());lag=str(delta)
            if delta < -120: mark('REVIEW','CLOCK_SKEW','Observed timestamp predates event; cannot silently reorder')
            if delta>86400: mark('REVIEW','LATE_ARRIVAL','Late message; event-time ordering retained')
        amount=None
        try:
            amount=Decimal(r.get('amount',''))
            if not amount.is_finite() or amount<=0: raise InvalidOperation('not positive finite amount')
            if amount.as_tuple().exponent < -2: mark('REVIEW','EXCESS_PRECISION','More than two decimal places')
        except (InvalidOperation, ValueError):
            mark('QUARANTINE','INVALID_AMOUNT','Nonpositive, missing or nonfinite monetary amount')
        if r.get('currency') not in CCY: mark('QUARANTINE','UNKNOWN_CURRENCY','Currency not authorized; no FX implied')
        if r.get('merchant_id') not in merchant_map: mark('QUARANTINE','UNREGISTERED_MERCHANT','Merchant missing in frozen reference')
        if r.get('channel') not in CHANNELS: mark('QUARANTINE','UNKNOWN_CHANNEL','Invalid channel')
        if r.get('event_type')!='AUTHORIZATION': mark('QUARANTINE','UNSUPPORTED_EVENT','Only authorization attempts in this demo')
        if not validate_id(r.get('account_token')): mark('QUARANTINE','UNSAFE_ACCOUNT_IDENTIFIER','Token invalid or resembles raw card data; content withheld')
        if not re.fullmatch(r'dev_\d{4}',r.get('device_token','')): mark('REVIEW','MISSING_DEVICE','Device not available or invalid')
        if r.get('customer_country') not in COUNTRIES: mark('REVIEW','UNKNOWN_CUSTOMER_COUNTRY','Country invalid or missing')
        if r.get('merchant_country') not in COUNTRIES: mark('REVIEW','UNKNOWN_MERCHANT_COUNTRY','Country invalid or missing')
        m=merchant_map.get(r.get('merchant_id'))
        if m and r.get('merchant_country')!=m['country']:
            mark('REVIEW','MERCHANT_REFERENCE_MISMATCH','Country differs from frozen merchant catalog')
        # Data minimization: never echo an unsafe account or original dirty row to shared outputs.
        if not validate_id(row.get('account_token')): row['account_token']='[REDACTED]'
        row['amount_decimal']=str(amount) if amount is not None and amount.is_finite() and amount>0 else ''
        row['observed_lag_seconds']=lag
        status='QUARANTINE' if any(z[0]=='QUARANTINE' for z in reasons) else 'REVIEW' if reasons else 'CANDIDATE'
        row['quality_decision']=status
        if status=='QUARANTINE': quarantine.append(row)
        elif status=='REVIEW': review.append(row)
        else: accepted.append(row)
    decision_fields=CANDIDATE_FIELDS+['quality_decision']
    write_csv(output/'candidate_transactions.csv',decision_fields,accepted)
    write_csv(output/'review_transactions.csv',decision_fields,review)
    write_csv(output/'quarantine_transactions.csv',decision_fields,quarantine)
    write_csv(output/'audit_issues.csv',ISSUE_FIELDS,issues)
    summary={'source_type':'SYNTHETIC_DEMO', 'dataset':'dirty_transaction_events',
             'input_rows':len(rows),'candidate_rows':len(accepted),'review_rows':len(review),
             'quarantine_rows':len(quarantine),'conservation_check':len(rows)==len(accepted)+len(review)+len(quarantine),
             'rule_hit_counts':dict(sorted(counts_reason.items())),
             'no_payment_authority':True,'fraud_decisions':'NONE',
             'quality_decision_is_not_a_fraud_verdict':True, 'outcome_labels_accessed_by_audit':False}
    (output/'quality_report.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
    return summary

def populate_sqlite(output):
    """Local read-only presentation datastore built from sanitized output."""
    out=Path(output); db=out/'quality_evidence.sqlite'; db.unlink(missing_ok=True)
    cn=sqlite3.connect(db)
    cn.executescript('''CREATE TABLE decisions (event_id TEXT NOT NULL, transaction_id TEXT, merchant_id TEXT, event_at TEXT, amount TEXT, currency TEXT, quality_decision TEXT NOT NULL); CREATE INDEX idx_quality ON decisions(quality_decision); CREATE TABLE issues (event_id TEXT, rule TEXT, severity TEXT);''')
    for status,file in [('CANDIDATE','candidate_transactions.csv'),('REVIEW','review_transactions.csv'),('QUARANTINE','quarantine_transactions.csv')]:
        rows=read_csv(out/file)
        cn.executemany('INSERT INTO decisions VALUES (?,?,?,?,?,?,?)',[(r['event_id'],r['transaction_id'],r['merchant_id'],r['event_at'],r['amount'],r['currency'],status) for r in rows])
    cn.executemany('INSERT INTO issues VALUES (?,?,?)',[(r['event_id'],r['rule'],r['severity']) for r in read_csv(out/'audit_issues.csv')])
    cn.commit();cn.close()
    return db
