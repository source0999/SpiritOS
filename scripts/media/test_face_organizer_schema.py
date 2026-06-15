import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.media import face_organizer as fo


def make_test_config(source_dir: Path, registry_path: Path) -> fo.OrganizerConfig:
    return fo.OrganizerConfig(
        source_dir=source_dir,
        db_dir=source_dir / "known_performers",
        report_path=source_dir / "report.html",
        backup_dir=source_dir / "backups",
        rename_manifest_path=source_dir / "rename_plan.json",
        apply=False,
        write_nfo=False,
        backup_videos=False,
        frame_count=1,
        sample_limit=None,
        force=False,
        skip_existing=False,
        recursive=True,
        model_name="buffalo_l",
        ctx_id=-1,
        det_size=(640, 640),
        review_dir_name=".face-review",
        min_face_score=0.5,
        min_face_area_ratio=0.001,
        ocr_watermarks=False,
        organize_manifest_path=source_dir / "organize_manifest.json",
        verification_registry_path=registry_path,
    )


class FakeFace:
    bbox = fo.np.array([0, 0, 32, 32], dtype=fo.np.float32)
    det_score = 0.99
    embedding = fo.np.ones(512, dtype=fo.np.float32)


class FakeRecognizer:
    class ImageCls:
        @staticmethod
        def open(path: Path):
            class Image:
                size = (640, 480)

                def close(self) -> None:
                    pass

            return Image()

    image_cls = ImageCls

    def __init__(self, *args, **kwargs) -> None:
        pass

    def detect(self, image_path: Path) -> list[FakeFace]:
        return [FakeFace()]

    def save_crop(self, frame_path: Path, face: FakeFace, crop_path: Path) -> None:
        crop_path.parent.mkdir(parents=True, exist_ok=True)
        crop_path.write_bytes(b"fake-crop")


