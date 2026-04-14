import sys
sys.path.append('scripts/sbcli-repo')

import json
from simplyblock_web.app import app
with open('docs/reference/api/openapi.json', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
print('Generated openapi.json')