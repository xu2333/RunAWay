"""Package an unprovisioned iPhoneOS archive; never label it installable/signed."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import struct
import zipfile


def package(archive, out):
    apps = list((Path(archive) / 'Products' / 'Applications').glob('*.app'))
    if len(apps) != 1:
        raise ValueError('Expected one application in the Xcode archive')
    app = apps[0]
    info = plistlib.loads((app / 'Info.plist').read_bytes())
    if info.get('CFBundleSupportedPlatforms') != ['iPhoneOS']:
        raise ValueError('This is not an iPhoneOS device build')
    executable = info.get('CFBundleExecutable', '')
    if not executable or Path(executable).name != executable:
        raise ValueError('Invalid application executable')
    header = (app / executable).read_bytes()[:32]
    if len(header) < 32 or header[:4] != b'\xcf\xfa\xed\xfe' or struct.unpack('<I', header[4:8])[0] != 0x0100000C:
        raise ValueError('Expected an arm64 Mach-O device executable')
    if (app / 'embedded.mobileprovision').exists():
        raise ValueError('Do not package a provisioned app as an unsigned artifact')
    files = sorted(p for p in app.rglob('*') if not p.is_dir())
    if any(p.is_symlink() for p in app.rglob('*')):
        raise ValueError('Unexpected symlink in application archive')
    destination = Path(out)
    destination.mkdir(parents=True, exist_ok=False)
    ipa = destination / 'RunAWay-device-unsigned.ipa'
    with zipfile.ZipFile(ipa, 'x', compression=zipfile.ZIP_DEFLATED) as output:
        for item in files:
            output.write(item, 'Payload/' + app.name + '/' + item.relative_to(app).as_posix())
    with zipfile.ZipFile(ipa) as output:
        if output.testzip() is not None:
            raise ValueError('Packaged IPA CRC differs')
    result = {'schema_version': 1, 'artifact_type': 'ios_device_build',
              'filename': ipa.name, 'bundle_id': info.get('CFBundleIdentifier'),
              'version': info.get('CFBundleShortVersionString'), 'platform': 'iPhoneOS',
              'architecture': 'arm64', 'bytes': ipa.stat().st_size,
              'sha256': hashlib.sha256(ipa.read_bytes()).hexdigest(),
              'installable_without_signing': False, 'distribution_signed': False,
              'apple_distribution_validation_performed': False,
              'note': 'Device build only; an owner-provided signing identity and provisioning profile are required for installation. Metadata/slice inspection is not Apple distribution validation.'}
    (destination / 'build-info.json').write_text(json.dumps(result, indent=2) + '\n')
    (destination / 'READ-ME.txt').write_text('RunAWay / iPhone device build\n\nThis is arm64 iPhoneOS code, not a simulator application.\nIt has not been provisioned for installation. Sign/build the Xcode project with your Apple team before installing on an iPhone or distributing through TestFlight.\nDo not upload private signing keys to the repository.\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.archive, args.out), sort_keys=True))
