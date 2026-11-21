# Mobile builds and installation

Both apps process selected files locally. There is no RunAWay account, upload,
telemetry, background scan or automatic model call. Extraction uses a request
you explicitly hand to your chosen model; the app has no bundled on-device LLM.

## Android

`runaway-android-debug` contains an installable development APK. Transfer it to
your Android phone and open it using the system package installer. It is a debug
prototype, not a Play Store release. Save private archives before replacing an
installation. CI debug signing is not a maintained release-signing identity.

`runaway-android-release-unsigned` contains a release APK and AAB for an owner's
release-signing workflow. They are deliberately not signed for distribution.
No private keystore is generated or uploaded by this repository's CI.

The app requests no Internet or broad storage permissions. Android's system file
picker grants access only to documents you select. Export defaults to Downloads
when supported, and you can choose another provider. Cloud providers are an
explicit owner choice and use their own policies.

## iPhone and iPad

`runaway-ios-simulator` is for an Xcode simulator, not installation on an iPhone.
`runaway-ios-device-unsigned` is an **arm64 iPhoneOS device build**, containing
`RunAWay-device-unsigned.ipa` and a build manifest. It still needs an owner's
Apple signing identity and provisioning before it can be installed or used for
TestFlight. An unsigned IPA is not a working TestFlight invitation.

For a normal Apple ID, install full Xcode from Apple and complete its first-launch
setup, then run:

```sh
cd apps/mobile
npm ci
npm run ios:personal
```

This builds and syncs the app, prepares a stable unique local bundle identifier
and opens the Xcode project. Sign in yourself under Xcode > Settings > Accounts,
select your Personal Team under App > Signing & Capabilities, connect and pair
your iPhone, choose it as the run destination and press Run. Complete any device
trust or Developer Mode steps yourself. The helper neither creates credentials
nor signs or installs the app.

The bundle identifier and optional Team ID live only in the ignored
`.runaway/ios-personal-signing.xcconfig`; keep this file to preserve the same app
identity. An optional `node prepare-personal-signing.mjs --team-id TEAMID` records
the team identifier shown in Xcode. Never provide a password, key or certificate.
TestFlight distribution requires the corresponding Apple Developer/App Store
Connect setup. Credentials and signing material stay outside the public repo.

On iOS the app exposes its Documents folder in Files and adds only a small
bundled `Read me.txt` explaining the local workflow. No personal source or profile
is automatically saved there. Explicit export opens the system document picker
at that local folder. Export staging files are cleared after completion/cancel;
you control the files you choose to keep and the providers/backups you use.

## What CI establishes

The native tests use only the bundled fictional demo. Android instrumentation
and iOS XCUITest open the actual system document interface, cancel a save, save
the private archive, clear the in-memory profile and reopen that archive through
the native open picker. A separate host-side checker reads the file that the
native picker saved and compares its detailed profile and prompt IDs with the
untouched fixture, including fictional provenance.

These are prospective checks, not results: see each PR's exact-head CI and test
artifacts for actual pass/fail outcomes. UI trees and native reports are retained
for failed tests. The device packager rejects simulator metadata, a non-arm64
executable and provisioned input mislabeled unsigned; that inspection is not
Apple distribution validation or a real-phone test.

The browser test still covers local import, evidence checks, all three harness
ZIPs, archive restoration and blocked network egress. None of these mechanical
checks establishes fidelity to a real person's future decisions.

See [local app and harness guide](local-mobile.md) for building and the three
independent Codex / Claude Code / Antigravity export modules.
