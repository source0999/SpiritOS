"""Execute private Rust reference probes with the campaign-owned toolchain."""
from __future__ import annotations

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Any

from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import materialize_implemented_fixture
from source_proxy.benchmarks.campaign_3_5_assets.core_references import apply_core_reference
from source_proxy.benchmarks.campaign_3_5_assets.seeding import Campaign35RunSeed, derive_task_seed, task_seed_commitment

CARGO=Path('/home/source/.campaign-3-5-tools/cargo/bin/cargo')
RUST_ENV={**os.environ,'CARGO_HOME':'/home/source/.campaign-3-5-tools/cargo','RUSTUP_HOME':'/home/source/.campaign-3-5-tools/rustup','RUSTUP_TOOLCHAIN':'stable'}
RUST_RUNTIME_TASKS=frozenset({'S06','S21','B06','M08'})

def _replace(path:Path,before:str,after:str)->None:
 text=path.read_text(encoding='utf-8')
 if before not in text: raise ValueError('campaign_3_5_rust_reference_baseline_mismatch')
 path.write_text(text.replace(before,after),encoding='utf-8')

def apply_rust_runtime_reference(task_id:str,root:Path)->None:
 if task_id=='S06': _replace(root/'src/collections.rs','pub fn dedupe_preserving_order(values: Vec<String>) -> Vec<String> { let mut copy=values; copy.sort(); copy.dedup(); copy }','pub fn dedupe_preserving_order(values: Vec<String>) -> Vec<String> { let mut seen=std::collections::HashSet::new(); values.into_iter().filter(|value| seen.insert(value.clone())).collect() }')
 elif task_id=='B06': _replace(root/'src/decode.rs','pub fn decode(chunk: &[u8]) -> String { String::from_utf8_lossy(chunk).into_owned() } // split UTF-8 baseline','pub fn decode(chunk: &[u8]) -> String { String::from_utf8_lossy(chunk).into_owned() }\npub fn decode_chunks(chunks: Vec<Vec<u8>>) -> String { let bytes: Vec<u8> = chunks.into_iter().flatten().collect(); String::from_utf8(bytes).expect("complete UTF-8 stream") }')
 elif task_id=='S21': apply_core_reference(task_id,root)
 elif task_id=='M08': (root/'crates/indexer/src/main.rs').write_text('use std::path::Path;\nfn resume(checkpoint:&Path, reset:bool)->String { if reset || !checkpoint.exists(){ std::fs::write(checkpoint,"0").unwrap(); } let value=std::fs::read_to_string(checkpoint).unwrap(); std::fs::write(checkpoint,"1").unwrap(); value }\nfn main(){}\n',encoding='utf-8')
 else: raise ValueError('campaign_3_5_rust_runtime_task_unknown')

def _test(root:Path,content:str)->bool:
 test=root/'tests'/'probe.rs';test.parent.mkdir(exist_ok=True);test.write_text(content,encoding='utf-8')
 return subprocess.run([str(CARGO),'test','--offline'],cwd=root,capture_output=True,text=True,env=RUST_ENV).returncode==0

def probe_rust_runtime(task_id:str,root:Path)->tuple[bool,str]:
 if task_id=='S06': return _test(root,'use collections::collections::dedupe_preserving_order; #[test] fn probe(){assert_eq!(dedupe_preserving_order(vec!["b".into(),"a".into(),"b".into(),"é".into()]),vec!["b","a","é"]);}\n'),'order_preserving_dedupe'
 if task_id=='B06': return _test(root,'use streaming::decode::decode_chunks; #[test] fn probe(){assert_eq!(decode_chunks(vec![vec![0xC3],vec![0xA9]]),"é");}\n'),'utf8_chunk_boundaries'
 if task_id=='M08':
  source=root/'crates/indexer/src/main.rs';source.write_text(source.read_text(encoding='utf-8')+'\n#[cfg(test)] mod probe { use super::*; #[test] fn checkpoint(){let p=std::env::temp_dir().join("campaign35-index"); let _=std::fs::remove_file(&p);assert_eq!(resume(&p,false),"0");assert_eq!(resume(&p,false),"1");assert_eq!(resume(&p,true),"0");}}\n',encoding='utf-8')
  return subprocess.run([str(CARGO),'test','--offline'],cwd=root,capture_output=True,text=True,env=RUST_ENV).returncode==0,'resumable_checkpoint'
 source=root/'src/main.rs';source.write_text(source.read_text(encoding='utf-8')+'\n#[cfg(test)] mod probe { use super::*; #[test] fn semver(){ assert_eq!(sort_versions(vec!["1.10.0".into(),"1.2.0".into(),"1.2.0-alpha".into()]), vec!["1.2.0-alpha","1.2.0","1.10.0"]); }}\n',encoding='utf-8')
 return subprocess.run([str(CARGO),'test'],cwd=root,capture_output=True,text=True,env=RUST_ENV).returncode==0,'semantic_version_order'

def validate_rust_runtime_references(tasks:list[dict[str,Any]])->dict[str,Any]:
 if not CARGO.is_file(): raise RuntimeError('campaign_3_5_rust_toolchain_unavailable')
 by_id={task['task_id']:task for task in tasks};records=[];seed=Campaign35RunSeed(raw=b'campaign35-rust-runtime'.ljust(32,b'0'),commitment='rust-runtime')
 with tempfile.TemporaryDirectory(prefix='campaign35-rust-runtime-') as temporary:
  for index,task_id in enumerate(sorted(RUST_RUNTIME_TASKS)):
   task=by_id[task_id];parent=Path(temporary)/str(index);parent.mkdir();local=derive_task_seed(seed,task_id,task['fixture']);fixture=materialize_implemented_fixture(parent,task,task_seed=local,task_seed_commitment=task_seed_commitment(local));apply_rust_runtime_reference(task_id,fixture.fixture_root);passed,category=probe_rust_runtime(task_id,fixture.fixture_root);records.append({'task_id':task_id,'passed':passed,'category':category})
 return {'schema_version':'campaign-3.5-rust-runtime-validation/v1','passed':all(row['passed'] for row in records),'task_count':len(records),'tasks':records,'validated_task_ids':[row['task_id'] for row in records if row['passed']]}
