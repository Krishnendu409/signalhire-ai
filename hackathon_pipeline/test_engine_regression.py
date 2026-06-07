from engine import RankingEngine
from test_regression import run_regression
import json

def test():
    engine = RankingEngine()
    
    base_jds = {
        'Search Engineer': {
            'family': 'Search Engineer',
            'keywords': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval', 'machine learning', 'python'],
            'title_terms': engine.config['role_families']['Search Engineer'],
            'req_skills': engine.config['skill_families']['Search Engineer']
        },
        'Frontend Engineer': {
            'family': 'Frontend Engineer',
            'keywords': ['react', 'vue', 'css', 'html', 'javascript', 'frontend', 'ui', 'typescript'],
            'title_terms': engine.config['role_families']['Frontend Engineer'],
            'req_skills': engine.config['skill_families']['Frontend Engineer']
        },
        'Sales Manager': {
            'family': 'Sales Manager',
            'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
            'title_terms': engine.config['role_families']['Sales Manager'],
            'req_skills': engine.config['skill_families']['Sales Manager']
        }
    }
    
    all_passed = True
    for jd_name, jd_data in base_jds.items():
        outputs = engine.run_pipeline(jd_data)
        if not run_regression(outputs, jd_name):
            all_passed = False
            
    if all_passed:
        print("ALL ENGINE REGRESSION TESTS PASSED.")
    else:
        print("REGRESSION TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    test()
