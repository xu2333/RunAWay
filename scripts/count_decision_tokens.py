"""Count frozen memory text with an existing local GGUF tokenizer; no inference/network."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);p.add_argument('--model',required=True);a=p.parse_args()
 root=Path(a.run);memories=json.loads((root/'memories.synthetic.json').read_text());model_path=Path(a.model)
 import llama_cpp
 model=llama_cpp.Llama(model_path=str(model_path),vocab_only=True,n_gpu_layers=0,verbose=False)
 try:
  values={pid:{k:len(model.tokenize(text.encode(),add_bos=False,special=False)) for k,text in conditions.items() if text is not None} for pid,conditions in memories.items()}
  h=hashlib.sha256()
  with model_path.open('rb') as f:
   for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
  (root/'memory-tokens.json').write_text(json.dumps(values,indent=2)+'\n')
  (root/'tokenizer-metadata.json').write_text(json.dumps({'model_sha256':h.hexdigest(),'model_name':model.metadata.get('general.name'),'llama_cpp_python':importlib.metadata.version('llama-cpp-python'),'inference_performed':False,'network':False,'token_counts_include_complete_memory_text':True},indent=2)+'\n')
  print(json.dumps(values,indent=2))
 finally:model.close()
if __name__=='__main__':main()
