# mac-dev-tools

macOS development tools shared across local agent and mobile app workflows.

## Automatic simulator slimming

[SimSlim](https://github.com/MobAI-App/simslim) reduces simulator memory by
disabling selected background services. This repo installs its watcher as a
per-user macOS login service. It covers iOS, Apple TV (tvOS), Apple Watch
(watchOS), and Apple Vision Pro (visionOS) simulators opened by T3 Code, Flutter, and Xcode in the default
and Xcode testing device sets. SimSlim 0.12.0 or newer is required.

On an Apple Silicon Mac with Xcode, a supported Simulator runtime, and Python 3:

```bash
brew tap mobai-app/tap
brew install mobai-app/tap/simslim
# For an existing Homebrew installation:
brew upgrade mobai-app/tap/simslim
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

The mobile profile targets PocketManage's current local QA workflow. It disables
163 of SimSlim 0.12.0's 169 managed services, retaining only:

| Service | Purpose |
| --- | --- |
| `com.apple.apsd` | Push notifications |
| `com.apple.swcd` | Universal links |
| `com.apple.searchd` | Local file indexing and picker Recents |
| `com.apple.assetsd` | Photo-library access |
| `com.apple.medialibraryd` | Media-library database |
| `com.apple.assetsd.nebulad` | Photo-asset transfers; retained conservatively for picker compatibility |

SimSlim 0.12.0 also keeps `com.apple.gamed` enabled to avoid XCUITest launch
delays. Its platform safeguards retain `homed` on watchOS and `mobileassetd`
on visionOS. The shared profile applies to Apple TV as well as iOS; Apple TV
app behavior still needs its own QA.

Core services outside SimSlim's managed list remain enabled, including local
Keychain, location, and sharing. PocketManage uses local Keychain storage and its
own contacts/calendar data; neither requires iCloud sync or native Contacts and
Calendar daemons. StoreKit, Wallet, iCloud Drive/sync, native Contacts/Calendar,
Photos analysis, and Apple telemetry services are disabled. Use a stock simulator
or a revised profile when testing those capabilities, Siri, full Spotlight, or widgets.
Cloud-backed photos/files and authenticated app flows still need separate QA.

## T3 Code and test readiness

Call `device_list`, then `device_open` for an explicit host and UDID. Keep the
executable, target, `--config`, and `--session` returned by `device_open` on every
`agent-device` command. Install this service separately on each remote host.

Automatic slimming happens after boot and may take longer than the scan interval.
Before app tests, both configuration checks must pass on the device's host:

```bash
simslim verify <udid> --profile ~/.config/simslim/mobile-dev.json
simslim doctor <udid> --requires push,universal-links
```

If the profile differs, apply it before QA:

```bash
simslim on <udid> --profile ~/.config/simslim/mobile-dev.json
```

After upgrading from the broader profile, run `on` once per existing simulator
to restore `searchd`, which the old profile disabled. A watcher restart alone
cannot re-enable it.

This can reboot the device. The watcher retries failures but does not repair
profile edits during an already processed boot session. Service checks verify
configuration; app features still need end-to-end tests. Test local photo and
file attachments, login/token persistence, links, and push delivery. SimSlim's
`doctor --requires photos` also requires background `photoanalysisd`, which this
profile intentionally disables; it does not measure picker functionality.

## Stats and service controls

```bash
simslim top
simslim measure <udid>
launchctl print gui/$(id -u)/com.macdevtools.simslim-watch
```

Logs are in `~/Library/Logs/SimSlim/`. The upstream SwiftUI app also displays
simulator RAM, disk usage, and service state. Build it from the upstream repo
with `make app`, then open `build/SimSlim.app`.

### Mobile Dev button in the macOS app

The optional patch adds a **Mobile Dev** button in the Memory sidebar and selects
that profile at startup when `~/.config/simslim/mobile-dev.json` exists. Click it
to reload the watcher's profile. **Apply to Selected** applies Mobile Dev to the
checked rows; **Apply to All Running** applies it to every booted simulator,
including rows hidden by search. Both reload the profile from disk before applying
and show target counts. These actions may reboot simulators. **Selection → Select
Running** also lets you select all running simulators before adjusting the selection.
Selecting **Mobile Dev** alone does not modify a simulator.

The patched app fits its initial and restored window to the screen. Narrow windows
scroll the simulator columns horizontally and wrap the header instead of clipping
the sidebar or hiding the final columns.

Build the patched app from the matching upstream release with Go and Xcode:

```bash
SIMSLIM_PATCH="$(pwd)/simslim/mobile-dev-app.patch"
SIMSLIM_SOURCE="$(mktemp -d)"
git clone --depth 1 --branch v0.12.0 https://github.com/MobAI-App/simslim.git "$SIMSLIM_SOURCE"
cd "$SIMSLIM_SOURCE"
git apply "$SIMSLIM_PATCH"
make app
open build/SimSlim.app
```

The app validates category and service names before replacing the current
selection. This patch targets SimSlim 0.12.0; a stock app upgrade removes it.

For stock testing, stop automatic slimming before restoring the device:

```bash
python3 simslim/install.py uninstall
simslim off <udid>
```

Removing the service leaves applied profiles intact. Restore reboots the device;
reopen its T3 stream afterward. Persistent slimming needs iOS/tvOS 18.5,
watchOS 11.5, or visionOS 2.5 or newer.
The watcher uses no-reboot slimming on every supported runtime and reapplies it
after boot on older runtimes. Restart the watcher after upgrading the CLI so
the running process discovers Apple TV and the other supported platforms.
