"""Extract five-second windows; never average window percentiles into a session p99."""
from pathlib import Path
import argparse,re,csv,sys
p=argparse.ArgumentParser();p.add_argument('log',type=Path);args=p.parse_args()
rows=[]
for line in args.log.read_text(errors='replace').splitlines():
    if 'WOW_METRICS intervals=' in line:
        rows.append(dict(re.findall(r'(\w+)=([0-9.eE+-]+)',line)))
if not rows:raise SystemExit('No WOW_METRICS windows found')
writer=csv.DictWriter(sys.stdout,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(f'# windows={len(rows)}; per-window percentiles only; includes loading/menu windows if present',file=sys.stderr)
