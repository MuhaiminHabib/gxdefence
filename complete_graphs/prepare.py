"""Complete raw graphs, training-only scaling and frozen classifiers/PG fits."""
from pathlib import Path
import sys,json,hashlib,random,copy,shutil
ROOT=Path(__file__).resolve().parent;FW=ROOT.parent/'framework'
sys.path[:0]=[str(FW),str(FW/'scripts')]
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score,average_precision_score,precision_score,recall_score
from torch_geometric.data import Data
from torch_geometric.explain import Explainer,PGExplainer
from src.models.marasi_models import MarasiGraphSAGE
PREP=ROOT/'prepared';PREP.mkdir(exist_ok=True)
DEVICE='cuda' if torch.cuda.is_available() else 'cpu';torch.set_num_threads(4)
def seed(s):
    random.seed(s);np.random.seed(s);torch.manual_seed(s);torch.cuda.manual_seed_all(s)
def save(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf8');tmp.replace(path)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def load(name):
    b=torch.load(PREP/f'{name}.pt',map_location='cpu',weights_only=False)
    model=MarasiGraphSAGE(b['data'].num_features,b['hidden']).to(DEVICE);model.load_state_dict(b['state']);model.eval()
    for p in model.parameters():p.requires_grad_(False)
    return b['data'].to(DEVICE),model,b
def split_scale(x,y,edge):
    known=np.flatnonzero(y>=0)
    train,rest=train_test_split(known,test_size=.35,stratify=y[known],random_state=42)
    val,test=train_test_split(rest,test_size=4/7,stratify=y[rest],random_state=42)
    scaler=StandardScaler().fit(x[train]);x=scaler.transform(x).astype(np.float32)
    if not np.isfinite(x).all():raise ValueError('Nonfinite features')
    data=Data(x=torch.tensor(x),edge_index=torch.tensor(edge,dtype=torch.long),y=torch.tensor(y))
    for key,ids in [('train',train),('val',val),('test',test)]:
        mask=torch.zeros(len(y),dtype=torch.bool);mask[ids]=True;setattr(data,key+'_mask',mask)
    return data,dict(train=len(train),validation=len(val),test=len(test),unknown=int((y<0).sum()),scaler_mean=scaler.mean_.tolist(),scaler_scale=scaler.scale_.tolist())
def elliptic():
    folder=FW/'data/raw/elliptic';features=pd.read_csv(folder/'elliptic_txs_features.csv',header=None)
    raw_ids=features.iloc[:,0].to_numpy(np.int64);idx=pd.Index(raw_ids)
    if not idx.is_unique:raise ValueError('Duplicate Elliptic transaction IDs')
    classes=pd.read_csv(folder/'elliptic_txs_classes.csv',dtype={'class':str}).set_index('txId')['class'].reindex(raw_ids)
    if classes.isna().any():raise ValueError('Missing class record')
    y=classes.map({'1':0,'2':1,'unknown':-1}).to_numpy(np.int64)
    edges=pd.read_csv(folder/'elliptic_txs_edgelist.csv');edge=np.stack([idx.get_indexer(edges.txId1),idx.get_indexer(edges.txId2)])
    if (edge<0).any():raise ValueError('Unmapped edge endpoint')
    # Column 1 is time step; use every remaining supplied numeric feature, no labels.
    x=features.iloc[:,2:].to_numpy(float);data,split=split_scale(x,y,edge)
    np.save(PREP/'elliptic_transaction_ids.npy',raw_ids)
    meta=dict(nodes=len(y),edges=edge.shape[1],features=x.shape[1],split=split,
        input_sha256={p.name:sha(p) for p in folder.glob('*.csv')},
        graph='All transaction nodes including unknown labels; all supplied directed edges. Unknown labels excluded from supervised loss and evaluation.',
        mapping='Feature-file row order with explicit txId endpoint mapping')
    return data,0,110,meta
def hi_small():
    source=Path(r'C:\habib dissertation\Projects\defence\AMLTerraform\data\HI-Small_Trans.csv')
    df=pd.read_csv(source,dtype={'From Bank':str,'To Bank':str,'Account':str,'Account.1':str})
    a=df['From Bank']+':'+df['Account'];b=df['To Bank']+':'+df['Account.1']
    accounts=np.unique(np.concatenate([a.values,b.values]));idx=pd.Index(accounts)
    src=idx.get_indexer(a);dst=idx.get_indexer(b);n=len(accounts)
    features=[];names=[]
    for side,ends,col in [('out',src,'Amount Paid'),('in',dst,'Amount Received')]:
        amounts=df[col].to_numpy(float);count=np.bincount(ends,minlength=n)
        sums=np.bincount(ends,weights=amounts,minlength=n);sq=np.bincount(ends,weights=amounts**2,minlength=n)
        mean=sums/np.maximum(count,1);std=np.sqrt(np.maximum(0,sq/np.maximum(count,1)-mean**2))
        for label,v in [('count',count),('sum',sums),('mean',mean),('std',std)]:
            features.append(np.log1p(np.maximum(v,0)));names.append(side+'_'+label)
    y=np.zeros(n,dtype=np.int64);fraud=df['Is Laundering'].to_numpy()==1;y[src[fraud]]=1;y[dst[fraud]]=1
    data,split=split_scale(np.stack(features,1),y,np.stack([src,dst]))
    np.save(PREP/'hi_small_account_ids.npy',accounts)
    meta=dict(source=str(source),source_sha256=sha(source),total_rows=len(df),selected_rows=len(df),nodes=n,edges=len(df),positive_accounts=int(y.sum()),features=names,split=split,
        label='Account incident to any laundering-labelled row in the complete CSV',selection='All source rows, original order; edge index equals zero-based source row',
        limitations='Same eight aggregate features as prior pilot. Amounts mix currencies; no claim of economically normalized flows. Weak-classifier limitation must be reported if it persists.')
    return data,1,64,meta
def train(name,data,illicit,hidden,meta):
    seed(42);data=data.to(DEVICE);model=MarasiGraphSAGE(data.num_features,hidden).to(DEVICE)
    opt=torch.optim.Adam(model.parameters(),lr=.005,weight_decay=5e-4)
    labels=data.y[data.train_mask];counts=torch.bincount(labels,minlength=2).float()
    weights=counts.sum()/(2*counts.clamp_min(1));best=-1;state=None;stale=0;hist=[]
    for ep in range(300):
        model.train();opt.zero_grad();out=model(data.x,data.edge_index)
        loss=torch.nn.functional.cross_entropy(out[data.train_mask],labels,weight=weights);loss.backward();opt.step();model.eval()
        with torch.no_grad():p=model(data.x,data.edge_index).softmax(1)[:,illicit]
        yy=(data.y[data.val_mask]==illicit).cpu().numpy();pv=p[data.val_mask].cpu().numpy()
        ap=float(average_precision_score(yy,pv));f1=float(f1_score(yy,pv>=.5,zero_division=0))
        hist.append(dict(epoch=ep,loss=float(loss),val_ap=ap,val_f1=f1))
        if ap>best+1e-6:best=ap;state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()};stale=0;best_epoch=ep
        else:stale+=1
        if ep%10==0:
            print(name,'TRAIN',hist[-1],flush=True);pd.DataFrame(hist).to_csv(PREP/f'{name}_training.csv',index=False)
            save(ROOT/'results/preparation_status.json',dict(state='training',dataset=name,epoch=ep,val_ap=ap,val_f1=f1))
        if stale>=30:break
    pd.DataFrame(hist).to_csv(PREP/f'{name}_training.csv',index=False);model.load_state_dict(state);model.eval()
    with torch.no_grad():p=model(data.x,data.edge_index).softmax(1)[:,illicit]
    metrics={}
    for split in ['train','val','test']:
        mask=getattr(data,split+'_mask');yy=(data.y[mask]==illicit).cpu().numpy();pv=p[mask].cpu().numpy();pred=pv>=.5
        metrics[split]=dict(f1=float(f1_score(yy,pred,zero_division=0)),ap=float(average_precision_score(yy,pv)),precision=float(precision_score(yy,pred,zero_division=0)),recall=float(recall_score(yy,pred,zero_division=0)),positive_prevalence=float(yy.mean()))
    meta.update(metrics=metrics,best_epoch=best_epoch,selection='Maximum validation AP, patience30, at most300 epochs; no test tuning',test_f1=metrics['test']['f1'],test_ap=metrics['test']['ap'])
    save(PREP/f'{name}_model_metrics.json',meta)
    return model,data
