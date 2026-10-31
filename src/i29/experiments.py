"""Exploratory time-split benchmark. NOT calibrated, validated or authorized to block payments."""
import json
from pathlib import Path
from datetime import timedelta
from math import log1p
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score,roc_auc_score
from .audit import read_csv, utc

def feature(r):
    t=utc(r['event_at']); amount=float(r['amount_decimal'])
    return [log1p(amount),t.hour/24., int(t.weekday()>=5), int(r['customer_country']!=r['merchant_country']),int(r['channel']=='web'),int(r['channel']=='pos')]

def evaluate(candidate_csv,outcome_csv,output,asof='2026-06-01T00:00:00Z'):
    cutoff=utc(asof)
    events=read_csv(candidate_csv); outcomes=read_csv(outcome_csv)
    label_map={r['transaction_id']:r for r in outcomes}
    train=[];test=[]; excluded_unmatured=0
    for r in events:
        t=utc(r['event_at']); lab=label_map.get(r['transaction_id'])
        if not t or not lab: continue
        decision=utc(lab['decided_at'])
        if not decision or decision>cutoff:
            excluded_unmatured+=1;continue
        if lab['decision'] not in ('CONFIRMED_FRAUD','REVIEWED_LEGITIMATE'): continue
        instance=(feature(r),int(lab['decision']=='CONFIRMED_FRAUD'))
        if t<utc('2025-09-01T00:00:00Z'): train.append(instance)
        elif t>=utc('2025-10-01T00:00:00Z') and t<utc('2026-01-01T00:00:00Z'):test.append(instance)
    x_train=np.array([e[0] for e in train]);y_train=np.array([e[1] for e in train]);x_test=np.array([e[0] for e in test]);y_test=np.array([e[1] for e in test])
    if len(train)<100 or len(test)<100 or len(set(y_train))<2 or len(set(y_test))<2:
        return {'status':'BLOCKED_INSUFFICIENT_CLASSES_OR_TEMPORAL_HOLDOUT','train':len(train),'test':len(test)}
    model=make_pipeline(StandardScaler(),LogisticRegression(class_weight='balanced',max_iter=400,random_state=29))
    model.fit(x_train,y_train)
    p=model.predict_proba(x_test)[:,1]
    budget=max(1,int(len(p)*0.03)); order=np.argsort(-p,kind='stable')[:budget]
    tp=int(y_test[order].sum()); precision=float(tp/budget); recall=float(tp/y_test.sum())
    base=float(np.mean(y_test))
    result={'status':'EXPLORATORY_SYNTHETIC_ONLY','synthetic_positive_generation':'DELIBERATELY_STRUCTURED',
            'train':len(train),'test':len(test),'train_frauds':int(y_train.sum()),'test_frauds':int(y_test.sum()),
            'test_prevalence':base,'average_precision':float(average_precision_score(y_test,p)),
            'roc_auc':float(roc_auc_score(y_test,p)), 'review_capacity_ratio':0.03,'review_count':budget,
            'true_synthetic_positive_in_review':tp,'precision_at_capacity':precision,'recall_at_capacity':recall,
            'mature_label_asof':asof,'unmatured_labels_excluded':excluded_unmatured,
            'prediction_features':['amount','UTC_hour','weekend','cross_border','channel'],
            'excluded_features':['chargeback_outcome','decided_at','device_post_event','merchant_future_statistics'],
            'fraud_or_payment_authority':'NONE', 'holdout_gap':'2025-09-01 to 2025-10-01'}
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    return result
