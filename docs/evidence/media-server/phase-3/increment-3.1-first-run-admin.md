# Increment 3.1 First-Run Admin Setup

Purpose:

- Complete Jellyfin wizard with a local admin user.

Reachability command run by Codex:

```bash
cd /home/source/SpiritOS
curl -I http://127.0.0.1:8096/web/
```

Reachability output:

```text
HTTP/1.1 200 OK
Content-Length: 5331
Content-Type: text/html
Server: Kestrel
```

Manual/user-only step:

- Open `http://127.0.0.1:8096` on the Dell, or through an approved private SSH tunnel.
- Create the Jellyfin admin account in the browser.
- Store the password outside the repo.
- Do not put the password in docs, shell history, `.env`, screenshots, or chat.

Manual check:

- Jellyfin first-run web app is reachable locally.
- Admin credential creation was not performed by Codex.
- No secret was written to the repo.
- No screenshot containing a password was created.

Follow-up after user reported manual admin setup:

```bash
curl -fsS http://127.0.0.1:8096/System/Info/Public
grep -Ei 'wizard|startup' /mnt/spirit-8tb/services/jellyfin/config/config/system.xml
```

Follow-up output:

```text
{"LocalAddress":"http://127.0.0.1:8096","ServerName":"f599a2eb64d4","Version":"10.11.10","ProductName":"Jellyfin Server","OperatingSystem":"","Id":"620f5439f5d54ea48fdbd79173352a02","StartupWizardCompleted":false}
<IsStartupWizardCompleted>false</IsStartupWizardCompleted>
```

Result:

- Jellyfin is still reporting the first-run wizard as incomplete.
- Codex did not ask for, print, store, or change the Jellyfin password.

Second follow-up after user completed the remaining wizard page:

```bash
curl -fsS http://127.0.0.1:8096/System/Info/Public
```

Second follow-up output:

```text
{"LocalAddress":"http://127.0.0.1:8096","ServerName":"f599a2eb64d4","Version":"10.11.10","ProductName":"Jellyfin Server","OperatingSystem":"","Id":"620f5439f5d54ea48fdbd79173352a02","StartupWizardCompleted":true}
```

Second follow-up result:

- Jellyfin now reports the startup wizard as complete.
- No credentials were requested, printed, stored, or changed by Codex.

Rollback:

- If setup must be restarted, stop Jellyfin and move the config directory aside only after explicit approval.

Status: GO
