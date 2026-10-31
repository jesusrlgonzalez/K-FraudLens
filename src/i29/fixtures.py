"""Deterministic SYNTHETIC dirty payments fixture. No real customers, PAN, CVV, or sanctioned entities."""
import csv
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone

SEED = 29029
FIELDS = ['event_id','transaction_id','event_at','observed_at','merchant_id','account_token','device_token','amount','currency','merchant_country','customer_country','channel','event_type']
MERCHANT_FIELDS = ['merchant_id','country','onboarded_at','merchant_category']
OUTCOME_FIELDS = ['transaction_id','decision','decided_at','reason']
DEFECT_FIELDS = ['row_index','event_id','defect','expected_handling']

def write_csv(path, fields, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fields, lineterminator='\n'); w.writeheader(); w.writerows(rows)

def iso(t):
    return t.isoformat(timespec='seconds').replace('+00:00','Z')

def generate(root, n=3200):
    root=Path(root); root.mkdir(parents=True,exist_ok=True)
    rng=random.Random(SEED)
    base=datetime(2025,1,1,tzinfo=timezone.utc)
    countries=['MX','US','DE']
    merchants=[{'merchant_id':f'mer_{i:03d}','country':countries[i%3], 'onboarded_at':iso(base-timedelta(days=80+i)), 'merchant_category':['retail','travel','digital','grocery'][i%4]} for i in range(64)]
    tx=[]; outcomes=[]
    for i in range(n):
        m=merchants[i%64]
        event_time=base + timedelta(minutes=i*155)
        amount=round(rng.lognormvariate(3.55,0.9),2)
        risky=(i%29==0 or (i%107==0 and amount>80))
        if risky: amount=round(amount*2.7,2)
        device=f'dev_{i%451:04d}'
        token=f'acct_{i%797:04d}'
        row={'event_id':f'ev_{i:06d}','transaction_id':f'tx_{i:06d}', 'event_at':iso(event_time),
             'observed_at':iso(event_time+timedelta(seconds=rng.randint(2,460))),
             'merchant_id':m['merchant_id'],'account_token':token,'device_token':device,'amount':f'{amount:.2f}',
             'currency':['MXN','USD','EUR'][i%3], 'merchant_country':m['country'],
             'customer_country':m['country'] if not risky and i%13!=0 else countries[(i+1)%3],
             'channel':['web','mobile','pos'][i%3], 'event_type':'AUTHORIZATION'}
        tx.append(row)
        delay=(1+(i*13)%37)
        outcomes.append({'transaction_id':row['transaction_id'],'decision':'CONFIRMED_FRAUD' if risky else 'REVIEWED_LEGITIMATE',
                         'decided_at':iso(event_time+timedelta(days=delay)), 'reason':'SIMULATED_ADJUDICATION'})
    # Inject tracked anomalies: preserve row count; some changes affect otherwise clean counterpart rows.
    inject=[
        ('BAD_AMOUNT',lambda x:set_(x,'amount','-42.00'),'QUARANTINE'),
        ('BAD_CURRENCY',lambda x:set_(x,'currency','ZZZ'),'QUARANTINE'),
        ('BAD_TIMESTAMP',lambda x:set_(x,'event_at','not-a-time'),'QUARANTINE'),
        ('UNKNOWN_MERCHANT',lambda x:set_(x,'merchant_id','mer_missing'),'QUARANTINE'),
        ('MISSING_DEVICE',lambda x:set_(x,'device_token',''),'REVIEW'),
        ('EVENT_TIME_FUTURE',lambda x:set_(x,'event_at','2030-01-01T00:00:00Z'),'QUARANTINE'),
        ('OBSERVER_CLOCK_SKEW',lambda x:set_(x,'observed_at','2024-01-01T00:00:00Z'),'REVIEW'),
        ('BAD_COUNTRY',lambda x:set_(x,'customer_country','N/A'),'REVIEW'),
        ('UNKNOWN_CHANNEL',lambda x:set_(x,'channel','satellite'),'QUARANTINE'),
        ('UNKNOWN_EVENT_TYPE',lambda x:set_(x,'event_type','SETTLED'),'QUARANTINE'),
        ('PAN_LIKE_DATA',lambda x:set_(x,'account_token','4111111111111111'),'QUARANTINE'),
        ('DUPLICATE_TRANSACTION',lambda x:set_(x,'transaction_id','tx_000000'),'QUARANTINE'),
    ]
    defects=[]
    for j in range(144):
        idx=32+j*19 # less than 3200
        defect,change,handling=inject[j%len(inject)]
        change(tx[idx])
        defects.append({'row_index':str(idx),'event_id':tx[idx]['event_id'],'defect':defect,'expected_handling':handling})
    write_csv(root/'transactions_dirty_SYNTHETIC.csv',FIELDS,tx)
    write_csv(root/'merchant_reference_SYNTHETIC.csv',MERCHANT_FIELDS,merchants)
    write_csv(root/'outcomes_SYNTHETIC_EVALUATION_ONLY.csv',OUTCOME_FIELDS,outcomes)
    write_csv(root/'defect_injection_manifest_SYNTHETIC.csv',DEFECT_FIELDS,defects)
    (root/'SYNTHETIC_ONLY_NOTICE.md').write_text('# Datos ficticios de prueba\n\nTODOS los registros se generaron para I29. No representan cuentas ni transacciones reales. Los targets de fraude se fabricaron mediante una regla; sus resultados ML no son extrapolables. No se almacenan PAN, CVV, nombres ni credenciales reales.\n',encoding='utf-8')
    return {'transactions':len(tx),'merchants':len(merchants),'outcomes':len(outcomes),'defects':len(defects)}

def set_(row,key,value):
    row[key]=value

if __name__=='__main__':
    import sys
    print(generate(sys.argv[1] if len(sys.argv)>1 else 'DATOS_FUENTES/04_SINTETICOS'))
