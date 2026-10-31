import pytest
from i29.adapters import inspect_ulb_columns,inspect_ieee_transaction_columns,SchemaAdmissionError

def test_ulb_compatible_schema_still_not_admitted():
    r=inspect_ulb_columns(['Time','Amount','Class']+[f'V{i}' for i in range(1,29)])
    assert r['status']=='RESEARCH_ONLY_SEPARATE_EXPERIMENT' and not r['contains_merchant_ids']

def test_ulb_missing_fields_blocked():
    with pytest.raises(SchemaAdmissionError):inspect_ulb_columns(['Time','Class'])

def test_ieee_relative_time_not_absolute():
    r=inspect_ieee_transaction_columns(['TransactionID','TransactionDT','TransactionAmt','isFraud'])
    assert r['has_relative_not_absolute_datetime'] and r['needs_new_approved_protocol']

def test_ieee_no_training_label_not_auto_admitted():
    with pytest.raises(SchemaAdmissionError):inspect_ieee_transaction_columns(['TransactionID','TransactionDT','TransactionAmt'])