def prepare(name):
    path=PREP/f'{name}.pt'
    if not path.exists():
        if name=='amlsim':
            shutil.copyfile(ROOT.parent/'prepared/amlsim.pt',path)
        else:
            data,illicit,hidden,meta=elliptic() if name=='elliptic' else hi_small()
            save(PREP/f'{name}_provenance.json',meta)
            model,data=train(name,data,illicit,hidden,meta)
            torch.save(dict(data=data.cpu(),state={k:v.detach().cpu() for k,v in model.state_dict().items()},illicit=illicit,hidden=hidden,meta=meta),path)
            del data,model;torch.cuda.empty_cache()
    data,model,b=load(name)
    for s in range(2026,2031):
        dest=PREP/f'{name}_pg_{s}.pt'
        if dest.exists():continue
        if name=='amlsim':shutil.copyfile(ROOT.parent/f'prepared/amlsim_pg_{s}.pt',dest);continue
        seed(s);alg=PGExplainer(epochs=20,lr=1e-6).to(DEVICE)
        ex=Explainer(model=model,algorithm=alg,explanation_type='phenomenon',edge_mask_type='object',model_config=dict(mode='multiclass_classification',task_level='node',return_type='raw'))
        with torch.no_grad():out=model(data.x,data.edge_index);pred=out.argmax(1);prob=out.softmax(1)[:,b['illicit']]
        incoming=torch.bincount(data.edge_index[1],minlength=data.num_nodes)
        candidates=(data.train_mask&(data.y==b['illicit'])&(pred==b['illicit'])&(prob>=.55)&(prob<=.95)&(incoming>0)).nonzero().flatten()
        nodes=candidates[:30].tolist()
        if not nodes:raise RuntimeError(f'No PG training nodes meet registered confidence rule for {name}')
        save(PREP/f'{name}_pg_training_nodes_{s}.json',nodes)
        for ep in range(20):
            losses=[alg.train(ep,model,data.x,data.edge_index,target=pred,index=int(n)) for n in nodes]
            if not np.isfinite(losses).all():raise ValueError('Nonfinite PG training')
            print(name,'PG',s,ep,float(np.mean(losses)),flush=True)
            save(ROOT/'results/preparation_status.json',dict(state='fitting_pg',dataset=name,trial=s,epoch=ep))
        torch.save(alg.state_dict(),dest)
    print('PREPARED',name,flush=True)
if __name__=='__main__':
    for name in (sys.argv[1:] or ['elliptic','amlsim','hi_small']):prepare(name)
    save(ROOT/'results/preparation_status.json',dict(state='complete'))
