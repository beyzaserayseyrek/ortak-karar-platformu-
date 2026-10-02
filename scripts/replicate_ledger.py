"""Two local file replicas: teaching demo, not distributed consensus."""
import json
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from policy import verify_events

source=Path(sys.argv[1] if len(sys.argv)>1 else 'instance/ortak.sqlite')
conn=sqlite3.connect(f'file:{source}?mode=ro',uri=True)
conn.row_factory=sqlite3.Row
rows=[dict(r) for r in conn.execute('SELECT * FROM events ORDER BY id')]
conn.close()
if not verify_events(rows)[0]: raise SystemExit('Kaynak zincir bozuk; çoğaltılmadı.')
for name in ('node-a','node-b'):
    path=Path('instance')/name/'ledger.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    print(name,verify_events(json.loads(path.read_text())), 'olay:',len(rows))
print('Tek kaynaktan iki yerel kopya. Ağ protokolü, bağımsız düğüm veya mutabakat yoktur.')
