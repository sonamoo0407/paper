"""Offline citation backbone using NetworkX. Input evidence requires human review."""
import argparse
import hashlib
import json
from pathlib import Path
import networkx as nx


def build(data):
    ids = [n['id'] for n in data['nodes']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate node IDs')
    seeds = set(data.get('seeds', []))
    if not seeds <= set(ids):
        raise ValueError('Unknown seed')
    graph = nx.DiGraph()
    graph.add_nodes_from(sorted(ids))
    excluded = []
    for e in data['edges']:
        a,b = e['source'],e['target']
        if a not in graph or b not in graph:
            raise ValueError('Unknown endpoint')
        if a == b or e.get('kind') != 'citation' or e.get('verification') not in ('metadata','fulltext') or not e.get('evidence'):
            excluded.append(e)
            continue
        if not graph.has_edge(a,b):
            graph.add_edge(a,b,records=[])
        graph[a][b]['records'].append(e)
    projection = nx.Graph()
    projection.add_nodes_from(sorted(ids))
    for a,b in sorted(graph.edges):
        rank=max(2 if e['verification']=='fulltext' else 1 for e in graph[a][b]['records'])
        rank=max(rank, projection.get_edge_data(a,b,{}).get('weight',0))
        projection.add_edge(a,b,weight=rank)
    forest=nx.maximum_spanning_tree(projection,algorithm='kruskal')
    pairs={frozenset((a,b)) for a,b in forest.edges}
    counts={n:{'direct_seeds':sorted(seeds & set(graph.predecessors(n))),
               'reachable_seeds':sorted(s for s in seeds if s!=n and nx.has_path(graph,s,n))}
            for n in graph}
    return {'nodes':data['nodes'],'seeds':sorted(seeds),'counts':counts,
            'edges':[dict(source=a,target=b,records=v['records'],in_backbone=frozenset((a,b)) in pairs)
                     for a,b,v in graph.edges(data=True)],
            'backbone_pairs':[sorted((a,b)) for a,b in forest.edges],
            'excluded_edges':excluded,'components':nx.number_connected_components(projection),
            'policy':'Undirected maximum spanning forest; fulltext=2 metadata=1; not intellectual origin',
            'networkx_version':nx.__version__}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('input',type=Path)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    raw=args.input.read_bytes()
    result=build(json.loads(raw.decode('utf-8-sig')))
    result['input_sha256']=hashlib.sha256(raw).hexdigest()
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/'input.json').write_bytes(raw)
    (args.out/'graph.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    graph=nx.DiGraph()
    graph.add_nodes_from((n['id'],{'title':str(n.get('title',n['id']))}) for n in result['nodes'])
    graph.add_edges_from((e['source'],e['target'],{'in_backbone':e['in_backbone']}) for e in result['edges'])
    nx.write_graphml(graph,args.out/'citations.graphml')
    forest=nx.Graph()
    forest.add_nodes_from(graph.nodes(data=True))
    forest.add_edges_from(result['backbone_pairs'])
    nx.write_graphml(forest,args.out/'backbone.graphml')
    print(args.out.resolve())

if __name__=='__main__': main()
