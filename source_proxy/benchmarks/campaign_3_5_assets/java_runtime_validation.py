"""Compile and execute private Java reference probes."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from source_proxy.benchmarks.campaign_3_5_assets.fixture_catalog import materialize_implemented_fixture
from source_proxy.benchmarks.campaign_3_5_assets.seeding import Campaign35RunSeed, derive_task_seed, task_seed_commitment


JAVA_RUNTIME_TASKS=frozenset({"S07","S16","S23","B11","M03","M11"})

def _replace(path:Path,before:str,after:str)->None:
    text=path.read_text(encoding="utf-8")
    if before not in text: raise ValueError("campaign_3_5_java_reference_baseline_mismatch")
    path.write_text(text.replace(before,after),encoding="utf-8")

def apply_java_runtime_reference(task_id:str,root:Path)->None:
    path=root/"src/main/java/app"/("CsvParser.java" if task_id=="S07" else "ConfigLoader.java" if task_id=="S16" else "WidgetAdvice.java" if task_id=="S23" else "EtagFilter.java" if task_id=="B11" else "Profile.java" if task_id=="M03" else "WebhookSigner.java")
    if task_id=="S07": _replace(path,"if(value.isEmpty()) throw new IllegalArgumentException(\"header\"); return 1;","if(value.isEmpty()) return 0; if(!value.startsWith(\"name,\")) throw new IllegalArgumentException(\"header\"); return 1;")
    elif task_id=="S16":
        _replace(path,"throw new ConfigLoadException(\"failed\");","throw new ConfigLoadException(\"failed\", e);")
        _replace(path,"ConfigLoadException(String m){super(m);}","ConfigLoadException(String m, Throwable cause){super(m,cause);}")
    elif task_id=="S23":
        _replace(path,"return 500;","return e.getClass().getSimpleName().equals(\"WidgetNotFoundException\") ? 404 : 500;")
        (path.parent / "WidgetNotFoundException.java").write_text("package app; class WidgetNotFoundException extends RuntimeException {}\n", encoding="utf-8")
    elif task_id=="M11": path.write_text("package app; import java.util.*; class WebhookSigner { String signV1(String payload,String secret){return Integer.toHexString((payload+secret).hashCode());} boolean verifyV2(String payload,long timestamp,String secret,long now,Set<String> seen){String key=timestamp+\":\"+payload;if(Math.abs(now-timestamp)>300||seen.contains(key))return false;seen.add(key);return signV1(timestamp+\".\"+payload,secret).length()>0;} }\n",encoding="utf-8")
    elif task_id=="B11": path.write_text("package app; class EtagFilter { String etag(byte[] canonicalBytes){return Integer.toHexString(java.util.Arrays.hashCode(canonicalBytes));} String etagForResponse(byte[] canonicalBytes, boolean gzip){return etag(canonicalBytes);} }\n",encoding="utf-8")
    elif task_id=="M03": path.write_text("package app; class Profile { String name; long version; Profile(String n,long v){name=n;version=v;} boolean update(String next,long ifMatch){if(version!=ifMatch)return false;name=next;version++;return true;} }\n",encoding="utf-8")

def _run(root:Path,source:str,harness:str)->bool:
    with tempfile.TemporaryDirectory(prefix="campaign35-java-output-") as temporary:
        output=Path(temporary); harness_path=root/"src/main/java/app/Probe.java"; harness_path.write_text("package app; public class Probe { public static void main(String[] a) { "+harness+" } }",encoding="utf-8")
        source_dir = root / "src/main/java/app"
        result=subprocess.run(["javac","-d",str(output),*[str(path) for path in source_dir.glob("*.java")]],capture_output=True,text=True)
        if result.returncode: return False
        return subprocess.run(["java","-cp",str(output),"app.Probe"],capture_output=True,text=True).returncode==0

def probe_java_runtime(task_id:str,root:Path)->tuple[bool,str]:
    if task_id=="S07": return _run(root,"CsvParser.java","if(new CsvParser().parse(\"\")!=0) System.exit(1); try { new CsvParser().parse(\"bad\"); System.exit(1); } catch(IllegalArgumentException ok) {}"),"empty_csv"
    if task_id=="S16": return _run(root,"ConfigLoader.java","try { new ConfigLoader().load(); System.exit(1); } catch(ConfigLoadException e) { if(e.getCause()==null || !\"failed\".equals(e.getMessage())) System.exit(1); }"),"preserved_io_cause"
    if task_id=="S23": return _run(root,"WidgetAdvice.java","if(new WidgetAdvice().status(new WidgetNotFoundException())!=404 || new WidgetAdvice().status(new RuntimeException())!=500) System.exit(1);"),"not_found_envelope_status"
    if task_id=="M11": return _run(root,"WebhookSigner.java","WebhookSigner s=new WebhookSigner(); java.util.Set<String> seen=new java.util.HashSet<>(); if(!s.verifyV2(\"p\",1000,\"k\",1001,seen)||s.verifyV2(\"p\",1000,\"k\",1001,seen)||s.verifyV2(\"p\",1000,\"k\",1400,new java.util.HashSet<>()))System.exit(1);"),"versioned_webhook_replay_protection"
    if task_id=="B11": return _run(root,"EtagFilter.java","EtagFilter f=new EtagFilter(); if(!f.etagForResponse(new byte[]{1},false).equals(f.etagForResponse(new byte[]{1},true)))System.exit(1);"),"canonical_response_etag"
    return _run(root,"Profile.java","Profile p=new Profile(\"a\",1); if(!p.update(\"b\",1)||p.update(\"c\",1)||p.version!=2)System.exit(1);"),"optimistic_concurrency"

def validate_java_runtime_references(tasks:list[dict[str,Any]])->dict[str,Any]:
    by_id={task["task_id"]:task for task in tasks};records=[];seed=Campaign35RunSeed(raw=b"campaign35-java-runtime".ljust(32,b"0"),commitment="java-runtime")
    with tempfile.TemporaryDirectory(prefix="campaign35-java-runtime-") as temporary:
        for index,task_id in enumerate(sorted(JAVA_RUNTIME_TASKS)):
            task=by_id[task_id];parent=Path(temporary)/str(index);parent.mkdir();local=derive_task_seed(seed,task_id,task["fixture"]);fixture=materialize_implemented_fixture(parent,task,task_seed=local,task_seed_commitment=task_seed_commitment(local));apply_java_runtime_reference(task_id,fixture.fixture_root);passed,category=probe_java_runtime(task_id,fixture.fixture_root);records.append({"task_id":task_id,"passed":passed,"category":category})
    return {"schema_version":"campaign-3.5-java-runtime-validation/v1","passed":all(row["passed"] for row in records),"task_count":len(records),"tasks":records,"validated_task_ids":[row["task_id"] for row in records if row["passed"]]}
