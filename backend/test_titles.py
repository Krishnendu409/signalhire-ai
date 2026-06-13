import asyncio
import sys
sys.path.insert(0, '.')
from app.services.ai import AIPipeline

tests = [
    ('Google - Senior Software Engineer\nFeb 2018 - Present\nBuilt scalable microservices.\nEducation: Master of Science Computer Science Stanford\nSkills: Python, Go, AWS, Kubernetes', 'Senior Software Engineer'),
    ('Backend Engineer at Twitter 2019 - Present\nScala microservices.\nEducation: BTech Computer Science\nSkills: Scala, Java, Kafka, Redis', 'Backend Engineer'),
    ('iOS Developer Apple March 2018 to Present\nSwift development.\nEducation: MSc Software Engineering\nSkills: Swift, Kotlin, iOS, Android', 'iOS Developer'),
    ('Data Scientist OpenAI March 2021 to Present\nPyTorch NLP research.\nEducation: Ph.D. Machine Learning\nSkills: Python, PyTorch, SQL', 'Data Scientist'),
    ('Machine Learning Engineer DeepMind Feb 2020 - Present\nPyTorch reinforcement learning.\nEducation: Ph.D. Computer Science\nSkills: Machine Learning, Python, TensorFlow', 'Machine Learning Engineer'),
    ('Network Engineer Cisco March 2016 - Present\nBGP/OSPF enterprise.\nEducation: B.E. Electronics\nCertifications: CCNA, CCNP\nSkills: Networking, Cisco, BGP, OSPF', 'Network Engineer'),
]

for text, expected in tests:
    r = asyncio.run(AIPipeline.parse_resume(text))
    title = r['current_title']
    edu = [e['degree'] for e in r['education']]
    match = expected.lower() in title.lower() or title.lower() in expected.lower()
    status = 'PASS' if match else 'FAIL'
    print(f"[{status}] Expected={expected:<35} Got={title:<35} Edu={edu}")
