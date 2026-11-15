"""Validate apkanalyzer's packaged manifest, not just the source XML. Offline."""
import json
import sys
import xml.etree.ElementTree as ET

ANDROID = '{http://schemas.android.com/apk/res/android}'
INTERNAL = 'io.runaway.taste.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'


def check(text):
    root = ET.fromstring(text)
    if root.get('package') != 'io.runaway.taste':
        raise ValueError('Unexpected app package')
    used = [node.get(ANDROID + 'name') for node in root if node.tag.startswith('uses-permission')]
    if any(name != INTERNAL for name in used):
        raise ValueError('Unexpected packaged permission')
    declarations = [node for node in root.findall('permission') if node.get(ANDROID + 'name') == INTERNAL]
    if INTERNAL in used and (len(declarations) != 1 or declarations[0].get(ANDROID + 'protectionLevel') not in ('signature', '0x2', '2')):
        raise ValueError('Internal receiver permission must be signature-protected')
    app = root.find('application')
    if app is None or app.get(ANDROID + 'allowBackup') != 'false':
        raise ValueError('Backups must be disabled')
    if app.get(ANDROID + 'usesCleartextTraffic') != 'false':
        raise ValueError('Cleartext traffic must be disabled')
    return {'status': 'passed', 'package': root.get('package'), 'permissions': used,
            'network_permissions': [], 'broad_storage_permissions': []}


if __name__ == '__main__':
    try:
        print(json.dumps(check(sys.stdin.read()), sort_keys=True))
    except (ValueError, ET.ParseError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
