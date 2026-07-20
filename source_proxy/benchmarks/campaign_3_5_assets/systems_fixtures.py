"""Go, Rust, Java, and SQL fixture families with task-specific baseline bugs."""
from __future__ import annotations

import hashlib
from typing import Callable


def _h(seed: str, fixture: str) -> str:
    return f"// fixture {fixture} layout {hashlib.sha256(seed.encode()).hexdigest()[:10]}\n"


def _go_cli(seed: str) -> dict[str, str]:
    return {"go.mod": "module example.invalid/report\ngo 1.22\n", "cmd/report.go": _h(seed,"go-cli-small") + "package main\nimport \"os\"\nfunc encodeJSON() string { return `{\"z\":1,\"a\":2}` } // baseline noncanonical order\nfunc listConfig(dir string) ([]string,error) { _,err:=os.ReadDir(dir); return nil,err } // ENOENT incorrectly fails\n", "cmd/report_test.go": "package main\nimport \"testing\"\nfunc TestBasic(t *testing.T) { if encodeJSON()==\"\" { t.Fatal() } }\n", "internal/legacy_json.go": "package internal\nfunc Encode() string{return \"decoy\"}\n"}


def _go_service_small(seed: str) -> dict[str, str]:
    return {"go.mod":"module example.invalid/service\ngo 1.22\n", "internal/cache/config.go":_h(seed,"go-service-small")+"package cache\nimport \"time\"\nfunc Duration(ttlMs int) time.Duration { return time.Duration(ttlMs) } // baseline nanoseconds\n", "internal/logging/middleware.go":"package logging\nimport \"context\"\nfunc Complete(ctx context.Context) map[string]string { return map[string]string{} } // loses existing correlation id\n", "internal/logging/context.go":"package logging\nconst CorrelationIDKey = \"correlation_id\"\n", "tests/basic_test.go":"package tests\nimport \"testing\"\nfunc TestPlaceholder(t *testing.T){}\n"}


def _go_service_multi(seed: str) -> dict[str, str]:
    return {"go.mod":"module example.invalid/multiservice\ngo 1.22\n", "internal/store/store.go":_h(seed,"go-service-multifile")+"package store\ntype Memory struct{}\nfunc (Memory) Put(k,v string) error{return nil}\n", "internal/config/config.go":"package config\ntype Config struct { Backend string; DefaultRate int }\n", "internal/http/writes.go":"package http\nfunc Write(){} // baseline has no tenant rate limit\n", "tests/conformance_test.go":"package tests\nimport \"testing\"\nfunc TestMemory(t *testing.T){}\n", "docs/storage.md":"Only in-memory storage is documented.\n"}


def _go_service_debug(seed: str) -> dict[str, str]:
    return {"go.mod":"module example.invalid/debug\ngo 1.22\n", "internal/hub/hub.go":_h(seed,"go-service-debug")+"package hub\ntype Hub struct { clients map[string]chan string }\nfunc (h *Hub) Disconnect(id string){} // baseline leak\n", "internal/http/routes.go":"package http\nfunc UserRoute(path string) string { return \"/users/{id}\" } // /users/me shadowed\n", "tests/basic_test.go":"package tests\nimport \"testing\"\nfunc TestBasic(t *testing.T){}\n", "internal/hub/old_hub.go":"package hub\n// archived decoy\n"}


def _go_worker_debug(seed: str) -> dict[str, str]:
    return {"go.mod":"module example.invalid/worker\ngo 1.22\n", "worker/retry.go":_h(seed,"go-worker-debug")+"package worker\nfunc Retry(err error) bool { return err != nil } // baseline retries permanent validation errors\n", "worker/errors.go":"package worker\ntype ValidationError struct{}\nfunc (ValidationError) Error() string{return \"invalid\"}\n", "tests/basic_test.go":"package tests\nimport \"testing\"\nfunc TestBasic(t *testing.T){}\n"}


