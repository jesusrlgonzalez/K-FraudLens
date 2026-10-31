import pytest
from i29.fixtures import generate
from i29.audit import audit

@pytest.fixture(scope='session')
def sample(tmp_path_factory):
    root=tmp_path_factory.mktemp('i29fixture')
    inp=root/'synth'; out=root/'audited'
    generate(inp)
    summary=audit(inp/'transactions_dirty_SYNTHETIC.csv',inp/'merchant_reference_SYNTHETIC.csv',out)
    return inp,out,summary
