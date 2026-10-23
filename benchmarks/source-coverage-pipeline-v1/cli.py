"""Explicitly selected files only: zero-call request/import CLI for any harness."""
import argparse,json,os,sys
from pathlib import Path
import producers as p
import auditing as audit
from coverage_contract import exact

def text(path):
 target=Path(path)
 if target.is_symlink():raise ValueError('Symlink inputs refused')
 if target.stat().st_size>256000:raise ValueError('Selected input exceeds256KB')
 return target.read_text(encoding='utf-8')

def load(path):return p.parse(text(path))

def sources(path):
 value=load(path)
 if type(value) is dict:
  exact(value,('schema_version','sources'))
  if type(value['schema_version']) is not int or value['schema_version']!=1:raise ValueError('Source schema version differs')
  value=value['sources']
 p.source_check(value);return value

def save(path,value):
 target=Path(path)
 if target.is_symlink():raise ValueError('Symlink outputs refused')
 fd=os.open(str(target),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'w',encoding='utf-8') as stream:stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main(argv=None):
 parser=argparse.ArgumentParser(description='Source-only coverage prototype; every command makes0model calls')
 commands=parser.add_subparsers(dest='command',required=True)
 for name in ('inventory-prepare','inventory-import','audit-prepare','audit-import','card-prepare','card-import'):
  cmd=commands.add_parser(name)
  cmd.add_argument('--sources' if name.startswith('inventory') else '--ledger',required=True)
  if name.startswith('card'):
   cmd.add_argument('--audit',required=True);cmd.add_argument('--budget-chars',type=int,required=True)
  if name.endswith('import'):
   cmd.add_argument('--answer',required=True);cmd.add_argument('--out',required=True)
 args=parser.parse_args(argv)
 try:
  if args.command=='inventory-prepare':result=p.make_inventory_request(sources(args.sources))
  elif args.command=='inventory-import':result=p.accept_inventory(text(args.answer),sources(args.sources))
  elif args.command=='audit-prepare':result=audit.make_audit_request(load(args.ledger))
  elif args.command=='audit-import':result=audit.accept_audit(text(args.answer),load(args.ledger))
  elif args.command=='card-prepare':result=audit.make_card_request(load(args.ledger),load(args.audit),args.budget_chars)
  else:result=audit.accept_card(text(args.answer),load(args.ledger),load(args.audit),args.budget_chars)
  if args.command.endswith('import'):
   save(args.out,result);result={'output':str(Path(args.out).resolve()),'status':result.get('status','inventory_candidate_unvalidated'),'model_calls':0}
  print(json.dumps(result,ensure_ascii=False,indent=2));return 0
 except (ValueError,TypeError,KeyError,OSError) as exc:
  print(json.dumps({'error_type':type(exc).__name__,'message':str(exc),'model_calls':0},ensure_ascii=False),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