def _rust_lib(seed: str) -> dict[str, str]:
    return {"Cargo.toml":"[package]\nname=\"collections\"\nversion=\"0.1.0\"\nedition=\"2021\"\n", "src/collections.rs":_h(seed,"rust-lib-small")+"pub fn dedupe_preserving_order(values: Vec<String>) -> Vec<String> { let mut copy=values; copy.sort(); copy.dedup(); copy }\n", "src/lib.rs":"pub mod collections;\n", "tests/basic.rs":"#[test] fn basic(){assert!(true);}\n", "src/sorted_dedupe.rs":"// intentionally different legacy API\n"}


def _rust_cli(seed: str) -> dict[str, str]:
    return {"Cargo.toml":"[package]\nname=\"plugins\"\nversion=\"0.1.0\"\nedition=\"2021\"\n", "src/main.rs":_h(seed,"rust-cli-small")+"fn sort_versions(mut values: Vec<String>) -> Vec<String> { values.sort(); values } // lexical baseline\nfn main(){}\n", "tests/basic.rs":"#[test] fn basic(){assert!(true);}\n", "README.md":"Plugin ordering uses version strings.\n"}


def _rust_debug(seed: str) -> dict[str, str]:
    return {"Cargo.toml":"[package]\nname=\"streaming\"\nversion=\"0.1.0\"\nedition=\"2021\"\n", "src/decode.rs":_h(seed,"rust-debug")+"pub fn decode(chunk: &[u8]) -> String { String::from_utf8_lossy(chunk).into_owned() } // split UTF-8 baseline\n", "src/lib.rs":"pub mod decode;\n", "tests/basic.rs":"#[test] fn basic(){assert!(true);}\n", "src/byte_dump.rs":"// diagnostic decoy\n"}


def _rust_workspace(seed: str) -> dict[str, str]:
    return {"Cargo.toml":"[workspace]\nmembers=[\"crates/indexer\"]\nresolver=\"2\"\n", "crates/indexer/Cargo.toml":"[package]\nname=\"indexer\"\nversion=\"0.1.0\"\nedition=\"2021\"\n", "crates/indexer/src/main.rs":_h(seed,"rust-workspace")+"fn rebuild(){ /* baseline always begins full rebuild */ }\nfn main(){ rebuild() }\n", "docs/rebuild.md":"Full rebuild is currently supported.\n", "crates/indexer/tests/basic.rs":"#[test] fn basic(){assert!(true);}\n"}


def _java_cli(seed: str) -> dict[str, str]:
    return {"pom.xml":"<project><modelVersion>4.0.0</modelVersion><groupId>x</groupId><artifactId>csv</artifactId><version>1</version></project>\n", "src/main/java/app/CsvParser.java":_h(seed,"java-cli-small")+"package app; public class CsvParser { public int parse(String value){ if(value.isEmpty()) throw new IllegalArgumentException(\"header\"); return 1; }}\n", "src/test/java/app/CsvParserTest.java":"package app; class CsvParserTest {}\n", "src/main/java/app/LegacyCsv.java":"package app; class LegacyCsv {}\n"}


def _java_service_small(seed: str) -> dict[str, str]:
    return {"pom.xml":"<project><modelVersion>4.0.0</modelVersion><groupId>x</groupId><artifactId>config</artifactId><version>1</version></project>\n", "src/main/java/app/ConfigLoader.java":_h(seed,"java-service-small")+"package app; import java.io.*; class ConfigLoader { void load() { try{ throw new IOException(\"disk\"); } catch(IOException e){ throw new ConfigLoadException(\"failed\"); } } } class ConfigLoadException extends RuntimeException { ConfigLoadException(String m){super(m);} }\n", "src/test/java/app/ConfigLoaderTest.java":"package app; class ConfigLoaderTest {}\n", "README.md":"Configuration loader service.\n"}


def _java_service_debug(seed: str) -> dict[str, str]:
    return {"pom.xml":"<project><modelVersion>4.0.0</modelVersion><groupId>x</groupId><artifactId>scheduler</artifactId><version>1</version></project>\n", "src/main/java/app/Scheduler.java":_h(seed,"java-service-debug")+"package app; class Scheduler { synchronized void cancel(){} synchronized void complete(){} } // baseline callbacks acquire competing locks elsewhere\n", "src/test/java/app/SchedulerTest.java":"package app; class SchedulerTest {}\n", "docs/locking.md":"Cancellation and completion are thread-safe.\n"}


