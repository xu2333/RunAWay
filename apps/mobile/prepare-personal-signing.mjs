// Local project preparation only. Does not log in, create certificates or sign.
import {mkdir,readFile,writeFile,lstat,rename,unlink} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import {spawnSync} from 'node:child_process';

export async function preparePersonalSigning(root,teamId=null){
  if(teamId!==null&&!/^[A-Z0-9]{10}$/.test(teamId))throw Error('Team ID must be the 10-character identifier shown in Xcode; never supply a password/key.');
  const folder=path.join(root,'.runaway'),file=path.join(folder,'ios-personal-signing.xcconfig');
  for(const entry of [folder,file]){try{if((await lstat(entry)).isSymbolicLink())throw Error('Refusing a symlink in local signing settings.');}catch(e){if(e.code!=='ENOENT')throw e;}}
  await mkdir(folder,{recursive:true,mode:0o700});
  let before=null;try{before=await readFile(file,'utf8');}catch(e){if(e.code!=='ENOENT')throw e;}
  const prior=before?.match(/^RUNAWAY_BUNDLE_IDENTIFIER\s*=\s*([A-Za-z0-9.-]+)\s*$/m);
  if(before!==null&&!prior)throw Error('Existing signing settings need review; not replacing them.');
  const bundleId=prior?.[1]??'io.runaway.taste.personal.local'+randomUUID().replaceAll('-','').slice(0,12);
  let after=before??'// RunAWay local signing only; never commit.\nRUNAWAY_BUNDLE_IDENTIFIER = '+bundleId+'\n';
  if(teamId!==null){
    if(/^DEVELOPMENT_TEAM\s*=/m.test(after))after=after.replace(/^DEVELOPMENT_TEAM\s*=.*$/m,'DEVELOPMENT_TEAM = '+teamId);
    else after+='DEVELOPMENT_TEAM = '+teamId+'\n';
  }
  if(after!==before){
    const temporary=file+'.'+randomUUID();
    try{await writeFile(temporary,after,{flag:'wx',mode:0o600});await rename(temporary,file);}finally{await unlink(temporary).catch(e=>{if(e.code!=='ENOENT')throw e;});}
  }
  return {status:'prepared',bundle_id:bundleId,team_configured:/^DEVELOPMENT_TEAM\s*=\s*[A-Z0-9]{10}\s*$/m.test(after),
    creates_credentials:false,signs_or_installs:false,
    next:'In Xcode > Settings > Accounts, sign in yourself. Select your Personal Team under App > Signing & Capabilities, connect your iPhone and Run.'};
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  try{
    const args=process.argv.slice(2);let teamId=null,open=false;
    for(let i=0;i<args.length;i++){
      if(args[i]==='--team-id'&&args[i+1])teamId=args[++i];
      else if(args[i]==='--open')open=true;
      else throw Error('Usage: node prepare-personal-signing.mjs [--team-id TEAMID] [--open]');
    }
    const root=fileURLToPath(new URL('../../',import.meta.url));
    console.log(JSON.stringify(await preparePersonalSigning(root,teamId),null,2));
    if(open){
      if(process.platform!=='darwin')throw Error('Open the iOS Xcode project on a Mac.');
      const result=spawnSync('/usr/bin/open',['-a','Xcode',fileURLToPath(new URL('ios/App/App.xcodeproj',import.meta.url))],{stdio:'inherit'});
      if(result.status!==0)throw Error('Install full Xcode from Apple, then run npm run ios:personal again.');
    }
  }catch(e){console.error(e.message);process.exitCode=1;}
}
