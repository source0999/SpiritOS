from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from source_proxy.sandbox.bubblewrap import (
    BubblewrapConfig,
    build_bubblewrap_args,
    is_trusted_network_command,
    main,
    probe_home_is_hidden,
    probe_network_denied,
    probe_npm_registry_allowed,
)


class BubblewrapSandboxTests(unittest.TestCase):
    def test_args_hide_home_and_drop_capabilities(self) -> None:
        args = build_bubblewrap_args(["/bin/ls", "/home"])

        self.assertIn("--unshare-user", args)
        self.assertIn("--unshare-pid", args)
        self.assertIn("--unshare-net", args)
        self.assertIn("--cap-drop", args)
        self.assertIn("ALL", args)
        self.assertIn("/etc/resolv.conf", args)
        self.assertNotIn("/home", args[:-2])
        self.assertEqual(args[-2:], ["/bin/ls", "/home"])

    def test_args_bind_workspace_read_only_without_binding_host_home(self) -> None:
        args = build_bubblewrap_args(
            ["/bin/pwd"],
            BubblewrapConfig(workspace=Path.cwd()),
        )

        self.assertIn("--ro-bind", args)
        self.assertIn("/workspace", args)
        self.assertIn("--chdir", args)
        self.assertNotIn(str(Path.home()), args)

    def test_args_attach_seccomp_fd_when_supplied(self) -> None:
        args = build_bubblewrap_args(["/bin/true"], seccomp_fd=7)

        self.assertIn("--seccomp", args)
        seccomp_index = args.index("--seccomp")
        self.assertEqual(args[seccomp_index + 1], "7")

    def test_probe_home_success_requires_no_such_file_error(self) -> None:
        completed = Mock(
            returncode=2,
            stdout="",
            stderr="/bin/ls: cannot access '/home': No such file or directory\n",
        )
        with patch("source_proxy.sandbox.bubblewrap.run_bubblewrap", return_value=completed):
            payload = probe_home_is_hidden()

        self.assertTrue(payload["home_hidden"])
        self.assertEqual(payload["returncode"], 2)
        self.assertEqual(payload["status"], "completed")

    def test_probe_reports_uid_map_permission_as_setup_failure(self) -> None:
        completed = Mock(
            returncode=1,
            stdout="",
            stderr="bwrap: setting up uid map: Permission denied\n",
        )
        with patch("source_proxy.sandbox.bubblewrap.run_bubblewrap", return_value=completed):
            payload = probe_home_is_hidden()

        self.assertFalse(payload["home_hidden"])
        self.assertEqual(payload["status"], "setup_failed")
        self.assertEqual(payload["setup_error"], "uid_map_permission_denied")
        self.assertIn("user namespaces", payload["recommended_fix"])

    def test_trusted_network_policy_does_not_unshare_network(self) -> None:
        args = build_bubblewrap_args(
            ["/usr/bin/npm", "ping", "--registry", "https://registry.npmjs.org"],
            BubblewrapConfig(network_policy="trusted_command"),
        )

        self.assertNotIn("--unshare-net", args)

    def test_trusted_network_command_gate_allows_only_npm_registry_ping(self) -> None:
        self.assertTrue(
            is_trusted_network_command(
                ["/usr/bin/npm", "ping", "--registry", "https://registry.npmjs.org"]
            )
        )
        self.assertFalse(is_trusted_network_command(["/usr/bin/curl", "https://google.com"]))
        self.assertFalse(is_trusted_network_command(["/usr/bin/npm", "install"]))

    def test_probe_network_denied_reports_failed_curl_as_denied(self) -> None:
        completed = Mock(returncode=6, stdout="", stderr="curl: (6) Could not resolve host\n")
        with patch("source_proxy.sandbox.bubblewrap.run_bubblewrap", return_value=completed):
            payload = probe_network_denied()

        self.assertTrue(payload["network_denied"])
        self.assertEqual(payload["status"], "completed")

    def test_probe_network_denied_does_not_count_setup_failure_as_denied(self) -> None:
        completed = Mock(
            returncode=1,
            stdout="",
            stderr="bwrap: Can't read /proc/sys/kernel/overflowuid: Permission denied\n",
        )
        with patch("source_proxy.sandbox.bubblewrap.run_bubblewrap", return_value=completed):
            payload = probe_network_denied()

        self.assertFalse(payload["network_denied"])
        self.assertEqual(payload["status"], "setup_failed")
        self.assertEqual(payload["setup_error"], "apparmor_proc_sys_kernel_denied")

    def test_probe_network_denied_detects_apparmor_userns_denial(self) -> None:
        completed = Mock(
            returncode=1,
            stdout="",
            stderr="bwrap: Creating new namespace failed: Permission denied\n",
        )
        with patch("source_proxy.sandbox.bubblewrap.run_bubblewrap", return_value=completed):
            payload = probe_network_denied()

        self.assertFalse(payload["network_denied"])
        self.assertEqual(payload["status"], "setup_failed")
        self.assertEqual(payload["setup_error"], "apparmor_userns_denied")
        self.assertIn("user namespace", payload["recommended_fix"])

    def test_probe_network_denied_detects_apparmor_mount_setup_denial(self) -> None:
        completed = Mock(
            returncode=1,
            stdout="",
            stderr="bwrap: Failed to make / slave: Permission denied\n",
        )
        with patch("source_proxy.sandbox.bubblewrap.run_bubblewrap", return_value=completed):
            payload = probe_network_denied()

        self.assertFalse(payload["network_denied"])
        self.assertEqual(payload["status"], "setup_failed")
        self.assertEqual(payload["setup_error"], "apparmor_mount_setup_denied")

    def test_probe_network_denied_detects_apparmor_pivot_root_denial(self) -> None:
        completed = Mock(
            returncode=1,
            stdout="",
            stderr="bwrap: pivot root: Permission denied\n",
        )
        with patch("source_proxy.sandbox.bubblewrap.run_bubblewrap", return_value=completed):
            payload = probe_network_denied()

        self.assertFalse(payload["network_denied"])
        self.assertEqual(payload["status"], "setup_failed")
        self.assertEqual(payload["setup_error"], "apparmor_pivot_root_denied")

    def test_probe_network_denied_detects_proc_mountpoint_denial(self) -> None:
        completed = Mock(
            returncode=1,
            stdout="",
            stderr="bwrap: Can't mkdir /proc: Permission denied\n",
        )
        with patch("source_proxy.sandbox.bubblewrap.run_bubblewrap", return_value=completed):
            payload = probe_network_denied()

        self.assertFalse(payload["network_denied"])
        self.assertEqual(payload["status"], "setup_failed")
        self.assertEqual(payload["setup_error"], "apparmor_proc_mountpoint_denied")

    def test_probe_network_denied_detects_mountinfo_denial(self) -> None:
        completed = Mock(
            returncode=1,
            stdout="",
            stderr="bwrap: Can't open /proc/self/mountinfo: Permission denied\n",
        )
        with patch("source_proxy.sandbox.bubblewrap.run_bubblewrap", return_value=completed):
            payload = probe_network_denied()

        self.assertFalse(payload["network_denied"])
        self.assertEqual(payload["status"], "setup_failed")
        self.assertEqual(payload["setup_error"], "apparmor_mountinfo_denied")

    def test_probe_npm_registry_reports_allowlisted_success(self) -> None:
        completed = Mock(returncode=0, stdout="npm notice PING https://registry.npmjs.org\n", stderr="")
        with patch("source_proxy.sandbox.bubblewrap.run_bubblewrap", return_value=completed):
            payload = probe_npm_registry_allowed()

        self.assertTrue(payload["registry_allowed"])
        self.assertTrue(payload["trusted_command_gate"])

    def test_cli_probe_npm_registry_uses_trusted_network_policy(self) -> None:
        completed = Mock(returncode=0, stdout="npm notice PING https://registry.npmjs.org\n", stderr="")
        with (
            patch("sys.argv", ["bubblewrap.py", "probe-npm-registry"]),
            patch("source_proxy.sandbox.bubblewrap.run_bubblewrap", return_value=completed) as run,
            patch("builtins.print"),
        ):
            with self.assertRaises(SystemExit) as exit_context:
                main()

        self.assertEqual(exit_context.exception.code, 0)
        self.assertEqual(run.call_args.args[1].network_policy, "trusted_command")

    def test_apparmor_profile_allows_bubblewrap_setup_caps(self) -> None:
        profile = Path("config/source-bwrap.apparmor").read_text(encoding="utf-8")

        self.assertIn("userns,", profile)
        self.assertIn("capability,", profile)
        self.assertNotIn("deny capability sys_admin", profile)
        self.assertIn("owner /proc/*/uid_map rw,", profile)
        self.assertIn("owner /proc/*/gid_map rw,", profile)
        self.assertIn("owner /proc/*/setgroups rw,", profile)
        self.assertIn("mount,", profile)
        self.assertIn("pivot_root,", profile)
        self.assertIn("/ rw,", profile)
        self.assertIn("/proc rw,", profile)
        self.assertNotIn("owner /proc/** rw", profile)
        self.assertIn("owner /proc/*/fd/ r,", profile)
        self.assertIn("/proc/self/mountinfo r,", profile)
        self.assertIn("owner /proc/*/mountinfo r,", profile)
        self.assertIn("/newroot/proc/ rw,", profile)
        self.assertIn("/usr/bin/npm rix,", profile)
        self.assertIn("/usr/share/nodejs/npm/bin/npm-cli.js rix,", profile)
        self.assertIn("/usr/lib/node_modules/npm/bin/npm-cli.js rix,", profile)
        self.assertIn("/etc/resolv.conf r,", profile)
        self.assertIn("/usr/share/nodejs/** r,", profile)
        self.assertIn("/newroot/** rwkl,", profile)
        self.assertNotIn("rwklc", profile)
        self.assertIn("mount fstype=proc -> /proc/,", profile)
        self.assertIn("/proc/ rw,", profile)
        self.assertIn("owner /tmp/** rwkl,", profile)


if __name__ == "__main__":
    unittest.main()
