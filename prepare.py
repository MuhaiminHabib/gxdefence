"""Build reproducible caches; retain existing classifier and PG weights."""
from pathlib import Path
import sys, json, hashlib, random, copy
ROOT=Path(__file__).resolve().parent
FW=ROOT/'framework'
sys.path[:0]=[str(FW),str(FW/'scripts')]
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, average_precision_score
from torch_geometric.data import Data
from torch_geometric.explain import Explainer, PGExplainer
from src.models.marasi_models import MarasiGraphSAGE
from run_explainer_reports import load_dataset

PREP=ROOT/'prepared'; PREP.mkdir(exist_ok=True)
DEVICE='cuda' if torch.cuda.is_available() else 'cpu'
torch.set_num_threads(4)
def seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)
def save(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf8');tmp.replace(path)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def load(name):
    b=torch.load(PREP/f'{name}.pt',map_location='cpu',weights_only=False)
    model=MarasiGraphSAGE(b['data'].num_features,b['hidden']).to(DEVICE)
    model.load_state_dict(b['state']);model.eval()
    for p in model.parameters():p.requires_grad_(False)
    return b['data'].to(DEVICE),model,b
def hi_small():
    source=Path(r'C:\habib dissertation\Projects\defence\AMLTerraform\data\HI-Small_Trans.csv')
    df=pd.read_csv(source,dtype={'From Bank':str,'To Bank':str,'Account':str,'Account.1':str})
    total=len(df); ids=np.sort(np.random.default_rng(42).choice(total,total//2,replace=False))
    np.save(PREP/'hi_small_source_rows.npy',ids);df=df.iloc[ids].copy()
    a=df['From Bank']+':'+df['Account'];b=df['To Bank']+':'+df['Account.1']
    accounts=np.unique(np.concatenate([a.values,b.values])); idx=pd.Index(accounts)
    src=idx.get_indexer(a);dst=idx.get_indexer(b);n=len(accounts)
    features=[]; names=[]
    for side,ends,col in [('out',src,'Amount Paid'),('in',dst,'Amount Received')]:
        amounts=df[col].to_numpy(float);counts=np.bincount(ends,minlength=n)
        sums=np.bincount(ends,weights=amounts,minlength=n)
        sq=np.bincount(ends,weights=amounts**2,minlength=n)
        means=sums/np.maximum(counts,1);std=np.sqrt(np.maximum(0,sq/np.maximum(counts,1)-means**2))
        for label,values in [('count',counts),('sum',sums),('mean',means),('std',std)]:
            features.append(np.log1p(np.maximum(values,0)));names.append(side+'_'+label)
    y=np.zeros(n,dtype=np.int64);fraud=df['Is Laundering'].to_numpy()==1
    y[src[fraud]]=1;y[dst[fraud]]=1
    train,rest=train_test_split(np.arange(n),test_size=.35,stratify=y,random_state=42)
    val,test=train_test_split(rest,test_size=4/7,stratify=y[rest],random_state=42)
    raw=np.stack(features,1);scaler=StandardScaler().fit(raw[train]);xx=scaler.transform(raw)
    data=Data(x=torch.tensor(xx,dtype=torch.float32),edge_index=torch.tensor(np.stack([src,dst])),y=torch.tensor(y))
    for key,values in [('train',train),('val',val),('test',test)]:
        mask=torch.zeros(n,dtype=torch.bool);mask[values]=True;setattr(data,key+'_mask',mask)
    np.save(PREP/'hi_small_account_ids.npy',accounts)
    meta=dict(source=str(source),source_sha256=sha(source),total_rows=total,selected_rows=len(ids),nodes=n,positive_accounts=int(y.sum()),features=names,
        scaler_mean=scaler.mean_.tolist(),scaler_scale=scaler.scale_.tolist(),label='any incident selected laundering row',selection='numpy default_rng(42), exactly floor(N/2) rows',split='stratified accounts 65/15/20 seed42')
    save(PREP/'hi_small_provenance.json',meta)
    data=data.to(DEVICE);seed(42);model=MarasiGraphSAGE(8,64).to(DEVICE)
    opt=torch.optim.Adam(model.parameters(),lr=.005,weight_decay=5e-4)
    weights=torch.tensor([1.,len(train)/max(1,int(y[train].sum()))-1],device=DEVICE)
    best=-1.;state=None;stale=0;hist=[]
    for epoch in range(300):
        model.train();opt.zero_grad();out=model(data.x,data.edge_index)
        loss=torch.nn.functional.cross_entropy(out[data.train_mask],data.y[data.train_mask],weight=weights)
        loss.backward();opt.step();model.eval()
        with torch.no_grad():
            p=model(data.x,data.edge_index).softmax(1)[:,1].cpu().numpy()
        ap=average_precision_score(y[val],p[val]);f1=f1_score(y[val],p[val]>=.5,zero_division=0)
        hist.append(dict(epoch=epoch,loss=float(loss),val_ap=float(ap),val_f1=float(f1)))
        if ap>best+1e-6:best=ap;state=copy.deepcopy(model.state_dict());stale=0
        else:stale+=1
        if epoch%10==0:print('HI TRAIN',hist[-1],flush=True);pd.DataFrame(hist).to_csv(PREP/'hi_small_training.csv',index=False)
        if stale>=30:break
    model.load_state_dict(state);model.eval()
    with torch.no_grad():p=model(data.x,data.edge_index).softmax(1)[:,1].cpu().numpy()
    meta['test_f1']=float(f1_score(y[test],p[test]>=.5,zero_division=0));meta['test_ap']=float(average_precision_score(y[test],p[test]))
    return data,model,1,64,meta
def prepare(name):
    path=PREP/f'{name}.pt'
    if not path.exists():
        seed(42)
        if name=='hi_small':data,model,illicit,hidden,meta=hi_small()
        else:
            data,model,illicit,hidden,cp,metrics=load_dataset(name,PREP,DEVICE)
            meta=dict(checkpoint=str(cp),checkpoint_sha256=sha(cp),metrics=metrics)
        model.eval()
        torch.save(dict(data=data.cpu(),state={k:v.detach().cpu() for k,v in model.state_dict().items()},illicit=illicit,hidden=hidden,meta=meta),path)
    data,model,b=load(name)
    for s in range(2026,2031):
        dest=PREP/f'{name}_pg_{s}.pt'
        if dest.exists():continue
        if name!='hi_small':
            import shutil
            shutil.copyfile(FW/f'outputs/graphsage_explanations_seed42_v2/{name}/pg_seed{s}.pt',dest)
            continue
        seed(s);alg=PGExplainer(epochs=20,lr=1e-6).to(DEVICE)
        ex=Explainer(model=model,algorithm=alg,explanation_type='phenomenon',edge_mask_type='object',model_config=dict(mode='multiclass_classification',task_level='node',return_type='raw'))
        with torch.no_grad():out=model(data.x,data.edge_index);pred=out.argmax(1);prob=out.softmax(1)[:,b['illicit']]
        incoming=torch.bincount(data.edge_index[1],minlength=data.num_nodes)
        candidates=(data.train_mask&(data.y==b['illicit'])&(pred==b['illicit'])&(prob>=.55)&(prob<=.95)&(incoming>0)).nonzero().flatten()
        nodes=candidates[:30].tolist()
        if not nodes:raise RuntimeError('No HI PG training nodes meet the registered confidence rule')
        save(PREP/f'hi_small_pg_training_nodes_{s}.json',nodes)
        for ep in range(20):
            losses=[alg.train(ep,model,data.x,data.edge_index,target=pred,index=int(n)) for n in nodes]
            if not np.isfinite(losses).all():raise ValueError('Nonfinite PG training')
            print('HI PG',s,ep,float(np.mean(losses)),flush=True)
        torch.save(alg.state_dict(),dest)
    print('PREPARED',name,flush=True)
if __name__=='__main__':
    for name in (sys.argv[1:] or ['elliptic','amlsim','hi_small']):prepare(name)
