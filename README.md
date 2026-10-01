# mac-dev-tools

macOS development tools shared across local agent and mobile app workflows.

## Automatic iOS simulator slimming

[SimSlim](https://github.com/MobAI-App/simslim) reduces simulator memory by
disabling selected background services. This repo installs its watcher as a
per-user macOS login service. It covers simulators opened by T3 Code, Flutter,
and Xcode in the default and Xcode testing device sets.

On an Apple Silicon Mac with Xcode, an iOS Simulator runtime, and Python 3:

```bash
brew tap mobai-app/tap
brew install mobai-app/tap/simslim
python3 simslim/install.py install
```

Use native ARM Homebrew, usually `/opt/homebrew/bin/brew`. Alternatively, install
the official ARM64 CLI release after verifying its SHA-256 against the release
asset digest. `SIMSLIM_BIN` can select a specific executable.

The service runs `simslim watch --profile ~/.config/simslim/mobile-dev.json
--interval 3s`. It starts at login and restarts if it exits. SimSlim slims running
simulators without rebooting them. The CLI path is absolute, and the installer
copies the profile outside this checkout. Reinstall after changing the profile
or moving the CLI.

The mobile profile retains push, StoreKit, universal links, Photos, Contacts,
Calendar, iCloud/keychain, and native diagnostics. Siri, Spotlight, and widgets
need a stock simulator or a revised profile. A partial slim count is expected
because the profile intentionally keeps some services enabled.

## T3 Code and test readiness

Call `device_list`, then `device_open` for an explicit host and UDID. Keep the
executable, target, `--config`, and `--session` returned by `device_open` on every
`agent-device` command. Install this service separately on each remote host.

Automatic slimming happens after boot and may take longer than the scan interval.
Before app tests, both checks must pass on the device's host:

```bash
simslim verify <udid> --profile ~/.config/simslim/mobile-dev.json
simslim doctor <udid> --requires push,storekit,universal-links,photos,contacts,calendar,icloud,keychain-sync
```

If the profile differs, apply it before QA:

```bash
simslim on <udid> --profile ~/.config/simslim/mobile-dev.json
```

This can reboot the device. The watcher retries failures but does not repair
profile edits during an already processed boot session. Service checks verify
configuration; app features still need end-to-end tests.

## Stats and service controls

```bash
simslim top
simslim measure <udid>
launchctl print gui/$(id -u)/com.macdevtools.simslim-watch
```

Logs are in `~/Library/Logs/SimSlim/`. The upstream SwiftUI app also displays
simulator RAM, disk usage, and service state. Build it from the upstream repo
with `make app`, then open `build/SimSlim.app`.

For stock testing, stop automatic slimming before restoring the device:

```bash
python3 simslim/install.py uninstall
simslim off <udid>
```

Removing the service leaves applied profiles intact. Restore reboots the device;
reopen its T3 stream afterward. Persistent slimming needs iOS 18.5 or newer;
older runtimes are slimmed again after boot by the watcher.
