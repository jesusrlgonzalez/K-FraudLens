"""Aggregated bipartite graph: exploratory entity co-occurrence, never fraud accusation."""
import json
from pathlib import Path
from collections import Counter
import networkx as nx
from .audit import read_csv

def run(candidate_csv,output):
    g=nx.Graph()
    rows=read_csv(candidate_csv)
    device_accounts={};device_merchants={}
    for r in rows:
        account='acct:'+r['account_token'];device='dev:'+r['device_token'];merchant='mer:'+r['merchant_id']
        g.add_edge(account,device)
        g.add_edge(account,merchant)
        device_accounts.setdefault(device,set()).add(account)
        device_merchants.setdefault(device,set()).add(merchant)
    # Explanatory graph only. Shared device / merchant connectivity is NOT proof of wrongdoing.
    shared=sum(len(accounts)>=3 for accounts in device_accounts.values())
    clusters=[len(comp) for comp in nx.connected_components(g)]
    result={'status':'EXPLORATORY_SYNTHETIC_ONLY', 'source_rows':len(rows),
            'nodes':int(g.number_of_nodes()), 'edges':int(g.number_of_edges()),
            'connected_components':len(clusters), 'largest_component_nodes':max(clusters,default=0),
            'devices_linking_three_or_more_accounts':shared,
            'identification_of_fraud_by_graph':'NONE',
            'graph_features_used_in_ml':False,
            'note':'Shared devices and large connected components are not evidence of fraud; no personal identities exist.'}
    p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return result