class FaceOrganizerSchemaTests(unittest.TestCase):
    def test_missing_identity_schema_fields_read_as_empty_defaults(self) -> None:
        fields = fo.identity_schema_fields({"schema": "media-face-organizer/v1"})

        self.assertEqual(fields["web_text_evidence"], [])
        self.assertEqual(fields["identity_trace"], [])
        self.assertEqual(fields["assignment_decision"]["schema"], fo.ASSIGNMENT_DECISION_SCHEMA)
        self.assertFalse(fields["assignment_decision"]["auto_assign_allowed"])
        self.assertTrue(fields["assignment_decision"]["review_required"])

    def test_web_text_evidence_normalizes_trust_and_review_defaults(self) -> None:
        items = fo.normalize_web_text_evidence(
            [
                {
                    "provider": "manual-yandex-url",
                    "query": '"publichandle" onlyfans',
                    "url": "https://yandex.com/search/?text=publichandle",
                    "source_trust_level": "not-a-tier",
                    "confidence": 0.42,
                }
            ]
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["schema"], fo.WEB_TEXT_EVIDENCE_SCHEMA)
        self.assertEqual(items[0]["source_trust_level"], "unknown")
        self.assertTrue(items[0]["review_required"])
        self.assertTrue(items[0]["unsafe_untrusted_content"])

    def test_registry_loader_adds_optional_schema_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            registry_path = Path(temp_name) / "performer_verification.json"
            registry_path.write_text(
                json.dumps({"schema": "media-performer-verification/v1", "performers": {}, "aliases": {}}),
                encoding="utf-8",
            )

            registry = fo.load_performer_registry(registry_path)

        self.assertEqual(registry["optional_schemas"]["web_text_evidence"], fo.WEB_TEXT_EVIDENCE_SCHEMA)
        self.assertEqual(registry["optional_schemas"]["identity_trace"], fo.IDENTITY_TRACE_SCHEMA)
        self.assertEqual(registry["optional_schemas"]["assignment_decision"], fo.ASSIGNMENT_DECISION_SCHEMA)

    def test_dry_run_verify_accepts_old_sidecar_and_exposes_additive_model_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            sidecar = root / "sample.mp4.face-meta.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(root / "sample.mp4"),
                        "performers": [
                            {
                                "name": "Public Stage Handle",
                                "status": "auto",
                                "verification_needed": False,
                                "source_signals": ["profile_url"],
                            }
                        ],
                        "metadata_hints": {
                            "candidate_names": [
                                {
                                    "name": "Public Stage Handle",
                                    "source": "watermark_ocr_text",
                                    "raw": "OnlyFans.com/publicstagehandle",
                                    "confidence": 0.82,
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )

            summary = fo.verify_performers(make_test_config(root, root / "performer_verification.json"))

        self.assertEqual(summary["scanned_records"], 1)
        self.assertEqual(summary["model_count"], 1)

        model = fo.model_index_entry(
            "public-stage-handle",
            {
                "name": "Public Stage Handle",
                "status": "profile-url",
                "video_count": 1,
                "profile_handles": [],
                "web_text_evidence_summary": fo.summarize_web_text_evidence([]),
                "identity_trace_summary": {"schema": fo.IDENTITY_TRACE_SCHEMA, "count": 0, "review_required": True},
                "assignment_decision": fo.blank_assignment_decision(),
            },
        )
        self.assertEqual(model["assignment_status"], "profile-url")
        self.assertEqual(model["identity_confidence"], 0.0)
        self.assertEqual(model["primary_evidence_role"], "profile-url")
        self.assertTrue(model["review_required"])

    def test_profile_slash_ocr_extracts_normalized_candidate_and_queries(self) -> None:
        candidates = fo.watermark_candidates(
            [
                {
                    "text": "OnlyFans.com/public_stage",
                    "region": "bottom_right",
                    "confidence": 0.91,
                    "frame_path": "/tmp/frame.jpg",
                }
            ]
        )

        self.assertEqual(candidates[0]["source"], "watermark_profile_url")
        self.assertEqual(candidates[0]["platform"], "onlyfans")
        self.assertEqual(candidates[0]["handle"], "public_stage")
        self.assertIn("Public Stage", candidates[0]["variants"])

        queries = fo.text_verification_queries(candidates, limit=1)
        self.assertTrue(any(item["label"] == "Yandex OnlyFans" for item in queries))
        self.assertTrue(all(item["text_only"] for item in queries))

    def test_angetawhite_alias_canonicalizes_to_angela_white(self) -> None:
        self.assertEqual(fo.split_handle_words("Angetawhite"), "Angela White")
        self.assertEqual(fo.canonical_performer_name("Angetawhite", fo.blank_performer_registry()), "Angela White")

    def test_407017_ocr_hints_keep_visible_text_variants_without_web_calls(self) -> None:
        candidates = fo.watermark_candidates(
            [
                {"text": "M Anyuitio", "region": "bottom_strip", "confidence": 0.82},
                {"text": "M Anvuitio", "region": "bottom_strip", "confidence": 0.8},
                {"text": "Mulan T", "region": "bottom_strip", "confidence": 0.76},
                {"text": "M Muanvuitto", "region": "full", "confidence": 0.61},
                {"text": "RETO", "region": "full", "confidence": 0.58},
            ]
        )

        names = [item["name"] for item in candidates]
        self.assertIn("M Anyuitio", names)
        self.assertIn("Mulan T", names)
        anyuitio = next(item for item in candidates if item["name"] == "M Anyuitio")
        self.assertIn("Anyuitio", anyuitio["variants"])

        queries = fo.text_verification_queries(candidates, limit=8)
        self.assertTrue(any(item["query"] == '"M Anyuitio" site:pimpbunny.com' for item in queries))
        self.assertTrue(any(item["query"] == '"Mulan T" site:coomer.st' for item in queries))
        self.assertFalse(any(item["url"].lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".m3u8")) for item in queries))

    def test_manual_correction_fixture_is_not_filename_mapping(self) -> None:
        hints = fo.build_metadata_hints(Path("/DATA/yes/unknown/407017_720p.mp4"), False, [], False)

        names = [item["name"] for item in hints["candidate_names"]]
        self.assertNotIn("Mulan Vuitton", names)

        correction = fo.store_manual_correction(
            make_test_config(Path("/tmp/source"), Path("/tmp/registry.json")),
            Path("/tmp/407017_720p.mp4.face-meta.json"),
            "Mulan Vuitton",
            corrected_by="Britton",
        )

        self.assertEqual(correction["new_canonical_name"], "Mulan Vuitton")
        self.assertEqual(correction["status"], "pending")
        self.assertTrue(correction["text_verification_queries"])
        self.assertFalse(correction["face_enrollment_performed"])

    def test_host_watermark_is_not_used_as_performer_name(self) -> None:
        candidates = fo.watermark_candidates(
            [{"text": "Visit onlyshare.io for MORE", "region": "bottom_strip", "confidence": 0.92}]
        )

        self.assertTrue(any(item.get("source") == "site_watermark" for item in candidates))
        result = fo.score_assignment({"performers": [], "metadata_hints": {"candidate_names": candidates}})

        decision = result["assignment_decision"]
        self.assertIsNone(decision["suggested_name"])
        self.assertIn("no_assignable_identity_signal", decision["blocking_reasons"])

    def test_user_entered_name_generates_search_queries(self) -> None:
        queries = fo.manual_name_queries("Aaliyah Yasan")

        self.assertTrue(any('"Aaliyah Yasan"' in item["query"] for item in queries))
        self.assertTrue(all(item["text_only"] for item in queries))

    def test_known_registry_without_embedding_reports_not_face_enrolled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            registry_path = root / "performer_verification.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "schema": "media-performer-verification/v1",
                        "performers": {
                            "izzy-green": {"name": "Izzy Green", "slug": "izzy-green", "aliases": []}
                        },
                        "aliases": {},
                    }
                ),
                encoding="utf-8",
            )
            (root / "model_index.json").write_text(
                json.dumps({"schema": "spiritflix-model-index/v1", "models": [{"name": "Izzy Green", "slug": "izzy-green"}]}),
                encoding="utf-8",
            )
            db_dir = root / "known_performers"
            db_dir.mkdir()
            (db_dir / "index.json").write_text(json.dumps({"performers": []}), encoding="utf-8")
            (db_dir / "performer_map.json").write_text(json.dumps({}), encoding="utf-8")
            fo.np.save(db_dir / "embeddings.npy", fo.np.empty((0, 512), dtype=fo.np.float32))
            config = dataclasses.replace(make_test_config(root, registry_path), db_dir=db_dir)

            audit = fo.audit_known_db(config)

        self.assertEqual(audit["performers_missing_known_record"][0]["name"], "Izzy Green")
        self.assertEqual(audit["performers_missing_known_record"][0]["status"], "in registry/model index, not face-enrolled")

    def test_confirmed_correction_requires_explicit_apply_before_registry_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            sidecar = root / "sample.mp4.face-meta.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(root / "sample.mp4"),
                        "manual_correction_pending": {
                            "status": "pending",
                            "corrected_by": "Britton",
                            "corrected_at": fo.utc_now(),
                            "source_file": str(root / "sample.mp4"),
                            "previous_suggestion": "M Anyuitio",
                            "new_canonical_name": "Mulan Vuitton",
                            "evidence_role": "user_confirmed_correction",
                            "face_enrollment_performed": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            registry_path = root / "performer_verification.json"
            config = make_test_config(root, registry_path)

            event = fo.confirm_manual_correction(config, sidecar, confirmed_by="Britton")

        self.assertEqual(event["new_canonical_name"], "Mulan Vuitton")
        self.assertFalse(registry_path.exists())

    def test_apply_manual_name_correction_queues_unenrolled_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "407017_720p.mp4"
            video.write_bytes(b"placeholder")
            sidecar = root / "407017_720p.mp4.face-meta.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(video),
                        "verification_needed": True,
                        "performers": [{"name": "unknown performer", "status": "unknown"}],
                    }
                ),
                encoding="utf-8",
            )
            registry_path = root / "performer_verification.json"
            db_dir = root / "known_performers"
            db_dir.mkdir()
            (db_dir / "index.json").write_text(json.dumps({"performers": []}), encoding="utf-8")
            (db_dir / "performer_map.json").write_text(json.dumps({}), encoding="utf-8")
            fo.np.save(db_dir / "embeddings.npy", fo.np.empty((0, 512), dtype=fo.np.float32))
            config = dataclasses.replace(make_test_config(root, registry_path), db_dir=db_dir, apply=True)

            result = fo.apply_manual_name_correction(config, sidecar, "Mulan Vuitton", corrected_by="Britton", confirmed_by="Britton")

            self.assertEqual(result["next_action"], "queued_for_face_enrollment")
            self.assertEqual(result["presence"]["status"], "in registry/model index, not face-enrolled")
            self.assertTrue(registry_path.exists())
            self.assertTrue((root / "model_index.json").exists())
            updated_sidecar = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertFalse(updated_sidecar["verification_needed"])
            self.assertEqual(updated_sidecar["manual_confirmed_model"]["name"], "Mulan Vuitton")
            self.assertFalse(updated_sidecar["manual_confirmed_model"]["face_enrolled"])
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertEqual(registry["performers"]["mulan-vuitton"]["evidence"][-1]["video_path"], str(video))
            groups = fo.build_enrollment_groups(config)
            self.assertTrue(any(group["name"] == "Mulan Vuitton" and group["candidate_videos"] == 1 for group in groups["groups"]))

    def test_enrolled_groups_include_candidate_ready_unenrolled_performer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Devorah Roloff sample.mp4"
            video.write_bytes(b"placeholder")
            sidecar = fo.meta_path_for(video)
            sidecar.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "performers": [{"name": "Devorah Roloff", "status": "manual-confirmed", "verification_needed": False}],
                    }
                ),
                encoding="utf-8",
            )
            registry_path = root / "performer_verification.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "schema": "media-performer-verification/v1",
                        "performers": {"devorah-roloff": {"name": "Devorah Roloff", "slug": "devorah-roloff", "status": "user-confirmed"}},
                        "aliases": {},
                    }
                ),
                encoding="utf-8",
            )
            crop = root / ".face-review" / "enrollment" / "devorah-roloff" / "crops" / "sample-face.jpg"
            crop.parent.mkdir(parents=True)
            crop.write_bytes(b"fake-jpeg")
            candidates = root / ".face-review" / "enrollment" / "enrollment_candidates.json"
            candidates.parent.mkdir(parents=True, exist_ok=True)
            candidates.write_text(
                json.dumps(
                    {
                        "groups": [
                            {
                                "slug": "devorah-roloff",
                                "name": "Devorah Roloff",
                                "recommended_crops": [
                                    {
                                        "crop_path": str(crop),
                                        "source_video": str(video),
                                        "source_video_name": video.name,
                                        "detection_score": 0.91,
                                        "quality_score": 0.91,
                                    }
                                ],
                                "recommended_stills": [],
                                "candidate_face_crops": 1,
                                "candidate_videos": 1,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, registry_path)

            payload = fo.build_enrolled_groups(config)

        groups = [group for group in payload["groups"] if group["name"] == "Devorah Roloff"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["candidate_face_crops"], 1)
        self.assertEqual(groups[0]["embedding_rows"], [])

    def test_manual_name_correction_reuses_existing_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "432038_720p.mkv"
            video.write_bytes(b"placeholder")
            sidecar = root / "432038_720p.mkv.face-meta.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(video),
                        "verification_needed": True,
                        "performers": [{"name": "unknown performer", "status": "unknown"}],
                    }
                ),
                encoding="utf-8",
            )
            registry_path = root / "performer_verification.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "schema": "media-performer-verification/v1",
                        "performers": {
                            "angela-white": {
                                "name": "Angela White",
                                "slug": "angela-white",
                                "aliases": ["Ang Lawhite"],
                                "status": "user-confirmed",
                            }
                        },
                        "aliases": {"anglawhite": "Angela White"},
                    }
                ),
                encoding="utf-8",
            )
            config = dataclasses.replace(make_test_config(root, registry_path), apply=True)

            lookup = fo.lookup_manual_model_name(config, "Ang Lawhite")
            result = fo.apply_manual_name_correction(config, sidecar, "Ang Lawhite", corrected_by="Britton", confirmed_by="Britton")
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            updated_sidecar = json.loads(sidecar.read_text(encoding="utf-8"))

        self.assertTrue(lookup["existing"])
        self.assertEqual(lookup["canonical_name"], "Angela White")
        self.assertTrue(result["auto_existing_match"])
        self.assertEqual(result["name"], "Angela White")
        self.assertIn("angela-white", registry["performers"])
        self.assertNotIn("ang-lawhite", registry["performers"])
        self.assertEqual(updated_sidecar["manual_confirmed_model"]["name"], "Angela White")

    def test_metadata_hints_include_deterministic_text_queries(self) -> None:
        hints = fo.build_metadata_hints(Path("/DATA/yes/unknown/Mulan_T.mp4"), False, [], False)

        self.assertIn("text_verification_queries", hints)
        self.assertTrue(hints["text_verification_queries"])
        self.assertTrue(all(item["text_only"] for item in hints["text_verification_queries"]))

    def test_url_generation_provider_returns_generated_text_urls_only(self) -> None:
        candidate = fo.normalized_candidate("Mulan T", "watermark_ocr_text", 0.66, "Mulan T")
        self.assertIsNotNone(candidate)

        packet = fo.provider_dry_run_packet([candidate], [fo.UrlGenerationProvider("manual-url-provider")])

        self.assertFalse(packet["network_executed"])
        self.assertTrue(packet["text_only"])
        self.assertTrue(packet["results"])
        self.assertTrue(all(item["result_type"] == "generated_url" for item in packet["results"]))
        self.assertTrue(any(item["label"] == "Yandex Coomer" for item in packet["results"]))

    def test_configured_domain_provider_keeps_repost_domains_low_trust(self) -> None:
        candidate = fo.normalized_candidate("Mulan T", "watermark_ocr_text", 0.66, "Mulan T")
        self.assertIsNotNone(candidate)

        provider = fo.ConfiguredDomainProvider("configured-domains", ("example-profile.test", "coomer.st"))
        results = provider.collect([candidate])

        by_domain = {item["source_domain"]: item for item in results}
        self.assertEqual(by_domain["example-profile.test"]["source_trust_level"], "configured-corroborator")
        self.assertEqual(by_domain["coomer.st"]["source_trust_level"], "repost-index")
        self.assertTrue(all(item["text_only"] for item in results))

    def test_mock_search_provider_normalizes_text_result_evidence(self) -> None:
        candidate = fo.normalized_candidate("Public Stage", "watermark_ocr_text", 0.7, "Public Stage")
        self.assertIsNotNone(candidate)
        query = fo.text_verification_queries([candidate], limit=1)[0]["query"]
        provider = fo.MockSearchProvider(
            "mock-searxng",
            {
                query: [
                    {
                        "title": "Public Stage official profile",
                        "url": "https://onlyfans.com/publicstage",
                        "content": "Visible text result for publicstage",
                    },
                    {
                        "title": "Public Stage repost listing",
                        "url": "https://pimpbunny.com/models/publicstage",
                        "snippet": "Corroborating text only",
                    },
                ]
            },
        )

        evidence = provider.collect([candidate])

        self.assertEqual(len(evidence), 2)
        self.assertEqual(evidence[0]["source_trust_level"], "creator-profile")
        self.assertEqual(evidence[1]["source_trust_level"], "repost-index")
        self.assertTrue(all(item["review_required"] for item in evidence))
        self.assertTrue(all(item["unsafe_untrusted_content"] for item in evidence))

    def test_scorer_allows_high_confidence_local_face_auto(self) -> None:
        result = fo.score_assignment(
            {
                "performers": [
                    {
                        "name": "Sava Schultz",
                        "status": "auto",
                        "similarity": 0.91,
                        "verification_needed": False,
                        "model_version": "insightface:buffalo_l",
                    }
                ],
                "metadata_hints": {"candidate_names": []},
            }
        )

        decision = result["assignment_decision"]
        self.assertEqual(decision["suggested_name"], "Sava Schultz")
        self.assertTrue(decision["auto_assign_allowed"])
        self.assertFalse(decision["review_required"])
        self.assertEqual(result["identity_trace"][0]["signal_type"], "local_face")

    def test_scorer_keeps_weak_ocr_review_required(self) -> None:
        result = fo.score_assignment(
            {
                "performers": [],
                "metadata_hints": {
                    "candidate_names": [
                        fo.normalized_candidate("M Anyuitio", "watermark_ocr_text", 0.62, "M Anyuitio")
                    ]
                },
            }
        )

        decision = result["assignment_decision"]
        self.assertEqual(decision["suggested_name"], "M Anyuitio")
        self.assertFalse(decision["auto_assign_allowed"])
        self.assertTrue(decision["review_required"])
        self.assertIn("ocr_text_requires_review", decision["blocking_reasons"])

    def test_scorer_blocks_face_text_contradiction(self) -> None:
        result = fo.score_assignment(
            {
                "performers": [
                    {
                        "name": "Sava Schultz",
                        "status": "auto",
                        "similarity": 0.89,
                        "verification_needed": False,
                    }
                ],
                "metadata_hints": {
                    "candidate_names": [
                        fo.normalized_candidate(
                            "Public Stage",
                            "watermark_profile_url",
                            0.88,
                            "OnlyFans.com/publicstage",
                            platform="onlyfans",
                            handle="publicstage",
                            profile_url="https://onlyfans.com/publicstage",
                            evidence_role="watermark_profile_url",
                        )
                    ]
                },
            }
        )

        decision = result["assignment_decision"]
        self.assertFalse(decision["auto_assign_allowed"])
        self.assertTrue(decision["review_required"])
        self.assertIn("local_face_text_contradiction", decision["blocking_reasons"])

    def test_scorer_keeps_repost_web_text_as_review_only(self) -> None:
        result = fo.score_assignment(
            {
                "performers": [],
                "metadata_hints": {
                    "candidate_names": [
                        fo.normalized_candidate("Public Stage", "watermark_ocr_text", 0.64, "Public Stage")
                    ]
                },
                "web_text_evidence": [
                    {
                        "provider": "mock",
                        "query": '"Public Stage"',
                        "url": "https://pimpbunny.com/models/publicstage",
                        "title": "Public Stage listing",
                        "snippet": "Public Stage",
                        "source_trust_level": "repost-index",
                        "confidence": 0.35,
                    }
                ],
            }
        )

        decision = result["assignment_decision"]
        self.assertFalse(decision["auto_assign_allowed"])
        self.assertTrue(decision["review_required"])
        self.assertIn("web_text_requires_review", decision["blocking_reasons"])
        self.assertTrue(any(item["signal_type"] == "web_text" for item in result["identity_trace"]))

    def test_scorer_rejects_host_or_noise_name(self) -> None:
        result = fo.score_assignment(
            {
                "performers": [],
                "metadata_hints": {
                    "candidate_names": [
                        {
                            "name": "OnlyFans",
                            "source": "watermark_ocr_text",
                            "confidence": 0.9,
                            "raw": "OnlyFans",
                        }
                    ]
                },
            }
        )

        decision = result["assignment_decision"]
        self.assertIsNone(decision["suggested_name"])
        self.assertFalse(decision["auto_assign_allowed"])
        self.assertIn("no_assignable_identity_signal", decision["blocking_reasons"])

    def test_report_renders_trace_queries_evidence_and_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            sidecar = root / "sample.mp4.face-meta.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(root / "sample.mp4"),
                        "verification_needed": True,
                        "performers": [],
                        "metadata_hints": {
                            "candidate_names": [
                                fo.normalized_candidate("Public Stage", "watermark_ocr_text", 0.66, "Public Stage")
                            ]
                        },
                        "web_text_evidence": [
                            {
                                "provider": "mock",
                                "query": '"Public Stage"',
                                "url": "https://pimpbunny.com/models/publicstage",
                                "title": "Public Stage listing",
                                "snippet": "Corroborating text only",
                                "source_trust_level": "repost-index",
                                "confidence": 0.35,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report_path = root / "report.html"

            fo.generate_report(make_test_config(root, root / "performer_verification.json"))
            html = report_path.read_text(encoding="utf-8")

        self.assertIn("Actual model/creator name", html)
        self.assertIn("Save pending evidence", html)
        self.assertIn("Confirm database update", html)
        self.assertIn("preview-panel", html)
        self.assertIn("Verification hints", html)
        self.assertIn("Show details", html)
        self.assertIn("Why this name?", html)
        self.assertIn("Generated text queries", html)
        self.assertIn("Web text evidence", html)
        self.assertIn("Text result only. Review required.", html)
        self.assertLess(html.index("preview-panel"), html.index("Show details"))
        self.assertLess(html.index("Verification hints"), html.index("Show details"))

    def test_report_all_includes_auto_records_in_audit_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            sidecar = root / "auto.mp4.face-meta.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(root / "auto.mp4"),
                        "verification_needed": False,
                        "performers": [
                            {
                                "name": "Sava Schultz",
                                "status": "auto",
                                "similarity": 0.91,
                                "verification_needed": False,
                            }
                        ],
                        "metadata_hints": {"candidate_names": []},
                    }
                ),
                encoding="utf-8",
            )
            config = dataclasses.replace(
                make_test_config(root, root / "performer_verification.json"),
                report_path=root / "audit.html",
                report_all=True,
            )

            fo.generate_report(config)
            html = config.report_path.read_text(encoding="utf-8")

        self.assertIn("All Records Audit", html)
        self.assertIn("auto.mp4", html)
        self.assertIn("Sava Schultz", html)

    def test_profile_handle_parser_accepts_platform_handles_and_urls(self) -> None:
        handles = fo.parse_profile_handles(["onlyfans:publicstage", "https://fansly.com/other_stage"])

        self.assertEqual(handles[0]["platform"], "onlyfans")
        self.assertEqual(handles[0]["handle"], "publicstage")
        self.assertEqual(handles[1]["platform"], "fansly")
        self.assertEqual(handles[1]["url"], "https://fansly.com/other_stage")

    def test_add_performer_dry_run_does_not_create_db_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            image = root / "crop.jpg"
            image.write_bytes(b"not-real-image-but-dry-run")
            config = make_test_config(root, root / "performer_verification.json")

            fo.add_performer_from_image(
                config,
                "Public Stage",
                image,
                aliases=["publicstage"],
                profile_handles=fo.parse_profile_handles(["onlyfans:publicstage"]),
                confirmed_by="Britton",
            )

            self.assertFalse((root / "known_performers" / "index.json").exists())
            self.assertFalse(config.verification_registry_path.exists())

    def test_add_performer_apply_records_index_and_registry_audit(self) -> None:
        original = fo.InsightFaceRecognizer
        try:
            fo.InsightFaceRecognizer = FakeRecognizer
            with tempfile.TemporaryDirectory() as temp_name:
                root = Path(temp_name)
                image = root / "crop.jpg"
                image.write_bytes(b"fake-local-crop")
                config = dataclasses.replace(
                    make_test_config(root, root / "performer_verification.json"),
                    apply=True,
                    db_dir=root / "known_performers",
                    min_face_score=0.5,
                )

                fo.add_performer_from_image(
                    config,
                    "Public Stage",
                    image,
                    aliases=["publicstage"],
                    profile_handles=fo.parse_profile_handles(["onlyfans:publicstage"]),
                    profile_urls=["https://onlyfans.com/publicstage"],
                    confirmed_by="Britton",
                )

                index = json.loads((config.db_dir / "index.json").read_text(encoding="utf-8"))
                registry = json.loads(config.verification_registry_path.read_text(encoding="utf-8"))
                samples = list((config.db_dir / "faces" / "public-stage").glob("*.jpg"))
        finally:
            fo.InsightFaceRecognizer = original

        self.assertEqual(index["performers"][0]["confirmed_by"], "Britton")
        self.assertEqual(index["performers"][0]["profile_handles"][0]["handle"], "publicstage")
        self.assertTrue(samples)
        self.assertEqual(registry["performers"]["public-stage"]["status"], "user-confirmed")
        self.assertEqual(registry["performers"]["public-stage"]["audit_events"][0]["event"], "confirmed_crop_enrolled")

    def test_enrollment_queue_groups_registry_model_performers_missing_embeddings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            registry_path = root / "performer_verification.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "schema": "media-performer-verification/v1",
                        "performers": {
                            "public-stage": {"name": "Public Stage", "slug": "public-stage", "status": "user-confirmed"}
                        },
                        "aliases": {},
                    }
                ),
                encoding="utf-8",
            )
            (root / "model_index.json").write_text(
                json.dumps({"schema": "spiritflix-model-index/v1", "models": [{"name": "Public Stage", "slug": "public-stage"}]}),
                encoding="utf-8",
            )
            config = make_test_config(root, registry_path)

            payload = fo.build_enrollment_groups(config)

        self.assertEqual(payload["summary"]["groups_found"], 1)
        self.assertEqual(payload["groups"][0]["name"], "Public Stage")
        self.assertEqual(payload["groups"][0]["status"], "user-confirmed but not face-enrolled")
        self.assertFalse(payload["groups"][0]["embedding_rows"])

    def test_enrollment_timestamps_spread_across_video(self) -> None:
        timestamps = fo.enrollment_timestamps(100.0, 5)

        self.assertEqual(len(timestamps), 5)
        self.assertLess(timestamps[0], timestamps[2])
        self.assertLess(timestamps[2], timestamps[-1])
        self.assertGreaterEqual(timestamps[0], 2.0)

    def test_candidate_ranking_prefers_clear_large_face(self) -> None:
        weak = type("WeakFace", (), {"bbox": fo.np.array([0, 0, 20, 20], dtype=fo.np.float32), "det_score": 0.62})()
        clear = type("ClearFace", (), {"bbox": fo.np.array([0, 0, 180, 180], dtype=fo.np.float32), "det_score": 0.96})()

        self.assertGreater(fo.face_quality_score(clear, (640, 480), 200.0), fo.face_quality_score(weak, (640, 480), 0.0))

    def test_generate_enrollment_candidates_recommends_five_when_enough_valid_crops_exist(self) -> None:
        original_recognizer = fo.InsightFaceRecognizer
        original_extract = fo.extract_frame_at
        original_duration = fo.ffprobe_duration
        try:
            fo.InsightFaceRecognizer = FakeRecognizer
            fo.extract_frame_at = lambda video, frame, timestamp: frame.write_bytes(b"fake-frame")
            fo.ffprobe_duration = lambda video: 120.0
            with tempfile.TemporaryDirectory() as temp_name:
                root = Path(temp_name)
                video = root / "sample.mp4"
                video.write_bytes(b"not-real-video")
                (root / "sample.mp4.face-meta.json").write_text(
                    json.dumps(
                        {
                            "schema": "media-face-organizer/v1",
                            "video_path": str(video),
                            "manual_correction_pending": {"new_canonical_name": "Public Stage", "status": "pending"},
                            "verification_needed": True,
                        }
                    ),
                    encoding="utf-8",
                )
                config = make_test_config(root, root / "performer_verification.json")

                payload = fo.generate_enrollment_candidates(config, frames_per_group=6)
        finally:
            fo.InsightFaceRecognizer = original_recognizer
            fo.extract_frame_at = original_extract
            fo.ffprobe_duration = original_duration

        self.assertGreaterEqual(len(payload["groups"][0]["recommended_crops"]), 5)
        self.assertFalse(payload["groups"][0]["blocked_reason"].startswith("only"))

    def test_blocked_reason_when_fewer_than_five_candidates_exist(self) -> None:
        reason = fo.blocked_reason_for_candidates([{"video_path": "one.mp4"}], [{"crop_path": "a.jpg"}, {"crop_path": "b.jpg"}], ["too blurry"])

        self.assertIn("only 2 valid crops found", reason)
        self.assertIn("only one source video found", reason)

    def test_pending_manual_correction_creates_candidate_but_does_not_enroll(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "sample.mp4"
            video.write_bytes(b"video")
            (root / "sample.mp4.face-meta.json").write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(video),
                        "manual_correction_pending": {"new_canonical_name": "Public Stage", "status": "pending"},
                        "verification_needed": True,
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, root / "performer_verification.json")
            payload = fo.build_enrollment_groups(config)

        self.assertEqual(payload["groups"][0]["status"], "unknown/review items with pending manual correction")
        self.assertFalse((root / "known_performers" / "index.json").exists())

    def test_enrollment_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            config = make_test_config(root, root / "performer_verification.json")
            crop = fo.enrollment_review_dir(config) / "public-stage" / "crops" / "crop.jpg"
            crop.parent.mkdir(parents=True)
            crop.write_bytes(b"crop")

            with self.assertRaisesRegex(RuntimeError, "confirmation"):
                fo.enroll_selected_crops(
                    config,
                    {"performer_name": "Public Stage", "confirmation": "wrong", "crop_paths": [str(crop)], "create_new": True},
                )

    def test_multiple_embeddings_can_map_to_one_performer_and_sava_embedding_remains(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            db = fo.KnownPerformersDB(root / "known_performers")
            db.ensure()
            sava_id = db.add_performer("Sava Schultz")
            db.append_embedding(sava_id, fo.np.ones(512, dtype=fo.np.float32))
            public_id = db.add_performer("Public Stage")
            db.append_embedding(public_id, fo.np.ones(512, dtype=fo.np.float32) * 2)
            db.append_embedding(public_id, fo.np.ones(512, dtype=fo.np.float32) * 3)
            summary = fo.known_db_summary(root / "known_performers")

        self.assertEqual(summary["performer_map"]["0"], "sava-schultz")
        self.assertEqual(summary["performer_map"]["1"], "public-stage")
        self.assertEqual(summary["performer_map"]["2"], "public-stage")

    def test_backup_known_performers_files_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            config = make_test_config(root, root / "performer_verification.json")
            db = fo.KnownPerformersDB(config.db_dir)
            db.ensure()

            backup = fo.backup_known_performers_files(config)
            self.assertTrue((backup / "index.json").exists())
            self.assertTrue((backup / "performer_map.json").exists())
            self.assertTrue((backup / "embeddings.npy").exists())

    def test_manual_crop_endpoint_rejects_invalid_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            with self.assertRaisesRegex(RuntimeError, "outside still frame"):
                fo.validate_crop_coordinates({"x": 90, "y": 90, "width": 20, "height": 20}, 100, 100)

    def test_manual_crop_multiface_is_candidate_evidence_not_enrolled(self) -> None:
        class MultiFaceRecognizer(FakeRecognizer):
            def detect(self, image_path: Path) -> list[FakeFace]:
                return [FakeFace(), FakeFace()]

        original_recognizer = fo.InsightFaceRecognizer
        try:
            fo.InsightFaceRecognizer = MultiFaceRecognizer
            with tempfile.TemporaryDirectory() as temp_name:
                from PIL import Image

                root = Path(temp_name)
                still = root / "still.jpg"
                Image.new("RGB", (200, 200), "white").save(still)
                config = make_test_config(root, root / "performer_verification.json")

                record = fo.save_manual_crop_candidate(
                    config,
                    {"performer": "Public Stage", "still_path": str(still), "crop": {"x": 10, "y": 10, "width": 80, "height": 80}},
                )
        finally:
            fo.InsightFaceRecognizer = original_recognizer

        self.assertEqual(record["validation"]["status"], "stored_candidate_evidence")
        self.assertIn("multi-face", record["validation"]["reason"])
        self.assertFalse(record["enrolled"])

    def test_report_nav_links_point_to_generated_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            config = make_test_config(root, root / "performer_verification.json")

            fo.generate_report(config)
            html = config.report_path.read_text(encoding="utf-8")

            self.assertIn("face_enrollment_queue.html", html)
            self.assertIn("face_gallery.html", html)
            self.assertIn("known_db_audit.html", html)
            self.assertTrue(config.report_path.with_name("face_enrollment_queue.html").exists())
            self.assertTrue(config.report_path.with_name("face_gallery.html").exists())
            self.assertTrue(config.report_path.with_name("known_db_audit.html").exists())

    def test_manual_crop_page_shows_save_feedback_and_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            config = make_test_config(root, root / "performer_verification.json")

            fo.generate_manual_crop_page(config)
            html = config.report_path.with_name("manual_crop.html").read_text(encoding="utf-8")

        self.assertIn("Saving crop candidate and validating face", html)
        self.assertIn("/api/enrollment/manual-crop", html)
        self.assertIn("Saved crop candidate", html)

    def test_enrollment_page_has_manual_still_button_and_merge_panel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            config = make_test_config(root, root / "performer_verification.json")
            payload = {
                "summary": {"groups_found": 1},
                "groups": [
                    {
                        "slug": "public-stage",
                        "name": "Public Stage",
                        "status": "user-confirmed but not face-enrolled",
                        "why": "test",
                        "registry_present": True,
                        "model_index_present": True,
                        "known_performers_record": False,
                        "embedding_rows": [],
                        "candidate_videos": 1,
                        "candidate_face_crops": 1,
                        "exists_because": ["registry"],
                        "recommended_crops": [
                            {
                                "crop_path": str(root / "crop.jpg"),
                                "still_path": str(root / "still.jpg"),
                                "source_video": str(root / "sample.mp4"),
                                "source_video_name": "sample.mp4",
                                "timestamp": 12.3,
                                "detection_score": 0.9,
                                "quality_score": 0.8,
                            }
                        ],
                    }
                ],
            }

            fo.generate_enrollment_queue_page(config, payload)
            html = config.report_path.with_name("face_enrollment_queue.html").read_text(encoding="utf-8")

        self.assertIn("Manual crop this still", html)
        self.assertIn("Merge duplicate creator / alias", html)
        self.assertIn("/api/enrollment/merge-creator", html)

    def test_merge_duplicate_creator_dry_run_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            config = make_test_config(root, root / "performer_verification.json")

            with self.assertRaisesRegex(RuntimeError, "confirmation"):
                fo.merge_duplicate_creator(config, {"source_name": "Public Stage", "target_name": "Known Stage", "confirmation": "wrong"})

    def test_merge_duplicate_creator_apply_updates_registry_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            registry_path = root / "performer_verification.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "schema": "media-performer-verification/v1",
                        "performers": {
                            "known-stage": {"name": "Known Stage", "slug": "known-stage", "aliases": [], "video_count": 1},
                            "duplicate-stage": {"name": "Duplicate Stage", "slug": "duplicate-stage", "aliases": ["dupstage"], "video_count": 2},
                        },
                        "aliases": {},
                    }
                ),
                encoding="utf-8",
            )
            config = dataclasses.replace(make_test_config(root, registry_path), apply=True)

            result = fo.merge_duplicate_creator(
                config,
                {
                    "source_name": "Duplicate Stage",
                    "target_name": "Known Stage",
                    "confirmation": "Known Stage",
                    "confirmed_by": "Britton",
                },
            )
            registry = json.loads(registry_path.read_text(encoding="utf-8"))

        self.assertEqual(result["event"], "duplicate_creator_merged")
        self.assertIn("known-stage", registry["performers"])
        self.assertNotIn("duplicate-stage", registry["performers"])
        self.assertIn("Duplicate Stage", registry["performers"]["known-stage"]["aliases"])
        self.assertEqual(registry["aliases"]["duplicatestage"], "Known Stage")

    def test_enrollment_groups_collapse_merged_alias_video_counts_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            registry_path = root / "performer_verification.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "schema": "media-performer-verification/v1",
                        "performers": {
                            "gem-the-jewels": {
                                "name": "Gem The Jewels",
                                "slug": "gem-the-jewels",
                                "aliases": ["Alienland"],
                                "status": "user-confirmed",
                            }
                        },
                        "aliases": {"alienland": "Gem The Jewels"},
                    }
                ),
                encoding="utf-8",
            )
            (root / "model_index.json").write_text(
                json.dumps({"schema": "spiritflix-model-index/v1", "models": [{"name": "Gem The Jewels", "slug": "gem-the-jewels"}]}),
                encoding="utf-8",
            )
            for name, suggested in [("a.mp4", "Alienland"), ("b.mp4", "Gem The Jewels")]:
                video = root / name
                video.write_bytes(b"video")
                (root / f"{name}.face-meta.json").write_text(
                    json.dumps(
                        {
                            "schema": "media-face-organizer/v1",
                            "video_path": str(video),
                            "assignment_decision": {"suggested_name": suggested, "review_required": True},
                            "verification_needed": True,
                        }
                    ),
                    encoding="utf-8",
                )
            config = make_test_config(root, registry_path)

            payload = fo.build_enrollment_groups(config)
            groups = {group["name"]: group for group in payload["groups"]}

        self.assertNotIn("Alienland", groups)
        self.assertEqual(groups["Gem The Jewels"]["candidate_videos"], 2)

    def test_enrollment_queue_excludes_enrolled_and_enrolled_page_shows_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            registry_path = root / "performer_verification.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "schema": "media-performer-verification/v1",
                        "performers": {
                            "public-stage": {"name": "Public Stage", "slug": "public-stage", "status": "user-confirmed"}
                        },
                        "aliases": {},
                    }
                ),
                encoding="utf-8",
            )
            (root / "model_index.json").write_text(
                json.dumps({"schema": "spiritflix-model-index/v1", "models": [{"name": "Public Stage", "slug": "public-stage"}]}),
                encoding="utf-8",
            )
            config = make_test_config(root, registry_path)
            db = fo.KnownPerformersDB(config.db_dir)
            db.ensure()
            performer_id = db.add_performer("Public Stage")
            sample_paths = []
            for index in range(5):
                sample = config.db_dir / "faces" / performer_id / f"sample-{index}.jpg"
                sample.parent.mkdir(parents=True, exist_ok=True)
                sample.write_bytes(b"sample")
                sample_paths.append(str(sample))
                db.append_embedding(performer_id, fo.np.ones(512, dtype=fo.np.float32) * (index + 1))
            db.record_enrollment(performer_id, Path(sample_paths[-1]), confirmed_by="Britton")

            fo.generate_enrollment_queue_page(config)
            fo.generate_enrolled_page(config)
            queue_html = config.report_path.with_name("face_enrollment_queue.html").read_text(encoding="utf-8")
            enrolled_html = config.report_path.with_name("face_enrolled_performers.html").read_text(encoding="utf-8")
            enrolled_json = json.loads(config.report_path.with_name("face_enrolled_performers.json").read_text(encoding="utf-8"))

        self.assertNotIn("<h2>Public Stage</h2>", queue_html)
        self.assertIn("<h2>Public Stage</h2>", enrolled_html)
        self.assertEqual(enrolled_json["summary"]["ready_with_five_screens"], 1)
        self.assertEqual(enrolled_json["summary"]["enrolled_performers"], 1)

    def test_gallery_upload_for_enrolled_model_writes_index_and_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            registry_path = root / "performer_verification.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "schema": "media-performer-verification/v1",
                        "performers": {
                            "public-stage": {"name": "Public Stage", "slug": "public-stage", "status": "user-confirmed"}
                        },
                        "aliases": {},
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, registry_path)
            db = fo.KnownPerformersDB(config.db_dir)
            db.ensure()
            performer_id = db.add_performer("Public Stage")
            db.append_embedding(performer_id, fo.np.ones(512, dtype=fo.np.float32))

            result = fo.save_gallery_uploads(
                config,
                {"performer_name": "Public Stage", "collection": "Launch Set"},
                [{"filename": "pose.jpg", "content_type": "image/jpeg", "content": b"fake image bytes"}],
            )
            fo.generate_enrolled_page(config)
            fo.generate_gallery_page(config)
            gallery_json = json.loads(config.report_path.with_name("face_gallery.json").read_text(encoding="utf-8"))
            gallery_html = config.report_path.with_name("face_gallery.html").read_text(encoding="utf-8")
            enrolled_html = config.report_path.with_name("face_enrolled_performers.html").read_text(encoding="utf-8")

        self.assertEqual(result["saved_count"], 1)
        self.assertEqual(gallery_json["summary"]["gallery_items"], 1)
        self.assertEqual(gallery_json["items"][0]["model_name"], "Public Stage")
        self.assertEqual(gallery_json["items"][0]["collection"], "Launch Set")
        self.assertIn("/model_gallery/public-stage/", "/" + gallery_json["items"][0]["url"])
        self.assertIn("Gallery Upload", gallery_html)
        self.assertIn("Launch Set", gallery_html)
        self.assertIn("Gallery pictures (1)", enrolled_html)

    def test_model_video_ledger_names_sava_count_types_and_evidence_buckets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            model_dir = root / "models" / "sava-schultz"
            model_dir.mkdir(parents=True)
            registry_path = root / "performer_verification.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "schema": "media-performer-verification/v1",
                        "performers": {
                            "sava-schultz": {"name": "Sava Schultz", "slug": "sava-schultz", "status": "user-confirmed"}
                        },
                        "aliases": {},
                    }
                ),
                encoding="utf-8",
            )
            face_rec_video = model_dir / "(19).mkv"
            model_unknown_video = model_dir / "(116).mkv"
            ocr_video = root / "6513.mp4"
            for video in (face_rec_video, model_unknown_video, ocr_video):
                video.write_bytes(b"video")
            (root / "6513.mp4.face-meta.json").write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(ocr_video),
                        "verification_needed": True,
                        "faces_detected": 11,
                        "performers": [{"name": "unknown performer", "confidence": 0.4608, "similarity": 0.4608, "status": "unknown"}],
                        "metadata_hints": {
                            "candidate_names": [
                                {
                                    "name": "Sava Schultz",
                                    "source": "watermark_ocr",
                                    "confidence": 0.87,
                                    "raw": ".com/savaschultz",
                                    "evidence_role": "ocr_handle",
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            (model_dir / "(19).mkv.face-meta.json").write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(face_rec_video),
                        "verification_needed": False,
                        "faces_detected": 4,
                        "performers": [
                            {
                                "id": "sava-schultz",
                                "name": "Sava Schultz",
                                "confidence": 0.91,
                                "similarity": 0.91,
                                "status": "auto",
                                "supporting_faces": 2,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (model_dir / "(116).mkv.face-meta.json").write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(model_unknown_video),
                        "verification_needed": True,
                        "faces_detected": 0,
                        "performers": [{"name": "unknown performer", "confidence": 0, "similarity": 0, "status": "unknown"}],
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, registry_path)
            generated_group = {
                "name": "Sava Schultz",
                "known_performer_id": "sava-schultz",
                "embedding_rows": [0, 1],
                "records": [
                    {"video_path": "/DATA/yes/6513.mp4"},
                    {"video_path": "/mnt/spirit-8tb/media/yes/6513.mp4"},
                    {"video_path": str(model_unknown_video)},
                    {"video_path": str(face_rec_video)},
                ],
                "library_video_matches": [{"video_path": str(face_rec_video), "resolved_video_path": str(face_rec_video)}],
            }

            ledger = fo.build_model_video_ledger(config, "Sava Schultz", "sava-schultz", generated_group=generated_group)
            rows = {row["basename"]: row for row in ledger["rows"]}

        self.assertEqual(ledger["schema"], "media-model-video-ledger/v1")
        self.assertEqual(ledger["count_types"]["source_files_count"], 3)
        self.assertEqual(ledger["count_types"]["model_folder_files_count"], 2)
        self.assertEqual(ledger["count_types"]["enrolled_accepted_screen_count"], 2)
        self.assertEqual(ledger["count_types"]["face_rec_supported_video_count"], 1)
        self.assertEqual(ledger["count_types"]["metadata_manual_only_video_count"], 2)
        self.assertEqual(sum(1 for row in ledger["rows"] if row["basename"] == "6513.mp4"), 1)
        self.assertTrue(rows["6513.mp4"]["organizer_visible"])
        self.assertEqual(rows["6513.mp4"]["match_evidence_type"], "ocr_only")
        self.assertEqual(rows["6513.mp4"]["match_state"], "needs_review")
        self.assertEqual(rows["6513.mp4"]["best_similarity"], 0.4608)
        self.assertEqual(rows["(19).mkv"]["match_evidence_type"], "face_rec")
        self.assertNotIn("model_folder_not_face_rec_supported", rows["(19).mkv"]["sync_mismatch_reasons"])
        self.assertEqual(rows["(116).mkv"]["match_evidence_type"], "metadata_only")
        self.assertIn("organizer_library_bucket_missing", rows["(116).mkv"]["sync_mismatch_reasons"])
        self.assertIn("model_folder_not_face_rec_supported", rows["(116).mkv"]["sync_mismatch_reasons"])
        self.assertIn("spiritflix_face_metadata_api", ledger["consumer_map"])

    def test_phase2_sava_crud_sync_contract_names_layers_backups_receipts_and_gates(self) -> None:
        contract = fo.phase2_sava_crud_sync_contract()

        self.assertEqual(contract["scope"], "sava-only")
        self.assertEqual(contract["performer_id"], "sava-schultz")
        self.assertIn("do_not_generalize_to_all_models", contract["non_goals"])
        self.assertIn("do_not_reset_sava_accepted_screens", contract["non_goals"])
        self.assertEqual(contract["6513_honesty_rule"]["current_bucket"], "ocr_only")
        self.assertEqual(contract["6513_honesty_rule"]["current_state"], "needs_review")
        self.assertEqual(contract["6513_honesty_rule"]["current_best_similarity"], 0.4608)
        self.assertIn("similarity >= 0.80", contract["6513_honesty_rule"]["rule"])

        required_actions = {
            "accept_recommended_screen",
            "reject_recommended_screen",
            "remove_accepted_screen",
            "confirm_video_match",
            "deny_video_match",
            "mark_video_faceless",
            "mark_creator_faceless",
            "rescan_sava_model",
            "sync_3001",
        }
        self.assertEqual(set(contract["action_layers"]), required_actions)
        for action in required_actions:
            item = contract["action_layers"][action]
            self.assertTrue(item["handler"])
            self.assertTrue(item["ledger_row_lookup"])
            self.assertTrue(item["updates_layers"])
            self.assertTrue(item["required_backup"])
            self.assertTrue(item["required_receipt"])
            self.assertTrue(item["post_checks"])

        self.assertIn("sidecar_path", contract["ledger_to_handler_mapping"])
        self.assertIn("match_evidence_type", contract["ledger_to_handler_mapping"])
        self.assertIn("faceless_video", contract["ledger_to_handler_mapping"])
        self.assertIn("faceless_creator", contract["ledger_to_handler_mapping"])
        self.assertTrue(any("/tmp/spiritos-spiritflix-stable-3001" in step for step in contract["refresh_3001_contract"]))
        self.assertTrue(any("verify http://10.0.0.186:3001/spiritflix" in step for step in contract["refresh_3001_contract"]))
        self.assertEqual(contract["faceless_state_contract"]["video"]["field"], "faceless_video")
        self.assertEqual(contract["faceless_state_contract"]["creator"]["field"], "faceless_creator")
        self.assertTrue(any("Sava ledger builds" in check for check in contract["phase3_preflight_checks"]))
        self.assertTrue(any("unit tests pass" in check for check in contract["phase3_preflight_checks"]))

    def test_phase2_sava_only_guard_rejects_other_models(self) -> None:
        self.assertTrue(fo.sava_only_guard("Sava Schultz", "sava-schultz")["allowed"])
        blocked = fo.sava_only_guard("Aaliyah Yasan", "aaliyah-yasan")
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["scope"], "sava-only")
        self.assertIn("Sava Schultz", blocked["reject_reason"])

    def test_phase3_sava_backup_manifest_captures_state_before_reset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            registry_path = root / "performer_verification.json"
            config = make_test_config(root, registry_path)
            model_dir = root / "models" / "sava-schultz"
            model_dir.mkdir(parents=True)
            video = model_dir / "(19).mkv"
            video.write_bytes(b"video")
            receipt = model_dir / "(19).mkv.media-ingest.json"
            receipt.write_text(json.dumps({"finalPath": str(video)}), encoding="utf-8")
            sidecar = model_dir / "(19).mkv.face-meta.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(video),
                        "verification_needed": False,
                        "performers": [
                            {
                                "id": "sava-schultz",
                                "name": "Sava Schultz",
                                "similarity": 0.91,
                                "confidence": 0.91,
                                "status": "auto",
                                "supporting_faces": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            registry_path.write_text(
                json.dumps(
                    {
                        "schema": "media-performer-verification/v1",
                        "performers": {"sava-schultz": {"name": "Sava Schultz", "slug": "sava-schultz"}},
                        "aliases": {},
                    }
                ),
                encoding="utf-8",
            )
            (root / "model_index.json").write_text(
                json.dumps({"schema": "spiritflix-model-index/v1", "models": [{"name": "Sava Schultz", "slug": "sava-schultz"}]}),
                encoding="utf-8",
            )
            db = fo.KnownPerformersDB(config.db_dir)
            db.ensure()
            performer_id = db.add_performer("Sava Schultz")
            sample = config.db_dir / "faces" / performer_id / "sample.jpg"
            sample.parent.mkdir(parents=True, exist_ok=True)
            sample.write_bytes(b"sample")
            row = db.append_embedding(performer_id, fo.np.ones(512, dtype=fo.np.float32))
            db.record_enrollment(performer_id, sample, confirmed_by="Britton", source_video=str(video), embedding_rows=[row])
            enrolled_payload = {
                "schema": "media-face-enrolled-performers/v1",
                "groups": [
                    {
                        "name": "Sava Schultz",
                        "slug": "sava-schultz",
                        "candidate_videos": 1,
                        "embedding_rows": [row],
                        "records": [{"video_path": str(video)}],
                        "library_video_matches": [{"video_path": str(video), "resolved_video_path": str(video)}],
                        "recommended_crops": [],
                        "recommended_stills": [],
                    }
                ],
            }
            config.report_path.with_name("face_enrolled_performers.json").write_text(json.dumps(enrolled_payload), encoding="utf-8")

            manifest = fo.phase3_backup_sava_current_state(config)
            backup_root = Path(manifest["backup_root"])
            self.assertEqual(manifest["schema"], "media-face-organizer-phase3-sava-backup/v1")
            self.assertFalse(manifest["reset_performed"])
            self.assertTrue(manifest["stop_before_reset_required"])
            self.assertEqual(manifest["pre_reset_counts"]["sava_accepted_sample_records"], 1)
            self.assertEqual(manifest["pre_reset_counts"]["sava_embedding_rows"], [0])
            self.assertTrue((backup_root / "backup_manifest.json").exists())
            self.assertTrue((backup_root / "sava_enrolled_group.json").exists())
            self.assertTrue((backup_root / "sava_known_sample_records.json").exists())
            self.assertTrue((backup_root / "sava_source_of_truth_ledger.json").exists())
            backed_up_types = {item["type"] for item in manifest["files"]}
            self.assertIn("state", backed_up_types)
            self.assertIn("sidecars", backed_up_types)
            self.assertIn("media_ingest_receipts", backed_up_types)
            self.assertIn("artifacts", backed_up_types)

    def test_phase3_sava_reset_removes_stale_samples_and_orphan_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            db_dir = root / "known_performers"
            faces_dir = db_dir / "faces" / "sava-schultz"
            faces_dir.mkdir(parents=True)
            stale_sample = faces_dir / "stale.jpg"
            current_sample = faces_dir / "current.jpg"
            stale_sample.write_bytes(b"stale")
            current_sample.write_bytes(b"current")
            current_video = root / "models" / "sava-schultz" / "current.mkv"
            current_video.parent.mkdir(parents=True)
            current_video.write_bytes(b"video")
            index = {
                "performers": [
                    {
                        "id": "sava-schultz",
                        "name": "Sava Schultz",
                        "enrolled_face_samples": [str(stale_sample), str(current_sample)],
                        "enrolled_face_sample_records": [
                            {
                                "sample_path": str(stale_sample),
                                "source_crop": str(root / ".face-review" / "missing.jpg"),
                                "source_video": str(root / "models" / "sava-schultz" / "missing.mp4"),
                                "embedding_rows": [1],
                            },
                            {
                                "sample_path": str(current_sample),
                                "source_crop": str(current_sample),
                                "source_video": str(current_video),
                                "embedding_rows": [2],
                            },
                        ],
                    }
                ]
            }
            fo.json_dump(db_dir / "index.json", index)
            fo.json_dump(db_dir / "performer_map.json", {"0": "sava-schultz", "1": "sava-schultz", "2": "sava-schultz"})
            fo.np.save(db_dir / "embeddings.npy", fo.np.ones((3, 512), dtype=fo.np.float32))
            registry_path = root / "performer_verification.json"
            registry_path.write_text(
                json.dumps({"performers": {"sava-schultz": {"name": "Sava Schultz", "slug": "sava-schultz"}}, "aliases": {}}),
                encoding="utf-8",
            )
            backup_root = root / "backup"
            backup_root.mkdir()
            config = dataclasses.replace(make_test_config(root, registry_path), db_dir=db_dir, apply=True)

            receipt = fo.phase3_reset_sava_stale_samples(config, backup_root=backup_root)
            after = fo.known_db_summary(db_dir)

        self.assertEqual(receipt["before"]["accepted_sample_count"], 2)
        self.assertEqual(receipt["after"]["accepted_sample_count"], 1)
        self.assertEqual(len(receipt["removed_samples"]), 1)
        self.assertEqual(receipt["orphan_embedding_rows_removed"], [0])
        self.assertEqual(receipt["after"]["sava_embedding_rows"], [0])
        self.assertEqual(int(after["embedding_rows"]), 1)

    def test_phase3_sava_uncertain_queue_keeps_only_review_band(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            backup_root = root / "phase3"
            backup_root.mkdir()
            (backup_root / "phase3_sava_bounded_rescan_receipt.json").write_text(
                json.dumps(
                    {
                        "results": [
                            {"video_path": str(root / "a.mkv"), "status": "review_match", "best_similarity": 0.62, "supporting_faces": 2, "faces_detected": 3},
                            {"video_path": str(root / "b.mkv"), "status": "review_match", "best_similarity": 0.7592, "supporting_faces": 4, "faces_detected": 4},
                            {"video_path": str(root / "c.mkv"), "status": "no_match", "best_similarity": 0.49, "faces_detected": 5},
                            {"video_path": str(root / "d.mkv"), "status": "faceless_no_face", "best_similarity": 0.0, "faces_detected": 0},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, root / "performer_verification.json")

            receipt = fo.phase3_sava_queue_uncertain_matches(config, backup_root=backup_root)

        self.assertEqual(receipt["schema"], "media-face-organizer-phase3-sava-uncertain-queue/v1")
        self.assertEqual(receipt["counts"]["queued_needs_confirmation"], 1)
        self.assertEqual(receipt["counts"]["above_queue_band"], 1)
        self.assertEqual(receipt["counts"]["hidden_low_confidence"], 1)
        self.assertEqual(receipt["counts"]["faceless_no_face"], 1)
        self.assertEqual(receipt["queued_needs_confirmation"][0]["similarity"], 0.62)

    def test_phase3_sava_6513_bucket_closeout_remains_unknown_without_sava_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            backup_root = root / "phase3"
            backup_root.mkdir()
            video = root / "6513.mp4"
            video.write_bytes(b"video")
            (root / "6513.mp4.face-meta.json").write_text(
                json.dumps(
                    {
                        "schema": "media-face-organizer/v1",
                        "video_path": str(video),
                        "generated_at": "2026-06-14T16:47:42+00:00",
                        "frames_analyzed": 12,
                        "faces_detected": 10,
                        "performers": [{"name": "unknown performer", "similarity": 0.4523, "confidence": 0.4523, "status": "unknown"}],
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, root / "performer_verification.json")
            generated_group = {
                "name": "Sava Schultz",
                "known_performer_id": "sava-schultz",
                "records": [{"video_path": str(video)}],
            }
            config.report_path.with_name("face_enrolled_performers.json").write_text(
                json.dumps({"groups": [generated_group]}),
                encoding="utf-8",
            )

            receipt = fo.phase3_sava_6513_bucket_closeout(config, backup_root=backup_root)

        self.assertEqual(receipt["schema"], "media-face-organizer-phase3-sava-6513-bucket-closeout/v1")
        self.assertEqual(receipt["final_bucket"], "unknown")
        self.assertFalse(receipt["sava_face_rec_confirmed"])
        self.assertEqual(receipt["ledger_row"]["basename"], "6513.mp4")

    def test_video_match_decision_resolves_cross_host_sidecar_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Sava Schultz sample.mp4"
            video.write_bytes(b"video")
            sidecar = root / "Sava Schultz sample.mp4.face-meta.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "performers": [
                            {
                                "id": "sava-schultz",
                                "name": "Sava Schultz",
                                "similarity": 0.76,
                                "confidence": 0.76,
                                "status": "possible",
                                "verification_needed": True,
                                "supporting_faces": 2,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            registry_path = root / "performer_verification.json"
            registry_path.write_text(json.dumps({"performers": {}, "aliases": {}}), encoding="utf-8")
            config = dataclasses.replace(make_test_config(root, registry_path), apply=True)
            meta_text = "M:/yes/Sava Schultz sample.mp4.face-meta.json"

            result = fo.set_enrolled_video_match_decision(
                config,
                {
                    "performer_name": "Sava Schultz",
                    "performer_id": "sava-schultz",
                    "meta_path": meta_text,
                    "decision": "accepted",
                    "visual_confirmed": True,
                },
            )

        self.assertEqual(result["decision"], "accepted")
        self.assertTrue(result["applied"])

    def test_mark_video_faceless_sets_sidecar_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "faceless.mkv"
            video.write_bytes(b"video")
            sidecar = root / "faceless.mkv.face-meta.json"
            sidecar.write_text(json.dumps({"video_path": str(video), "performers": []}), encoding="utf-8")
            config = dataclasses.replace(make_test_config(root, root / "performer_verification.json"), apply=True)

            result = fo.mark_video_faceless(config, {"meta_path": str(sidecar), "performer_name": "Sava Schultz"})
            updated = json.loads(sidecar.read_text(encoding="utf-8"))

        self.assertTrue(result["applied"])
        self.assertTrue(updated["faceless_video"])
        self.assertFalse(updated["verification_needed"])

    def test_faceless_video_is_not_pending_enrolled_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Sava Schultz faceless.mkv"
            video.write_bytes(b"video")
            sidecar = root / "Sava Schultz faceless.mkv.face-meta.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "faceless_video": True,
                        "metadata_hints": {"candidate_names": [{"name": "Sava Schultz", "source": "filename", "confidence": 0.74}]},
                        "performers": [],
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, root / "performer_verification.json")

            matches = fo.enrolled_video_matches(config, {"name": "Sava Schultz", "known_performer_id": "sava-schultz"})

        self.assertEqual(matches["pending"], [])

    def test_unknown_model_record_stays_in_verification_queue_until_left_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "unknown-model.mkv"
            video.write_bytes(b"video")
            sidecar = video.with_name(f"{video.name}.face-meta.json")
            sidecar.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "verification_needed": False,
                        "performers": [{"name": "unknown performer", "status": "unknown", "verification_needed": True}],
                        "review_frames": [],
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, root / "performer_verification.json")

            fo.generate_report(config)
            html_before = config.report_path.read_text(encoding="utf-8")
            event = fo.mark_video_left_unknown(dataclasses.replace(config, apply=True), sidecar, confirmed_by="Britton")
            fo.generate_report(config)
            html_after = config.report_path.read_text(encoding="utf-8")
            updated = json.loads(sidecar.read_text(encoding="utf-8"))

        self.assertEqual(event["event"], "video_left_unknown")
        self.assertIn("unknown-model.mkv", html_before)
        self.assertNotIn("unknown-model.mkv", html_after)
        self.assertFalse(updated["verification_needed"])
        self.assertTrue(updated["left_unknown_decision"])

    def test_sidecarless_video_is_in_verification_queue_as_unscanned_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Unknown Model Upload.mp4"
            video.write_bytes(b"video")
            config = make_test_config(root, root / "performer_verification.json")

            records = fo.verification_queue_records(config)
            fo.generate_report(config)
            html = config.report_path.read_text(encoding="utf-8")

        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]["unscanned"])
        self.assertEqual(records[0]["_meta_path"], str(fo.meta_path_for(video)))
        self.assertIn("Unknown Model Upload.mp4", html)
        self.assertIn("Video has not been face-scanned yet", html)
        self.assertIn("Leave unknown", html)

    def test_unknown_folder_sidecarless_video_is_in_verification_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            unknown_dir = root / "unknown"
            unknown_dir.mkdir()
            video = unknown_dir / "Unknown Folder Upload.mp4"
            video.write_bytes(b"video")
            config = make_test_config(root, root / "performer_verification.json")

            records = fo.verification_queue_records(config)

        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]["unscanned"])
        self.assertEqual(records[0]["video_path"], str(video))

    def test_unscanned_unknown_preview_frames_are_saved_when_apply_is_enabled(self) -> None:
        def fake_extract_preview_frames(video_path: Path, review_dir: Path, frame_count: int) -> list[Path]:
            paths = []
            for index in range(1, frame_count + 1):
                review_dir.mkdir(parents=True, exist_ok=True)
                frame = review_dir / f"unscanned-preview-{index:02d}.jpg"
                frame.write_bytes(b"fake-jpeg")
                paths.append(frame)
            return paths

        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Unknown Model Upload.mp4"
            video.write_bytes(b"video")
            config = dataclasses.replace(make_test_config(root, root / "performer_verification.json"), apply=True)

            with patch.object(fo, "extract_unscanned_preview_frames", side_effect=fake_extract_preview_frames):
                records = fo.verification_queue_records(config)

            frame_paths = [Path(item) for item in records[0]["review_frames"]]
            self.assertEqual(len(frame_paths), 2)
            self.assertTrue(all(path.name.startswith("unscanned-preview-") for path in frame_paths))
            self.assertTrue(all(path.exists() for path in frame_paths))

    def test_metadata_only_video_match_accept_creates_manual_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Sava Schultz grinding BBC so lewd leak.mkv"
            video.write_bytes(b"video")
            sidecar = root / "Sava Schultz grinding BBC so lewd leak.mkv.face-meta.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "metadata_hints": {"candidate_names": [{"name": "Sava Schultz", "source": "filename", "confidence": 0.65}]},
                        "performers": [{"name": "unknown performer", "similarity": 0.2, "status": "unknown", "verification_needed": True}],
                    }
                ),
                encoding="utf-8",
            )
            registry_path = root / "performer_verification.json"
            registry_path.write_text(json.dumps({"performers": {}, "aliases": {}}), encoding="utf-8")
            config = dataclasses.replace(make_test_config(root, registry_path), apply=True)

            result = fo.set_enrolled_video_match_decision(
                config,
                {
                    "performer_name": "Sava Schultz",
                    "performer_id": "sava-schultz",
                    "meta_path": str(sidecar),
                    "decision": "accepted",
                    "visual_confirmed": True,
                },
            )
            updated = json.loads(sidecar.read_text(encoding="utf-8"))
            with patch.object(
                fo,
                "latest_sava_uncertain_queue_receipt",
                return_value={
                    "queued_needs_confirmation": [
                        {"video_path": str(video), "sidecar_path": str(sidecar), "similarity": 0.65, "supporting_faces": 0}
                    ]
                },
            ):
                matches = fo.enrolled_video_matches(config, {"name": "Sava Schultz", "known_performer_id": "sava-schultz"})

        self.assertTrue(result["applied"])
        self.assertEqual(updated["face_match_decisions"][-1]["match_evidence_type"], "metadata_only")
        self.assertTrue(any(item.get("status") == "manual-confirmed" for item in updated["performers"]))
        self.assertEqual(matches["pending"], [])
        self.assertEqual(matches["auto"][0]["kind"], "accepted_manual")
        self.assertFalse(matches["auto"][0]["has_face_evidence"])

    def test_accepted_manual_video_match_renders_as_confirmed_not_actionable(self) -> None:
        html = fo.render_enrolled_video_matches(
            {
                "name": "Sava Schultz",
                "known_performer_id": "sava-schultz",
                "auto_video_matches": [
                    {
                        "kind": "accepted_manual",
                        "video_name": "Sava Schultz grinding BBC so lewd leak.mp4",
                        "confidence": 0.65,
                        "confidence_percent": 65,
                        "has_face_evidence": False,
                        "supporting_faces": 0,
                        "preview_paths": [],
                    }
                ],
                "pending_video_matches": [],
                "library_video_matches": [],
                "missing_video_matches": [],
                "source_of_truth_ledger": {"rows": []},
            }
        )

        self.assertIn("Video match review (0 need action", html)
        self.assertIn("Confirmed outside-library matches", html)
        self.assertIn("manually confirmed metadata/title match", html)
        self.assertNotIn("Confirm video", html)

    def test_scan_sidecar_write_preserves_user_video_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            sidecar = root / "Sava Schultz sample.mkv.face-meta.json"
            existing = {
                "video_path": str(root / "Sava Schultz sample.mkv"),
                "faceless_video": True,
                "faceless_video_decisions": [{"event": "video_marked_faceless"}],
                "face_match_decisions": [
                    {
                        "decision": "accepted",
                        "performer_name": "Sava Schultz",
                        "performer_id": "sava-schultz",
                        "visual_confirmed": True,
                        "match_evidence_type": "metadata_only",
                    }
                ],
                "performers": [
                    {
                        "name": "Sava Schultz",
                        "id": "sava-schultz",
                        "status": "manual-confirmed",
                        "verification_needed": False,
                    }
                ],
            }
            fresh = {
                "video_path": str(root / "Sava Schultz sample.mkv"),
                "verification_needed": True,
                "performers": [{"name": "unknown performer", "status": "unknown", "verification_needed": True}],
            }
            sidecar.write_text(json.dumps(existing), encoding="utf-8")

            merged = fo.write_scan_sidecar(sidecar, fresh)
            updated = json.loads(sidecar.read_text(encoding="utf-8"))

        self.assertTrue(merged["faceless_video"])
        self.assertFalse(merged["verification_needed"])
        self.assertEqual(updated["face_match_decisions"][0]["decision"], "accepted")
        self.assertTrue(any(item.get("status") == "manual-confirmed" for item in updated["performers"]))

    def test_enrolled_model_scan_videos_includes_filename_hint_uploads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Sava.schultz Horny Tease OnlyFans.mp4"
            video.write_bytes(b"video")
            config = make_test_config(root, root / "performer_verification.json")

            videos = fo.enrolled_model_scan_videos(config, "Sava Schultz", "sava-schultz")

        self.assertEqual(videos, [video])

    def test_enrolled_model_scan_videos_includes_non_sava_filename_hint_uploads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Jane Doe new upload.mp4"
            video.write_bytes(b"video")
            config = make_test_config(root, root / "performer_verification.json")

            videos = fo.enrolled_model_scan_videos(config, "Jane Doe", "jane-doe")

        self.assertEqual(videos, [video])

    def test_enrolled_model_scan_videos_prioritizes_unscanned_new_uploads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            old_video = root / "Sava Schultz old.mp4"
            new_video = root / "Sava Schultz new.mp4"
            old_video.write_bytes(b"old")
            new_video.write_bytes(b"new")
            fo.json_dump(fo.meta_path_for(old_video), {"video_path": str(old_video), "performers": []})
            config = make_test_config(root, root / "performer_verification.json")

            videos = fo.enrolled_model_scan_videos(config, "Sava Schultz", "sava-schultz")

        self.assertEqual(videos[0], new_video)
        self.assertIn(old_video, videos)

    def test_metadata_dedupe_prefers_exact_sidecar_with_user_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Sava Schultz grinding BBC so lewd leak.mp4"
            video.write_bytes(b"video")
            stale = root / "Sava Schultz grinding BBC so lewd leak.mkv.face-meta.json"
            exact = root / "Sava Schultz grinding BBC so lewd leak.mp4.face-meta.json"
            stale.write_text(
                json.dumps(
                    {
                        "video_path": str(root / "Sava Schultz grinding BBC so lewd leak.mkv"),
                        "performers": [{"name": "unknown performer", "supporting_faces": 10, "status": "unknown"}],
                        "metadata_hints": {"candidate_names": [{"name": "Sava Schultz", "source": "filename", "confidence": 0.65}]},
                    }
                ),
                encoding="utf-8",
            )
            exact.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "face_match_decisions": [{"decision": "accepted", "performer_name": "Sava Schultz", "performer_id": "sava-schultz"}],
                        "performers": [{"name": "Sava Schultz", "id": "sava-schultz", "status": "manual-confirmed", "verification_needed": False}],
                    }
                ),
                encoding="utf-8",
            )

            records = fo.collect_metadata(root, True)

        grinding = [record for record in records if "grinding BBC" in str(record.get("video_path"))]
        self.assertEqual(len(grinding), 1)
        self.assertEqual(Path(grinding[0]["_meta_path"]), exact)
        self.assertEqual(grinding[0]["face_match_decisions"][0]["decision"], "accepted")

    def test_sava_queue_receipt_does_not_readd_current_library_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "models" / "sava-schultz" / "(19).mkv"
            video.parent.mkdir(parents=True)
            video.write_bytes(b"video")
            sidecar = video.with_name(f"{video.name}.face-meta.json")
            sidecar.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "performers": [
                            {
                                "name": "Sava Schultz",
                                "id": "sava-schultz",
                                "similarity": 0.63,
                                "confidence": 0.63,
                                "status": "possible",
                                "verification_needed": True,
                                "supporting_faces": 7,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, root / "performer_verification.json")

            with patch.object(
                fo,
                "latest_sava_uncertain_queue_receipt",
                return_value={"queued_needs_confirmation": [{"video_path": str(video), "sidecar_path": str(sidecar), "similarity": 0.63, "supporting_faces": 7}]},
            ):
                matches = fo.enrolled_video_matches(config, {"name": "Sava Schultz", "known_performer_id": "sava-schultz"})

        self.assertEqual(len(matches["library"]), 1)
        self.assertEqual(matches["pending"], [])

    def test_deep_scan_enrolled_video_is_single_file_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Sava Schultz sample.mkv"
            video.write_bytes(b"video")
            sidecar = root / "Sava Schultz sample.mkv.face-meta.json"
            sidecar.write_text(json.dumps({"video_path": str(video), "performers": []}), encoding="utf-8")
            config = dataclasses.replace(make_test_config(root, root / "performer_verification.json"), apply=True)

            def fake_scan(video_path: Path, scan_config: fo.OrganizerConfig, db: object, recognizer: object) -> dict:
                self.assertEqual(video_path, video)
                self.assertEqual(scan_config.frame_count, fo.ENROLLMENT_SINGLE_VIDEO_DEEP_SCAN_FRAMES)
                return {
                    "video_path": str(video_path),
                    "frames_analyzed": scan_config.frame_count,
                    "faces_detected": 5,
                    "performers": [
                        {
                            "id": "sava-schultz",
                            "name": "Sava Schultz",
                            "similarity": 0.82,
                            "confidence": 0.82,
                            "status": "auto",
                            "supporting_faces": 4,
                        }
                    ],
                }

            with (
                patch.object(fo, "require_ffmpeg", return_value=None),
                patch.object(fo.KnownPerformersDB, "load", return_value=None),
                patch.object(fo, "InsightFaceRecognizer", return_value=object()),
                patch.object(fo, "scan_video", side_effect=fake_scan),
            ):
                result = fo.deep_scan_enrolled_video(
                    config,
                    {
                        "performer_name": "Sava Schultz",
                        "performer_id": "sava-schultz",
                        "meta_path": "M:/yes/Sava Schultz sample.mkv.face-meta.json",
                    },
                )

            updated = json.loads(sidecar.read_text(encoding="utf-8"))

        self.assertTrue(result["applied"])
        self.assertEqual(result["frames_analyzed"], fo.ENROLLMENT_SINGLE_VIDEO_DEEP_SCAN_FRAMES)
        self.assertEqual(result["supporting_faces"], 4)
        self.assertEqual(updated["faces_detected"], 5)

    def test_scan_single_video_scans_exact_upload_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "new-upload.mkv"
            sibling = root / "aaa-other.mkv"
            video.write_bytes(b"video")
            sibling.write_bytes(b"other")
            config = dataclasses.replace(make_test_config(root, root / "performer_verification.json"), apply=True)

            def fake_scan(video_path: Path, scan_config: fo.OrganizerConfig, db: object, recognizer: object) -> dict:
                self.assertEqual(video_path, video)
                self.assertEqual(scan_config.source_dir, root)
                return {
                    "video_path": str(video_path),
                    "frames_analyzed": 1,
                    "faces_detected": 0,
                    "performers": [{"name": "unknown performer", "status": "unknown", "verification_needed": True}],
                }

            with (
                patch.object(fo, "require_ffmpeg", return_value=None),
                patch.object(fo.KnownPerformersDB, "load", return_value=None),
                patch.object(fo, "InsightFaceRecognizer", return_value=object()),
                patch.object(fo, "scan_video", side_effect=fake_scan),
            ):
                result = fo.scan_single_video(config, video)
            video_sidecar_exists = fo.meta_path_for(video).exists()
            sibling_sidecar_exists = fo.meta_path_for(sibling).exists()

        self.assertEqual(result["video_path"], str(video))
        self.assertTrue(video_sidecar_exists)
        self.assertFalse(sibling_sidecar_exists)

    def test_metadata_only_sava_candidate_is_pending_video_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Sava Schultz title hit.mkv"
            video.write_bytes(b"video")
            sidecar = root / "Sava Schultz title hit.mkv.face-meta.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "metadata_hints": {
                            "candidate_names": [
                                {
                                    "name": "Sava Schultz",
                                    "source": "filename",
                                    "confidence": 0.7,
                                }
                            ]
                        },
                        "performers": [{"name": "unknown performer", "similarity": 0.32, "status": "unknown"}],
                        "review_frames": [str(root / ".face-review" / "frame-01.jpg")],
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, root / "performer_verification.json")

            matches = fo.enrolled_video_matches(
                config,
                {"name": "Sava Schultz", "known_performer_id": "sava-schultz"},
            )
            ledger = fo.build_model_video_ledger(config, "Sava Schultz", "sava-schultz")

        self.assertEqual(len(matches["pending"]), 1)
        self.assertEqual(matches["pending"][0]["kind"], "metadata_review")
        self.assertFalse(matches["pending"][0]["has_face_evidence"])
        row = next(item for item in ledger["rows"] if item["basename"] == video.name)
        self.assertEqual(row["match_evidence_type"], "metadata_only")
        self.assertTrue(row["needs_user_decision"])

    def test_no_face_evidence_performer_row_uses_metadata_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Sava.schultz Onlyfans Butt Slap Red Tease Video Leaked.mp4"
            video.write_bytes(b"video")
            sidecar = video.with_name(f"{video.name}.face-meta.json")
            sidecar.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "metadata_hints": {
                            "candidate_names": [
                                {
                                    "name": "Sava Schultz",
                                    "source": "filename",
                                    "confidence": 0.87,
                                }
                            ]
                        },
                        "performers": [
                            {
                                "id": "sava-schultz",
                                "name": "Sava Schultz",
                                "confidence": 0.87,
                                "similarity": 0.0,
                                "supporting_faces": 0,
                                "status": "auto",
                                "verification_needed": False,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, root / "performer_verification.json")

            matches = fo.enrolled_video_matches(
                config,
                {"name": "Sava Schultz", "known_performer_id": "sava-schultz"},
            )

        self.assertEqual(len(matches["pending"]), 1)
        self.assertEqual(matches["pending"][0]["kind"], "metadata_review")
        self.assertEqual(matches["pending"][0]["confidence"], 0.74)
        self.assertFalse(matches["pending"][0]["has_face_evidence"])

    def test_non_sava_no_face_evidence_preview_stays_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "Jane Doe teaser.mp4"
            video.write_bytes(b"video")
            sidecar = video.with_name(f"{video.name}.face-meta.json")
            sidecar.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "metadata_hints": {
                            "candidate_names": [
                                {
                                    "name": "Jane Doe",
                                    "source": "filename",
                                    "confidence": 0.82,
                                }
                            ]
                        },
                        "performers": [
                            {
                                "id": "jane-doe",
                                "name": "Jane Doe",
                                "confidence": 0.82,
                                "similarity": 0.0,
                                "supporting_faces": 0,
                                "status": "auto",
                                "verification_needed": False,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, root / "performer_verification.json")

            matches = fo.enrolled_video_matches(
                config,
                {"name": "Jane Doe", "known_performer_id": "jane-doe"},
            )
            html = fo.render_enrolled_video_matches(
                {
                    "name": "Jane Doe",
                    "known_performer_id": "jane-doe",
                    "pending_video_matches": matches["pending"],
                    "auto_video_matches": [],
                    "library_video_matches": [],
                    "missing_video_matches": [],
                    "source_of_truth_ledger": {"rows": []},
                }
            )

        self.assertEqual(len(matches["pending"]), 1)
        self.assertEqual(matches["pending"][0]["kind"], "metadata_review")
        self.assertFalse(matches["pending"][0]["has_face_evidence"])
        self.assertIn("metadata/title match; needs visual review", html)
        self.assertIn("no saved Jane Doe face-rec evidence", html)
        self.assertNotIn("Sava", html)

    def test_queue_video_match_record_resolves_sidecar_preview_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            video = root / "models" / "sava-schultz" / "(19).mkv"
            review = video.parent / ".face-review" / "(19)"
            review.mkdir(parents=True)
            video.write_bytes(b"video")
            crop = review / "frame-01-face-01.jpg"
            frame = review / "frame-01.jpg"
            crop.write_bytes(b"crop")
            frame.write_bytes(b"frame")
            sidecar = video.with_name(f"{video.name}.face-meta.json")
            sidecar.write_text(
                json.dumps(
                    {
                        "video_path": str(video),
                        "performers": [
                            {
                                "id": "sava-schultz",
                                "name": "Sava Schultz",
                                "similarity": 0.63,
                                "supporting_faces": 7,
                                "face_crop_path": str(crop),
                                "original_frame_path": str(frame),
                            }
                        ],
                        "review_frames": [str(frame)],
                    }
                ),
                encoding="utf-8",
            )
            config = make_test_config(root, root / "performer_verification.json")

            record = fo.queue_video_match_record(
                {
                    "video_path": "M:/yes/models/sava-schultz/(19).mkv",
                    "sidecar_path": "M:/yes/models/sava-schultz/(19).mkv.face-meta.json",
                    "similarity": 0.63,
                    "supporting_faces": 7,
                },
                kind="phase3_needs_confirmation",
                config=config,
            )

        self.assertEqual(record["meta_path"], str(sidecar))
        self.assertEqual(record["video_name"], "(19).mkv")
        self.assertGreaterEqual(len(record["preview_paths"]), 2)
        self.assertTrue(record["has_face_evidence"])

    def test_remove_candidate_crops_from_queue_prunes_accepted_recommendations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            config = dataclasses.replace(make_test_config(root, root / "performer_verification.json"), apply=True)
            candidate_dir = fo.enrollment_review_dir(config)
            crop_a = candidate_dir / "sava-schultz" / "a.jpg"
            crop_b = candidate_dir / "sava-schultz" / "b.jpg"
            still_a = candidate_dir / "sava-schultz" / "a-still.jpg"
            crop_a.parent.mkdir(parents=True)
            for path in (crop_a, crop_b, still_a):
                path.write_bytes(b"image")
            fo.json_dump(
                candidate_dir / "enrollment_candidates.json",
                {
                    "groups": [
                        {
                            "name": "Sava Schultz",
                            "slug": "sava-schultz",
                            "recommended_crops": [
                                {"crop_path": str(crop_a), "still_path": str(still_a)},
                                {"crop_path": str(crop_b), "still_path": str(candidate_dir / "b-still.jpg")},
                            ],
                            "recommended_stills": [{"still_path": str(still_a)}],
                        }
                    ]
                },
            )

            removed = fo.remove_candidate_crops_from_queue(config, "Sava Schultz", [str(crop_a)])
            updated = json.loads((candidate_dir / "enrollment_candidates.json").read_text(encoding="utf-8"))
            group = updated["groups"][0]

        self.assertEqual(removed, 1)
        self.assertEqual([item["crop_path"] for item in group["recommended_crops"]], [str(crop_b)])
        self.assertEqual(group["recommended_stills"], [])

    def test_smart_accept_uses_optimal_remaining_screen_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            config = dataclasses.replace(make_test_config(root, root / "performer_verification.json"), apply=True)
            db_dir = config.db_dir
            db_dir.mkdir(parents=True)
            existing_records = [{"sample_path": str(root / f"sample-{index}.jpg")} for index in range(8)]
            fo.json_dump(
                db_dir / "index.json",
                {"performers": [{"id": "sava-schultz", "name": "Sava Schultz", "enrolled_face_sample_records": existing_records}]},
            )
            fo.json_dump(db_dir / "performer_map.json", {})
            fo.np.save(db_dir / "embeddings.npy", fo.np.zeros((0, 512), dtype=fo.np.float32))
            candidate_dir = fo.enrollment_review_dir(config) / "sava-schultz"
            candidate_dir.mkdir(parents=True)
            crops = []
            for index in range(15):
                crop = candidate_dir / f"crop-{index}.jpg"
                crop.write_bytes(b"crop")
                crops.append(
                    {
                        "crop_path": str(crop),
                        "source_video": str(root / f"video-{index}.mkv"),
                        "quality_score": 1.0 - index / 100,
                        "detection_score": 0.99,
                    }
                )
            fo.json_dump(
                fo.enrollment_review_dir(config) / "enrollment_candidates.json",
                {"groups": [{"name": "Sava Schultz", "slug": "sava-schultz", "recommended_crops": crops}]},
            )

            with (
                patch.object(fo, "InsightFaceRecognizer", return_value=FakeRecognizer()),
                patch.object(fo, "rescan_unidentified_videos_after_enrollment", return_value={"scanned": 0, "matched_new_performer": 0}),
            ):
                result = fo.smart_accept_best_crops(
                    config,
                    {"performer_name": "Sava Schultz", "confirmation": "Sava Schultz"},
                )

        self.assertEqual(result["selection_count"], 12)
        self.assertEqual(len(result["enrollment"]["embedding_row_indexes_added"]), 12)

    def test_enrolled_groups_keep_recommendations_visible_after_optimal_screen_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            config = make_test_config(root, root / "performer_verification.json")
            samples = [str(root / f"accepted-{index}.jpg") for index in range(fo.ENROLLMENT_CONFIDENCE_MAX_TARGET_SCREENS)]
            stale_crop = {"crop_path": str(root / "stale-crop.jpg"), "source_video": str(root / "video.mkv")}
            stale_still = {"still_path": str(root / "stale-still.jpg"), "source_video": str(root / "video.mkv")}
            known_record = {
                "id": "sava-schultz",
                "name": "Sava Schultz",
                "enrolled_face_samples": samples,
            }
            group_payload = {
                "groups": [
                    {
                        "name": "Sava Schultz",
                        "slug": "sava-schultz",
                        "known_performer_id": "sava-schultz",
                        "embedding_rows": [0],
                        "recommended_crops": [stale_crop],
                        "recommended_stills": [stale_still],
                    }
                ]
            }

            with (
                patch.object(fo, "build_enrollment_groups", return_value=group_payload),
                patch.object(fo, "known_db_summary", return_value={"by_id": {"sava-schultz": known_record}}),
                patch.object(fo, "enrolled_video_matches", return_value={"library": [], "missing": [], "auto": [], "pending": []}),
                patch.object(fo, "build_model_video_ledger", return_value={}),
            ):
                result = fo.build_enrolled_groups(config)

        group = result["groups"][0]
        self.assertEqual(len(group["enrolled_samples"]), fo.ENROLLMENT_CONFIDENCE_MAX_TARGET_SCREENS)
        self.assertEqual(group["recommended_crops"], [stale_crop])
        self.assertEqual(group["recommended_stills"], [stale_still])
        self.assertEqual(result["summary"]["live_recommendations"], 1)


if __name__ == "__main__":
    unittest.main()
