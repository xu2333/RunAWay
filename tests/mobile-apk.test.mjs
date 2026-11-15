import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const checker=fileURLToPath(new URL('../scripts/check_mobile_apk.py',import.meta.url));
const internal='io.runaway.taste.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION';
function manifest(permission='',protection='signature',backup='false'){
  return `<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="io.runaway.taste"><permission android:name="${internal}" android:protectionLevel="${protection}"/>${permission}<application android:allowBackup="${backup}" android:usesCleartextTraffic="false"/></manifest>`;
}
function run(text){return spawnSync('python3',['-B',checker],{input:text,encoding:'utf8'});}
test('packaged APK allows only the app-scoped signature receiver permission',()=>{
  for(const text of [manifest(),manifest(`<uses-permission android:name="${internal}"/>`)]){const result=run(text);assert.equal(result.status,0,result.stderr);assert.deepEqual(JSON.parse(result.stdout).network_permissions,[]);}
  for(const text of [manifest('<uses-permission android:name="android.permission.INTERNET"/>'),manifest('<uses-permission-sdk-23 android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>'),manifest(`<uses-permission android:name="${internal}"/>`,'normal'),manifest('','signature','true'),'<bad>'])assert.equal(run(text).status,1);
});
