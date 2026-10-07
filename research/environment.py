"""Record installed runtime and source provenance without credentials."""
import hashlib
import argparse
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--final',action='store_true')
    args=parser.parse_args()
    out = Path('artifacts/environment')
    out.mkdir(parents=True,exist_ok=True)
    versions = {distribution.metadata['Name']:distribution.version for distribution in importlib.metadata.distributions()}
    hashes = {str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in Path('research').glob('*.py')}
    manifest = {'recorded_at':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
                'platform':platform.platform(),'packages':dict(sorted(versions.items())),
                'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                'source_sha256':hashes,'note':'Includes installed versions and code hashes; no connection URLs or credentials.'}
    (out/('runtime_final.json' if args.final else 'runtime.json')).write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f"Runtime saved: Python {manifest['python']}, {len(versions)} distributions")


if __name__=='__main__': main()
