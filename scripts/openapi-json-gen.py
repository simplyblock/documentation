import sys
import types
sys.path.append('scripts/sbcli-repo')

# The schema needs sbcli's API importable, not a database. sbcli selects the
# FoundationDB API version at import time (fdb.api_version), which neither the
# PyPI package "fdb" (a Firebird driver) nor the FoundationDB binding without
# its C client provides in this image: a stub stands in for the binding.
_fdb = types.ModuleType('fdb')
_fdb.api_version = lambda *_a, **_k: None
_fdb.open = lambda *_a, **_k: None
_fdb.transactional = lambda f: f
_fdb.FDBError = type('FDBError', (Exception,), {})
_fdb.tuple = types.ModuleType('fdb.tuple')
_fdb.tuple.pack = lambda t: repr(t).encode()
_fdb.tuple.unpack = lambda b: ()
_fdb.tuple.range = lambda t: (b'', b'')
sys.modules['fdb'] = _fdb
sys.modules['fdb.tuple'] = _fdb.tuple

import json
from simplyblock_web.app import app
with open('docs/reference/api/openapi.json', 'w') as f:
    openapi = app.openapi()
    openapi["paths"] = {path: x for path, x in openapi["paths"].items() if path.startswith("/api/v2")}
    json.dump(openapi, f, indent=2)
print('Generated openapi.json')