import argparse
import json
import os

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import networkx as nx
from tqdm import tqdm


def find_col(df, keywords):
    for col in df.columns:
        name = col.lower()
        if any(key in name for key in keywords):
            return col
    return None


def load_connections(path):
    df = pd.read_csv(path, sep="\t")
    wf_col = find_col(df, ["workflow", "wf", "workflow_id", "wf_id"])
    src_col = find_col(df, ["source", "src", "from", "out"])
    tgt_col = find_col(df, ["target", "tgt", "to", "in"])

    if src_col is None or tgt_col is None:
        if df.shape[1] >= 2:
            src_col = df.columns[0]
            tgt_col = df.columns[1]
        else:
            raise ValueError("Could not infer source/target columns.")

    if wf_col is None:
        df["__workflow__"] = "all"
        wf_col = "__workflow__"

    return df, wf_col, src_col, tgt_col


def build_sequences(df, wf_col, src_col, tgt_col):
    sequences = []
    for wf_id, gdf in df.groupby(wf_col):
        edges = list(zip(gdf[src_col].astype(str), gdf[tgt_col].astype(str)))
        graph = nx.DiGraph()
        graph.add_edges_from(edges)
        if len(graph.nodes) == 0:
            continue
        try:
            order = list(nx.topological_sort(graph))
        except Exception:
            order = list(graph.nodes())
        sequences.append(order)
    return sequences


def build_vocab(sequences, tool_popularity_path=None):
    tokens = set()
    for seq in sequences:
        tokens.update(seq)

    if tool_popularity_path and os.path.exists(tool_popularity_path):
        pop = pd.read_csv(tool_popularity_path)
        if "tool_id" in pop.columns:
            tokens.update(pop["tool_id"].astype(str).tolist())

    specials = ["<PAD>", "<BOS>", "<EOS>", "<UNK>"]
    vocab = specials + sorted(tokens)
    stoi = {token: idx for idx, token in enumerate(vocab)}
    itos = {idx: token for token, idx in stoi.items()}
    return vocab, stoi, itos


class SlidingWindowDataset(Dataset):
    def __init__(self, sequences, stoi, block_size, pad_id, bos_id, eos_id, unk_id):
        self.block_size = block_size
        self.pad_id = pad_id
        self.stoi = stoi
        self.unk_id = unk_id

        self.seqs = []
        for seq in sequences:
            ids = [bos_id] + [stoi.get(t, unk_id) for t in seq] + [eos_id]
            if len(ids) >= 2:
                self.seqs.append(ids)

        self.lengths = [max(0, len(seq) - 1) for seq in self.seqs]
        self.cum = np.cumsum(self.lengths) if self.lengths else np.array([0])

    def __len__(self):
        return int(self.cum[-1]) if len(self.cum) > 0 else 0

    def __getitem__(self, idx):
        seq_idx = int(np.searchsorted(self.cum, idx, side="right"))
        prev = 0 if seq_idx == 0 else self.cum[seq_idx - 1]
        offset = idx - prev
        seq = self.seqs[seq_idx]

        x = seq[offset:offset + self.block_size]
        y = seq[offset + 1:offset + self.block_size + 1]

        x = x + [self.pad_id] * (self.block_size - len(x))
        y = y + [self.pad_id] * (self.block_size - len(y))

        return torch.tensor(x), torch.tensor(y)


class TransformerLM(nn.Module):
    def __init__(self, vocab_size, d_model=256, nhead=8, num_layers=4, dim_ff=1024, dropout=0.1, max_len=512):
        super().__init__()
        self.token_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(max_len, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_ff,
            dropout=dropout,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.lm_head = nn.Linear(d_model, vocab_size)

    def forward(self, x):
        batch, steps = x.size()
        pos = torch.arange(steps, device=x.device).unsqueeze(0).expand(batch, steps)
        hidden = self.token_emb(x) + self.pos_emb(pos)
        mask = torch.triu(torch.ones(steps, steps, device=x.device), diagonal=1).bool()
        hidden = self.encoder(hidden, mask=mask)
        logits = self.lm_head(hidden)
        return logits


def train(args):
    df, wf_col, src_col, tgt_col = load_connections(args.connections)
    sequences = build_sequences(df, wf_col, src_col, tgt_col)
    print("Loaded {} workflow sequences".format(len(sequences)))

    vocab, stoi, itos = build_vocab(sequences, args.tool_popularity)
    print("Vocab size: {}".format(len(vocab)))

    pad_id = stoi["<PAD>"]
    bos_id = stoi["<BOS>"]
    eos_id = stoi["<EOS>"]
    unk_id = stoi["<UNK>"]

    dataset = SlidingWindowDataset(sequences, stoi, args.block_size, pad_id, bos_id, eos_id, unk_id)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TransformerLM(
        vocab_size=len(vocab),
        d_model=args.d_model,
        nhead=args.nhead,
        num_layers=args.num_layers,
        dim_ff=args.dim_ff,
        dropout=args.dropout,
        max_len=args.block_size,
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss(ignore_index=pad_id)

    model.train()
    for epoch in range(1, args.epochs + 1):
        total_loss = 0.0
        for x, y in tqdm(loader, desc="Epoch {}".format(epoch)):
            x = x.to(device)
            y = y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits.view(-1, logits.size(-1)), y.view(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / max(1, len(loader))
        print("Epoch {} Loss: {:.4f}".format(epoch, avg_loss))

    os.makedirs(args.out_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(args.out_dir, "transformer_model.pt"))
    with open(os.path.join(args.out_dir, "vocab.json"), "w") as handle:
        json.dump(stoi, handle, indent=2)
    print("Saved model + vocab to: {}".format(args.out_dir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--connections", required=True, help="workflow connections TSV")
    parser.add_argument("--tool_popularity", default=None, help="tool popularity CSV (optional)")
    parser.add_argument("--out_dir", default="model_out")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--block_size", type=int, default=64)
    parser.add_argument("--d_model", type=int, default=256)
    parser.add_argument("--nhead", type=int, default=8)
    parser.add_argument("--num_layers", type=int, default=4)
    parser.add_argument("--dim_ff", type=int, default=1024)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--lr", type=float, default=3e-4)

    train(parser.parse_args())
