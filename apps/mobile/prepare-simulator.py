"""Choose an available iPhone simulator on the disposable CI host, never a phone."""
import json
import os
import platform
import subprocess
from pathlib import Path


def call(*args):
    return subprocess.check_output(['xcrun', 'simctl', *args], text=True, timeout=420)


if os.environ.get('GITHUB_ACTIONS') != 'true':
    raise SystemExit('This helper is for disposable CI simulators. Use Xcode locally.')
devices = json.loads(call('list', 'devices', 'available', '--json'))['devices']
candidates = [(runtime, device) for runtime, group in devices.items() if '.iOS-' in runtime
              for device in group if device['name'].startswith('iPhone') and device.get('isAvailable', True)]
if not candidates:
    raise SystemExit('No available iPhone simulator runtime on this CI image')
def version(item):
    return tuple(int(part) for part in item[0].split('.iOS-')[-1].split('-'))

# Keep Intel CI on an available iOS18 runtime where possible. New runtimes can
# compile successfully while their cold boot exceeds the host's resource budget.
if platform.machine() == 'x86_64':
    stable = [item for item in candidates if version(item)[0] == 18]
    if stable:
        candidates = stable
runtime, device = max(candidates, key=lambda item: (item[1]['state'] == 'Booted', version(item), 'iPhone SE' in item[1]['name']))
print(json.dumps({'selected_device': device['name'], 'runtime': runtime, 'udid': device['udid'], 'host_arch': platform.machine(), 'physical_device': False}), flush=True)
if device['state'] != 'Booted':
    call('boot', device['udid'])
# bootstatus alone did not establish a usable UI session: the first hosted
# run failed before any test with an AX-loaded notification timeout. Start
# the Simulator host explicitly; the unchanged XCTest still decides success.
subprocess.run(['open', '-a', 'Simulator', '--args', '-CurrentDeviceUDID', device['udid']], check=True, timeout=30)
subprocess.run(['xcrun', 'simctl', 'bootstatus', device['udid'], '-b'], check=True, timeout=420)
Path('build').mkdir(exist_ok=True)
subprocess.run(['xcrun', 'simctl', 'io', device['udid'], 'screenshot', 'build/simulator-before-test.png'], check=True, timeout=60)
with Path(os.environ['GITHUB_ENV']).open('a') as stream:
    stream.write('RUNAWAY_SIMULATOR=' + device['udid'] + '\n')
print(json.dumps({'device': device['name'], 'runtime': runtime, 'udid': device['udid'], 'physical_device': False}))
