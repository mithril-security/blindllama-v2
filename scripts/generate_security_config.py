#!/usr/bin/env python3
import json
from pathlib import Path

application_disk_build_info = json.loads(Path("local/application_disk_info.json").read_text())
application_disk_roothash = application_disk_build_info[0]['roothash']
with open("client/client/blindllamav2/security_config/application.json", 'w') as json_file:
    json.dump({"application_disk_roothash": application_disk_roothash}, json_file, indent=4)