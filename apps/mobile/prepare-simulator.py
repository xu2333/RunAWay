"""Choose an available iPhone simulator on the disposable CI host, never a phone."""
import json
import os
import subprocess
from pathlib import Path


def call(*args):
    return subprocess.check_output(['xcrun', 'simctl', *args], text=True, timeout=240)


if os.environ.get('GITHUB_ACTIONS') != 'true':
    raise SystemExit('This helper is for disposable CI simulators. Use Xcode locally.')
devices = json.loads(call('list', 'devices', 'available', '--json'))['devices']
candidates = [(runtime, device) for runtime, group in devices.items() if '.iOS-' in runtime
              for device in group if device['name'].startswith('iPhone') and device.get('isAvailable', True)]
if not candidates:
    raise SystemExit('No available iPhone simulator runtime on this CI image')
runtime, device = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
if device['state'] != 'Booted':
    call('boot', device['udid'])
call('bootstatus', device['udid'], '-b')
with Path(os.environ['GITHUB_ENV']).open('a') as stream:
    stream.write('RUNAWAY_SIMULATOR=' + device['udid'] + '\n')
print(json.dumps({'device': device['name'], 'runtime': runtime, 'udid': device['udid'], 'physical_device': False}))
