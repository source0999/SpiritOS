"""Execute private SQL migration references with Python's SQLite driver."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from source_proxy.benchmarks.campaign_3_5_assets.core_references import apply_core_reference
from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import materialize_implemented_fixture
from source_proxy.benchmarks.campaign_3_5_assets.seeding import Campaign35RunSeed, derive_task_seed, task_seed_commitment

SQL_RUNTIME_TASKS=frozenset({'S14','B09'})

def apply_sql_runtime_reference(task_id:str,root:Path)->None:
 if task_id=='S14':
  (root/'migrations/002_middle_name_up.sql').write_text('ALTER TABLE users ADD COLUMN middle_name TEXT;\n',encoding='utf-8')
  (root/'migrations/002_middle_name_down.sql').write_text('-- SQLite compatibility rebuild is required for down migration\n',encoding='utf-8')
  (root/'src/models.py').write_text('class User: middle_name: str | None = None\n',encoding='utf-8')
 elif task_id=='B09': apply_core_reference(task_id,root)
 else: raise ValueError('campaign_3_5_sql_runtime_task_unknown')

def probe_sql_runtime(task_id:str,root:Path)->tuple[bool,str]:
 db=sqlite3.connect(':memory:')
 if task_id=='S14':
  db.executescript((root/'migrations/001_users.sql').read_text());db.executescript((root/'migrations/002_middle_name_up.sql').read_text());columns={row[1] for row in db.execute('pragma table_info(users)')};return 'middle_name' in columns,'nullable_middle_name'
 db.execute('create table users(id integer primary key)');db.execute('insert into users values(1)');db.executescript((root/'migrations/002_add_status.sql').read_text());row=db.execute('select status from users').fetchone();return row==('active',),'populated_migration'

def validate_sql_runtime_references(tasks:list[dict[str,Any]])->dict[str,Any]:
 by_id={task['task_id']:task for task in tasks};records=[];seed=Campaign35RunSeed(raw=b'campaign35-sql-runtime'.ljust(32,b'0'),commitment='sql-runtime')
 with tempfile.TemporaryDirectory(prefix='campaign35-sql-runtime-') as temporary:
  for index,task_id in enumerate(sorted(SQL_RUNTIME_TASKS)):
   task=by_id[task_id];parent=Path(temporary)/str(index);parent.mkdir();local=derive_task_seed(seed,task_id,task['fixture']);fixture=materialize_implemented_fixture(parent,task,task_seed=local,task_seed_commitment=task_seed_commitment(local));apply_sql_runtime_reference(task_id,fixture.fixture_root);passed,category=probe_sql_runtime(task_id,fixture.fixture_root);records.append({'task_id':task_id,'passed':passed,'category':category})
 return {'schema_version':'campaign-3.5-sql-runtime-validation/v1','passed':all(row['passed'] for row in records),'task_count':len(records),'tasks':records,'validated_task_ids':[row['task_id'] for row in records if row['passed']]}
