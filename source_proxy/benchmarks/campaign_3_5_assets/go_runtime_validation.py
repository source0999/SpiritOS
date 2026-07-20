"""Compile and execute private Go reference probes with the pinned toolchain."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import materialize_implemented_fixture
from source_proxy.benchmarks.campaign_3_5_assets.seeding import Campaign35RunSeed, derive_task_seed, task_seed_commitment

GO=Path('/home/source/.campaign-3-5-tools/go/bin/go')
GO_RUNTIME_TASKS=frozenset({'S03','S13','S18','S25','B08','B14'})

def _replace(path:Path,before:str,after:str)->None:
 text=path.read_text(encoding='utf-8')
 if before not in text: raise ValueError('campaign_3_5_go_reference_baseline_mismatch')
 path.write_text(text.replace(before,after),encoding='utf-8')

def apply_go_runtime_reference(task_id:str,root:Path)->None:
 if task_id=='S03': _replace(root/'cmd/report.go','return `{\"z\":1,\"a\":2}`','return `{\"a\":2,\"z\":1}` + "\\n"')
 elif task_id=='S13': _replace(root/'internal/cache/config.go','return time.Duration(ttlMs) } // baseline nanoseconds','return time.Duration(ttlMs) * time.Millisecond }')
 elif task_id=='S18': _replace(root/'cmd/report.go','_,err:=os.ReadDir(dir); return nil,err','entries,err:=os.ReadDir(dir); if os.IsNotExist(err) { return []string{},nil }; if err != nil { return nil,err }; out:=make([]string,len(entries)); for i,e:=range entries { out[i]=e.Name() }; return out,nil')
 elif task_id=='S25': _replace(root/'internal/logging/middleware.go','return map[string]string{} } // loses existing correlation id','if value,ok:=ctx.Value(CorrelationIDKey).(string); ok { return map[string]string{CorrelationIDKey:value} }; return map[string]string{} }')
 elif task_id=='B08': _replace(root/'internal/http/routes.go','return \"/users/{id}\" } // /users/me shadowed','if path==\"/users/me\" { return \"/users/me\" }; return \"/users/{id}\" }')
 elif task_id=='B14': _replace(root/'worker/retry.go','func Retry(err error) bool { return err != nil } // baseline retries permanent validation errors','func Retry(err error) bool { _,permanent:=err.(ValidationError); return err != nil && !permanent }')
 else: raise ValueError('campaign_3_5_go_runtime_task_unknown')

def _test(root:Path,path:Path,content:str)->bool:
 test=path/'probe_test.go'; test.write_text(content,encoding='utf-8')
 return subprocess.run([str(GO),'test','.'],cwd=path,capture_output=True,text=True).returncode==0

def probe_go_runtime(task_id:str,root:Path)->tuple[bool,str]:
 if task_id=='S03': return _test(root,root/'cmd','package main\nimport "testing"\nfunc TestProbe(t *testing.T){if encodeJSON()!="{\\\"a\\\":2,\\\"z\\\":1}\\n"{t.Fatal(encodeJSON())}}\n'),'canonical_json'
 if task_id=='S18': return _test(root,root/'cmd','package main\nimport "testing"\nfunc TestProbe(t *testing.T){x,e:=listConfig("/definitely-missing-campaign35");if e!=nil||len(x)!=0{t.Fatal(x,e)}}\n'),'missing_directory'
 if task_id=='S13': return _test(root,root/'internal/cache','package cache\nimport("testing";"time")\nfunc TestProbe(t *testing.T){if Duration(5)!=5*time.Millisecond{t.Fatal(Duration(5))}}\n'),'milliseconds_ttl'
 if task_id=='S25': return _test(root,root/'internal/logging','package logging\nimport("testing";"context")\nfunc TestProbe(t *testing.T){x:=Complete(context.WithValue(context.Background(),CorrelationIDKey,"x"));if x[CorrelationIDKey]!="x"{t.Fatal(x)}}\n'),'correlation_logging'
 if task_id=='B08': return _test(root,root/'internal/http','package http\nimport "testing"\nfunc TestProbe(t *testing.T){if UserRoute("/users/me")!="/users/me"{t.Fatal(UserRoute("/users/me"))}}\n'),'literal_route_priority'
 if task_id=='B14': return _test(root,root/'worker','package worker\nimport("testing";"errors")\nfunc TestProbe(t *testing.T){if Retry(ValidationError{})||!Retry(errors.New("network")){t.Fatal()}}\n'),'permanent_error_no_retry'
 return False,'unknown'

def validate_go_runtime_references(tasks:list[dict[str,Any]])->dict[str,Any]:
 if not GO.is_file(): raise RuntimeError('campaign_3_5_go_toolchain_unavailable')
 by_id={task['task_id']:task for task in tasks};records=[];seed=Campaign35RunSeed(raw=b'campaign35-go-runtime'.ljust(32,b'0'),commitment='go-runtime')
 with tempfile.TemporaryDirectory(prefix='campaign35-go-runtime-') as temporary:
  for index,task_id in enumerate(sorted(GO_RUNTIME_TASKS)):
   task=by_id[task_id];parent=Path(temporary)/str(index);parent.mkdir();local=derive_task_seed(seed,task_id,task['fixture']);fixture=materialize_implemented_fixture(parent,task,task_seed=local,task_seed_commitment=task_seed_commitment(local));apply_go_runtime_reference(task_id,fixture.fixture_root);passed,category=probe_go_runtime(task_id,fixture.fixture_root);records.append({'task_id':task_id,'passed':passed,'category':category})
 return {'schema_version':'campaign-3.5-go-runtime-validation/v1','passed':all(row['passed'] for row in records),'task_count':len(records),'tasks':records,'validated_task_ids':[row['task_id'] for row in records if row['passed']]}
