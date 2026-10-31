"""Public-source admission checks only. Neither real source fits the synthetic merchant/event contract."""
class SchemaAdmissionError(ValueError):
    pass

def inspect_ulb_columns(columns):
    fields=set(columns)
    expected={'Time','Amount','Class'}|{f'V{i}' for i in range(1,29)}
    missing=expected-fields
    if missing: raise SchemaAdmissionError(f'ULB fields missing: {sorted(missing)}')
    return {'dataset':'ULB_CC_2013','status':'RESEARCH_ONLY_SEPARATE_EXPERIMENT',
            'contains_merchant_ids':False,'contains_event_absolute_utc':False,
            'needs_new_approved_protocol':True,'do_not_auto_join_i29_fixture':True}

def inspect_ieee_transaction_columns(columns):
    fields=set(columns)
    expected={'TransactionID','TransactionDT','TransactionAmt','isFraud'}
    missing=expected-fields
    if missing:raise SchemaAdmissionError(f'IEEE-CIS train columns missing: {sorted(missing)}')
    return {'dataset':'IEEE_CIS_TRAIN','status':'COMPETITION_RULES_AND_SCHEMA_REVIEW_REQUIRED',
            'has_relative_not_absolute_datetime':True,'identity_table_optional':True,
            'needs_new_approved_protocol':True,'do_not_auto_join_i29_fixture':True}
