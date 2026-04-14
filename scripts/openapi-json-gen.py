import sys
sys.path.append('scripts/sbcli-repo')

import json
from simplyblock_web.app import app
with open('docs/reference/api/openapi.json', 'w') as f:
    openapi = app.openapi()
    openapi["paths"] = {path: x for path, x in openapi["paths"].items() if path.startswith("/api/v2")}
    json.dump(openapi, f, indent=2)
print('Generated openapi.json')