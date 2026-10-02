"""Read-only integrity check and in-memory tampering demonstration."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from policy import verify_events

parser=argparse.ArgumentParser()
parser.add_argument('database',nargs='?',default='instance/ortak.sqlite')
parser.add_argument('--demo-tamper',action='store_true')
args=parser.parse_args()
with sqlite3.connect(f'file:{args.database}?mode=ro',uri=True) as conn:
    conn.row_factory=sqlite3.Row
    rows=[dict(r) for r in conn.execute('SELECT * FROM events ORDER BY id')]
print('Orijinal zincir:',verify_events(rows))
if args.demo_tamper and rows:
    rows[len(rows)//2]['object_id']+=1
    print('Bellekte bozulan kopya:',verify_events(rows))
