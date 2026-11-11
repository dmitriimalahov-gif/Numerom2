import importlib.util
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from domain.relationships import connection


class RelationshipNarrationTests(unittest.TestCase):
    def test_every_possible_pair_uses_its_actual_report_interpretation(self):
        spec=importlib.util.spec_from_file_location('relationship_narration',ROOT/'scripts/prepare-relationship-narration.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        rows={r['id']:r for r in module.entries()}
        published={r['id']:r for r in json.loads((ROOT/'packages/project-knowledge/ru.json').read_text())['items']}
        for key,row in rows.items():self.assertEqual(published[key],row)
        for a in [1,2,3,4,5,6,7,8,9,11,22,33]:
            for b in [1,2,3,4,5,6,7,8,9,11,22,33]:
                item=connection({'number':a},{'number':b,'name':'Private name'})
                score=item['score'];key='same' if score==10 else 'close' if score>=8 else 'different' if score>=6 else 'contrast'
                self.assertEqual(rows['relationship-'+key]['text'],item['interpretation']+' '+item['focus'])
                self.assertNotIn('Private name',rows['relationship-'+key]['text'])
