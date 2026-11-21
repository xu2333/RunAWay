#!/usr/bin/env bash
set -euo pipefail
if [[ "${GITHUB_ACTIONS:-}" != "true" ]]; then
  echo 'This helper is for the disposable CI emulator; run native tests from Android Studio locally.' >&2
  exit 1
fi
runaway_serial=$(adb get-serialno)
case "$runaway_serial" in emulator-*) ;; *) echo 'Expected the CI emulator, not a phone.' >&2; exit 1 ;; esac
mkdir -p build
trap 'adb -s "$runaway_serial" pull /sdcard/Android/data/io.runaway.taste/files/native-picker-window.xml build/native-picker-window.xml >/dev/null 2>&1 || true' EXIT
(cd android && ./gradlew :app:connectedDebugAndroidTest --no-daemon)
adb -s "$runaway_serial" pull /sdcard/Download/runaway.private.json build/android-roundtrip.synthetic.json
node check-native-archive.mjs --archive build/android-roundtrip.synthetic.json --out build/android-native-roundtrip.json
