import unittest
from build_forest import build

def fixture():
    return {'nodes':[{'id':n} for n in 'ABXYZ'],'seeds':['A','B'],
            'edges':[dict(source=a,target=b,kind='citation',verification='fulltext',evidence=['MOCK'])
                     for a,b in [('A','X'),('B','X'),('A','Y'),('Y','X'),('A','X')]]}

class Tests(unittest.TestCase):
    def test_counts(self):
        r=build(fixture())
        self.assertEqual(len(r['edges']),4)
        self.assertEqual(r['counts']['X']['direct_seeds'],['A','B'])
        self.assertEqual(r['counts']['X']['reachable_seeds'],['A','B'])
        self.assertEqual(len(r['backbone_pairs']),3)
        self.assertEqual(r['components'],2)
    def test_invalid(self):
        d=fixture(); d['edges'][0]['target']='missing'
        with self.assertRaises(ValueError): build(d)
    def test_semantic_not_citation(self):
        d=fixture(); d['edges'][0]['kind']='extends_method'
        self.assertEqual(len(build(d)['excluded_edges']),1)
    def test_cycle(self):
        d=fixture(); d['edges'].append(dict(source='X',target='A',kind='citation',verification='metadata',evidence=['MOCK']))
        self.assertEqual(build(d)['counts']['X']['reachable_seeds'],['A','B'])
    def test_deterministic(self):
        d=fixture(); r=build(d); d['edges'].reverse()
        self.assertEqual(r['backbone_pairs'],build(d)['backbone_pairs'])

if __name__=='__main__': unittest.main()
