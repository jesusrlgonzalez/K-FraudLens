"""I29 public CLI: fixture, audit, experiment. No effectful financial operations."""
import argparse
import json
from pathlib import Path
from .fixtures import generate
from .audit import audit,populate_sqlite
from .experiments import evaluate

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('fixture');a.add_argument('--out',default='DATOS_FUENTES/04_SINTETICOS')
    b=sub.add_parser('audit');b.add_argument('--source',default='DATOS_FUENTES/04_SINTETICOS/transactions_dirty_SYNTHETIC.csv');b.add_argument('--merchants',default='DATOS_FUENTES/04_SINTETICOS/merchant_reference_SYNTHETIC.csv');b.add_argument('--out',default='outputs/demo')
    c=sub.add_parser('evaluate');c.add_argument('--source',default='outputs/demo/candidate_transactions.csv');c.add_argument('--outcomes',default='DATOS_FUENTES/04_SINTETICOS/outcomes_SYNTHETIC_EVALUATION_ONLY.csv');c.add_argument('--out',default='outputs/demo/ml_experiment.json')
    args=p.parse_args()
    if args.action=='fixture': result=generate(args.out)
    elif args.action=='audit': result=audit(args.source,args.merchants,args.out);populate_sqlite(args.out)
    else:result=evaluate(args.source,args.outcomes,args.out)
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':main()
