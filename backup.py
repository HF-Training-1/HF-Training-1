"""Offline full data backup. Stop the app first so database and uploads stay consistent."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import zipfile

p=argparse.ArgumentParser()
p.add_argument('destination',type=Path)
p.add_argument('--app-stopped',action='store_true',help='Confirm the application is stopped')
a=p.parse_args()
if not a.app_stopped:
    raise SystemExit('Stop the app, then add --app-stopped. This is required for a consistent files/database backup.')
root=Path(os.environ.get('HF_DATA_DIR',str(Path(__file__).parent/'instance'))).resolve()
if not (root/'hf.sqlite3').exists():
    raise SystemExit('No database found in HF_DATA_DIR.')
if a.destination.exists() or a.destination.resolve().is_relative_to(root):
    raise SystemExit('Choose a new backup path outside the data directory.')
with tempfile.TemporaryDirectory() as t:
    copy=Path(t)/'hf.sqlite3'
    with sqlite3.connect(root/'hf.sqlite3') as source,sqlite3.connect(copy) as target:
        source.backup(target)
        result=target.execute('PRAGMA integrity_check').fetchone()[0]
        if result!='ok':
            raise SystemExit('Database integrity check failed.')
    manifest={}
    with zipfile.ZipFile(a.destination,'x',zipfile.ZIP_DEFLATED) as z:
        for source,name in [(copy,'hf.sqlite3')]+[(x,str(x.relative_to(root))) for x in (root/'uploads').glob('*') if x.is_file()]:
            z.write(source,name)
            manifest[name]=hashlib.sha256(source.read_bytes()).hexdigest()
        z.writestr('manifest.json',json.dumps(manifest,indent=2))
print('Backup created. It contains private records; store securely outside GitHub. See restore instructions.')
