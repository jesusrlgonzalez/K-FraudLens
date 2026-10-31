"""Fail closed: caller claims never authorize approval without verified independent evidence."""
def gate_status(claim):
    if not (claim.get('source_admitted') and claim.get('independent_reviewer') and claim.get('evidence_sha256')):
        return 'BLOCK'
    return 'PENDING_EXTERNAL_VERIFICATION'
