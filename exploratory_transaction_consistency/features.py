"""Exact incident-record feature updates; original preprocessing is read-only."""
import contextlib
import io
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch

STUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(STUDY / 'framework'))
from src.data.ibm_amlsim_prev_reproduction import build_ibm_amlsim_graph


class Records:
    def __init__(self, name, data):
        self.name, self.data = name, data
        self.n = data.num_nodes
        self.edges = data.edge_index.numpy()
        self.prep = None
        if name == 'amlsim':
            self.folder = STUDY / 'framework/data/raw/ibm_amlsim'
            self.accounts = pd.read_csv(self.folder / 'accounts.csv')
            self.frame = pd.read_csv(self.folder / 'transactions.csv')
            account_ids = self.accounts.ACCOUNT_ID.astype(str)
            idx = pd.Index(account_ids)
            src = idx.get_indexer(self.frame.SENDER_ACCOUNT_ID.astype(str))
            dst = idx.get_indexer(self.frame.RECEIVER_ACCOUNT_ID.astype(str))
            valid = (src >= 0) & (dst >= 0)
            self.frame = self.frame.loc[valid].reset_index(drop=True)
            src, dst = src[valid], dst[valid]
            with contextlib.redirect_stdout(io.StringIO()):
                ref, self.prep = build_ibm_amlsim_graph(
                    self.folder, seed=42, include_fraud_tx_count_features=False,
                    include_categorical_features=False, return_preprocessing=True,
                    accounts_frame=self.accounts, transactions_frame=self.frame)
            torch.testing.assert_close(ref.edge_index, data.edge_index, atol=0, rtol=0)
            torch.testing.assert_close(ref.x, data.x, atol=2e-5, rtol=2e-5)
            assert list(ref.feature_names) == list(data.feature_names)
            assert not data.include_fraud_tx_count_features and not data.include_categorical_features
            for mask in ('train_mask', 'val_mask', 'test_mask'):
                assert torch.equal(getattr(ref, mask), getattr(data, mask))
            self.names = list(data.feature_names)
            self.mean = self.prep['numeric_scaler'].mean_
            self.scale = self.prep['numeric_scaler'].scale_
            self.amount_out = self.frame.TX_AMOUNT.to_numpy(float)
            self.amount_in = self.amount_out
            self.types = pd.factorize(self.frame.TX_TYPE)[0]
            timestamp = self.frame.TIMESTAMP
            self.times = (timestamp.to_numpy(float) if np.issubdtype(timestamp.dtype, np.number)
                          else (pd.to_datetime(timestamp, errors='coerce').astype('int64') // 10**9).to_numpy(float))
            self.static = self.accounts[['INIT_BALANCE', 'TX_BEHAVIOR_ID']].to_numpy(float)
            self.clean_max_error = float((ref.x-data.x).abs().max())
            del ref
        elif name == 'hi_small':
            meta = json.loads((STUDY / 'complete_graphs/prepared/hi_small_provenance.json').read_text())
            self.source = Path(meta['source'])
            cols = ['From Bank', 'To Bank', 'Account', 'Account.1', 'Amount Paid', 'Amount Received']
            self.frame = pd.read_csv(self.source, usecols=cols,
                                    dtype={c: str for c in cols[:4]})
            accounts = np.load(STUDY / 'complete_graphs/prepared/hi_small_account_ids.npy', allow_pickle=True)
            idx = pd.Index(accounts)
            src = idx.get_indexer(self.frame['From Bank'] + ':' + self.frame['Account'])
            dst = idx.get_indexer(self.frame['To Bank'] + ':' + self.frame['Account.1'])
            self.amount_out = self.frame['Amount Paid'].to_numpy(float)
            self.amount_in = self.frame['Amount Received'].to_numpy(float)
            self.names = meta['features']
            self.mean = np.asarray(meta['split']['scaler_mean'])
            self.scale = np.asarray(meta['split']['scaler_scale'])
            self.frame = None
        else:
            raise ValueError(name)
        assert np.array_equal(np.stack([src, dst]), self.edges), 'Raw transaction-row mapping differs'
        self.src, self.dst = src, dst
        self.index = []
        for ends in (src, dst):
            order = np.argsort(ends, kind='stable')
            offsets = np.r_[0, np.cumsum(np.bincount(ends, minlength=self.n))]
            self.index.append((order, offsets))
        if name == 'hi_small':
            ref = self.full_reference(set())
            torch.testing.assert_close(ref, data.x, atol=2e-5, rtol=2e-5)
            self.clean_max_error = float((ref-data.x).abs().max())
        self.update_calls = 0

    def incident(self, node, side, removed, retained):
        if retained is not None:
            r = np.asarray(sorted(retained), dtype=np.int64)
            ends = self.src if side == 0 else self.dst
            return r[ends[r] == node]
        order, offsets = self.index[side]
        r = order[offsets[node]:offsets[node+1]]
        if removed:
            r = r[~np.isin(r, list(removed))]
        return r

    def vector(self, node, removed, retained=None):
        if self.name == 'hi_small':
            vals = []
            for side, amounts in enumerate((self.amount_out, self.amount_in)):
                r = self.incident(node, side, removed, retained)
                a = amounts[r]; count = len(a)
                # bincount accumulates in original row order, matching full preprocessing
                # even for nearly constant large amounts where variance cancellation matters.
                zeros = np.zeros(count, dtype=np.int64)
                total = float(np.bincount(zeros, weights=a, minlength=1)[0])
                mean = total / max(count, 1)
                # Match the original population-variance formula, not pandas ddof=1.
                sq = float(np.bincount(zeros, weights=np.square(a), minlength=1)[0])
                std = np.sqrt(max(0., sq / max(count, 1) - mean**2))
                vals.extend([count, total, mean, std])
            raw = np.log1p(np.maximum(vals, 0.))
        else:
            v = {'INIT_BALANCE': np.log1p(max(0., self.static[node, 0])),
                 'TX_BEHAVIOR_ID': self.static[node, 1]}
            for side, prefix in enumerate(('out', 'in')):
                r = self.incident(node, side, removed, retained)
                a = self.amount_out[r]; count = len(a)
                peers = self.dst[r] if side == 0 else self.src[r]
                stats = dict(tx_count=count, amount_sum=float(a.sum()),
                             amount_mean=float(a.mean()) if count else 0.,
                             amount_std=float(a.std(ddof=1)) if count > 1 else 0.,
                             amount_min=float(a.min()) if count else 0.,
                             amount_max=float(a.max()) if count else 0.,
                             unique_tx_types=len(np.unique(self.types[r])))
                stats['unique_receivers' if side == 0 else 'unique_senders'] = len(np.unique(peers))
                v.update({prefix+'_'+k: np.log1p(max(value, 0.)) for k, value in stats.items()})
                v[prefix+'_first_time'] = float(self.times[r].min()) if count else 0.
                v[prefix+'_last_time'] = float(self.times[r].max()) if count else 0.
            # Preserve the original ratios of transformed values exactly.
            v['total_tx_count'] = v['out_tx_count']+v['in_tx_count']
            v['total_amount_sum'] = v['out_amount_sum']+v['in_amount_sum']
            v['out_in_count_ratio'] = v['out_tx_count']/(v['in_tx_count']+1.)
            v['in_out_count_ratio'] = v['in_tx_count']/(v['out_tx_count']+1.)
            raw = np.asarray([v[k] for k in self.names])
        arr = ((raw-self.mean)/self.scale).astype(np.float32)
        assert np.isfinite(arr).all()
        return arr

    def features(self, nodes, removed, retained=None):
        nodes = list(map(int, nodes)); removed = set(removed)
        x = self.data.x[nodes].clone()
        affected = (set(nodes) if retained is not None else
                    set(self.edges[:, sorted(removed)].reshape(-1).tolist()) if removed else set())
        for j, node in enumerate(nodes):
            if node in affected:
                x[j] = torch.from_numpy(self.vector(node, removed, retained))
        self.update_calls += 1
        return x

    def full_reference(self, removed, retained=None):
        if retained is None:
            keep = np.ones(self.edges.shape[1], dtype=bool)
            keep[list(removed)] = False
        else:
            keep = np.zeros(self.edges.shape[1], dtype=bool)
            keep[list(retained)] = True
        if self.name == 'amlsim':
            with contextlib.redirect_stdout(io.StringIO()):
                ref = build_ibm_amlsim_graph(
                    self.folder, seed=42, include_fraud_tx_count_features=False,
                    include_categorical_features=False, numeric_scaler=self.prep['numeric_scaler'],
                    accounts_frame=self.accounts, transactions_frame=self.frame.loc[keep])
            return ref.x
        vals = []
        for ends, amounts in ((self.src, self.amount_out), (self.dst, self.amount_in)):
            count = np.bincount(ends[keep], minlength=self.n)
            total = np.bincount(ends[keep], weights=amounts[keep], minlength=self.n)
            sq = np.bincount(ends[keep], weights=amounts[keep]**2, minlength=self.n)
            mean = total/np.maximum(count, 1)
            std = np.sqrt(np.maximum(0., sq/np.maximum(count, 1)-mean**2))
            vals.extend([np.log1p(np.maximum(v, 0.)) for v in (count, total, mean, std)])
        return torch.from_numpy(((np.stack(vals, 1)-self.mean)/self.scale).astype(np.float32))
