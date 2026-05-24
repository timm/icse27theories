#!/usr/bin/env python3
# Port of kaiaulu smell_radio_silence to python.
# Pipeline: mbox files -> reply graph -> community detection -> brokers.

import os, re, mailbox, email.utils, glob
from collections import defaultdict
import networkx as nx
import community as community_louvain

MBOX_DIR = "/home/claude/helix/helix/mod_mbox/save_mbox_mail"

# ---- 1. parse mbox -> messages -----------------------------------------

def normalize_addr(raw):
  """Lowercase email portion of a From header. Returns None on garbage."""
  if not raw: return None
  name, addr = email.utils.parseaddr(raw)
  if not addr or "@" not in addr: return None
  return addr.lower().strip()

def parse_one_mbox(path):
  """Yield (msg_id, in_reply_to, sender) per message."""
  for msg in mailbox.mbox(path):
    msg_id = (msg.get("Message-ID") or "").strip().strip("<>")
    irt    = (msg.get("In-Reply-To") or "").strip().strip("<>")
    sender = normalize_addr(msg.get("From"))
    if not msg_id or not sender:
      continue
    yield msg_id, irt or None, sender

# ---- 2. assemble reply edges -------------------------------------------

msg_to_sender = {}
replies = []  # (child_sender, parent_msg_id)

for path in sorted(glob.glob(f"{MBOX_DIR}/*.mbox")):
  for mid, irt, snd in parse_one_mbox(path):
    msg_to_sender[mid] = snd
    if irt:
      replies.append((snd, irt))

print(f"parsed {len(msg_to_sender)} messages, {len(replies)} reply links")

# resolve reply parents -> edges between developers (undirected, weighted)
edges = defaultdict(int)
for child, parent_mid in replies:
  parent = msg_to_sender.get(parent_mid)
  if parent is None or parent == child:
    continue
  a, b = sorted([child, parent])  # canonical ordering for undirected
  edges[(a, b)] += 1

print(f"developer pairs with reply links: {len(edges)}")

# ---- 3. build graph ----------------------------------------------------

G = nx.Graph()
for (a, b), w in edges.items():
  G.add_edge(a, b, weight=w)

print(f"graph: {G.number_of_nodes()} devs, {G.number_of_edges()} undirected edges")

# isolate the largest connected component (community detection wants it)
ccs = sorted(nx.connected_components(G), key=len, reverse=True)
print(f"connected components: {len(ccs)} (sizes: {[len(c) for c in ccs[:5]]}...)")
G_main = G.subgraph(ccs[0]).copy()
print(f"largest CC: {G_main.number_of_nodes()} devs, {G_main.number_of_edges()} edges")

# ---- 4. community detection (Louvain) ----------------------------------

partition = community_louvain.best_partition(G_main, weight="weight", random_state=1)
n_clusters = len(set(partition.values()))
print(f"Louvain found {n_clusters} clusters")

cluster_to_devs = defaultdict(list)
for dev, c in partition.items():
  cluster_to_devs[c].append(dev)

# ---- 5. radio silence pass (port of kaiaulu R/smells.R:207) ------------

brokers = []
broker_details = []

for clust_id, devs in cluster_to_devs.items():
  # size-1 cluster: that single dev is a broker by definition (kaiaulu line 244)
  if len(devs) == 1:
    brokers.append(devs[0])
    broker_details.append((devs[0], clust_id, "size-1 cluster"))
    continue

  # for each (vert, out_cluster), collect outgoing edges
  outgoing = defaultdict(list)  # out_cluster -> [(from_dev, to_dev)]
  for v in devs:
    for nbr in G_main.neighbors(v):
      c_nbr = partition[nbr]
      if c_nbr != clust_id:
        outgoing[c_nbr].append((v, nbr))

  # for each external cluster: if only ONE edge connects us to it,
  # the source developer is a radio-silence broker
  for out_c, links in outgoing.items():
    if len(links) == 1:
      src, dst = links[0]
      brokers.append(src)
      broker_details.append((src, clust_id, f"sole link to cluster {out_c} via {dst}"))

unique_brokers = sorted(set(brokers))

# ---- 6. report ---------------------------------------------------------

print(f"\n=== Radio Silence brokers (n={len(unique_brokers)}) ===")
for b in unique_brokers[:30]:
  print(f"  {b}")
if len(unique_brokers) > 30:
  print(f"  ... ({len(unique_brokers)-30} more)")

# breakdown
print(f"\n=== Smell incidents (n={len(broker_details)}) ===")
print("(a single dev can be a broker for multiple cluster pairs)")
for dev, cid, reason in broker_details[:15]:
  print(f"  {dev}  [cluster {cid}]  {reason}")
if len(broker_details) > 15:
  print(f"  ... ({len(broker_details)-15} more incidents)")

# summary stats
cluster_sizes = sorted([len(v) for v in cluster_to_devs.values()], reverse=True)
print(f"\n=== Cluster size distribution ===")
print(f"  total clusters: {n_clusters}")
print(f"  size-1 clusters: {sum(1 for s in cluster_sizes if s == 1)}")
print(f"  largest 5 cluster sizes: {cluster_sizes[:5]}")