def _java_spring_small(seed: str) -> dict[str, str]:
    return {"pom.xml":"<project><modelVersion>4.0.0</modelVersion><groupId>x</groupId><artifactId>widgets</artifactId><version>1</version></project>\n", "src/main/java/app/WidgetAdvice.java":_h(seed,"java-spring-small")+"package app; class WidgetAdvice { int status(Exception e){ return 500; } } // missing widget maps incorrectly\n", "src/test/java/app/WidgetAdviceTest.java":"package app; class WidgetAdviceTest {}\n", "src/main/java/app/LegacyAdvice.java":"package app; class LegacyAdvice {}\n"}


def _java_spring_multi(seed: str) -> dict[str, str]:
    return {"pom.xml":"<project><modelVersion>4.0.0</modelVersion><groupId>x</groupId><artifactId>profiles</artifactId><version>1</version></project>\n", "src/main/java/app/Profile.java":_h(seed,"java-spring-multifile")+"package app; class Profile { String name; } // baseline has no version\n", "src/main/java/app/WebhookSigner.java":"package app; class WebhookSigner { String sign(String p){return p;} } // v1 only\n", "migrations/V1__profiles.sql":"CREATE TABLE profiles (id VARCHAR(32) PRIMARY KEY, name VARCHAR(255));\n", "src/test/java/app/IntegrationTest.java":"package app; class IntegrationTest {}\n", "docs/webhooks.md":"Only v1 signatures are documented.\n"}


def _java_spring_debug(seed: str) -> dict[str, str]:
    return {"pom.xml":"<project><modelVersion>4.0.0</modelVersion><groupId>x</groupId><artifactId>etag</artifactId><version>1</version></project>\n", "src/main/java/app/EtagFilter.java":_h(seed,"java-spring-debug")+"package app; class EtagFilter { String etag(byte[] wireBytes){return Integer.toHexString(java.util.Arrays.hashCode(wireBytes));} } // gzip variance\n", "src/test/java/app/EtagTest.java":"package app; class EtagTest {}\n", "README.md":"Conditional responses support compression.\n"}


def _sql_small(seed: str) -> dict[str, str]:
    return {"migrations/001_users.sql":_h(seed,"sql-app-small").replace("//", "--", 1)+"CREATE TABLE users (id INTEGER PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL);\n", "src/models.py":"class User: middle_name = None  # baseline database has no column\n", "tests/test_migrations.py":"def test_initial_schema(): assert True\n", "migrations/legacy_users.sql":"-- historical schema decoy\n"}


def _sql_debug(seed: str) -> dict[str, str]:
    return {"migrations/002_add_status.sql":_h(seed,"sql-app-debug").replace("//", "--", 1)+"ALTER TABLE users ADD COLUMN status TEXT NOT NULL; -- baseline fails populated rows\n", "migrations/002_down.sql":"ALTER TABLE users DROP COLUMN status;\n", "tests/test_migrations.py":"def test_empty_database(): assert True\n", "docs/migrations.md":"Migrations are reversible.\n"}


SYSTEM_FIXTURE_BUILDERS: dict[str, Callable[[str], dict[str, str]]] = {
 "go-cli-small":_go_cli,"go-service-small":_go_service_small,"go-service-multifile":_go_service_multi,"go-service-debug":_go_service_debug,"go-worker-debug":_go_worker_debug,
 "rust-lib-small":_rust_lib,"rust-cli-small":_rust_cli,"rust-debug":_rust_debug,"rust-workspace":_rust_workspace,
 "java-cli-small":_java_cli,"java-service-small":_java_service_small,"java-service-debug":_java_service_debug,"java-spring-small":_java_spring_small,"java-spring-multifile":_java_spring_multi,"java-spring-debug":_java_spring_debug,
 "sql-app-small":_sql_small,"sql-app-debug":_sql_debug,
}


def build_system_fixture(fixture_id: str, seed: str) -> dict[str, str]:
    return SYSTEM_FIXTURE_BUILDERS[fixture_id](seed)
