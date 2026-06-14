import asyncio
import json
import csv
from app.services.ai import AIPipeline
from app.services.ranking import rank_candidates_for_job

# Manually curated 25 realistic real-world resume formats
MANUAL_RESUMES = [
    {
        "text": "Alice Johnson\nalice.j@email.com\n\nObjective: Seeking a Senior Software Engineer position.\n\nProfessional Experience:\nGoogle - Senior Software Engineer\nFeb 2018 - Present\nLed the development of scalable microservices using Go and Python.\n\nAmazon - Software Development Engineer II\nJun 2015 - Jan 2018\nDeveloped AWS Lambda functions using Node.js.\n\nEducation:\nMaster of Science in Computer Science, Stanford University\n\nSkills:\nPython, Go, Node.js, AWS, Kubernetes, Microservices",
        "gt": {"title": "Senior Software Engineer", "yoe": 11, "skills": ["Python", "Go", "Node.js", "AWS", "Kubernetes", "Microservices"], "education": "MS", "certifications": []}
    },
    {
        "text": "Bob Smith | DevOps Engineer | bobs@outlook.com\n\nEXPERIENCE\nDevOps Engineer @ Netflix\nJanuary 2020 - Current\nManaged Kubernetes clusters and CI/CD pipelines.\n\nSystems Administrator @ Oracle\nMarch 2016 - December 2019\nMaintained Linux infrastructure.\n\nEDUCATION\nBachelor of Engineering in IT\n\nCERTIFICATIONS\nAWS Certified Solutions Architect, CKA\n\nTECHNICAL SKILLS\nDocker, Kubernetes, Jenkins, AWS, Bash, Linux",
        "gt": {"title": "DevOps Engineer", "yoe": 10, "skills": ["Docker", "Kubernetes", "Jenkins", "AWS", "Bash", "Linux"], "education": "BE", "certifications": ["AWS Certified Solutions Architect", "CKA"]}
    },
    {
        "text": "CAROL DAVIS\ncarol.davis@work.com\n\nSummary: Data Scientist with expertise in NLP.\n\nWork History:\nData Scientist | OpenAI\nMarch 2021 to Present\nTrained large language models using PyTorch.\n\nData Analyst | Meta\nJuly 2018 to February 2021\nAnalyzed user data using SQL and Python.\n\nEducation:\nPh.D. in Machine Learning\n\nSkills:\nPython, PyTorch, SQL, NLP, TensorFlow",
        "gt": {"title": "Data Scientist", "yoe": 7, "skills": ["Python", "PyTorch", "SQL", "NLP", "TensorFlow"], "education": "PhD", "certifications": []}
    },
    {
        "text": "David Lee - Frontend Developer\ndavid.lee@web.com\n\nEXPERIENCE:\nFrontend Developer, Airbnb (Jan 2019 - Present)\nBuilt highly interactive UIs using React and TypeScript.\n\nWeb Developer, StartUp Inc (Jun 2017 - Dec 2018)\nDeveloped HTML/CSS templates.\n\nEDUCATION:\nB.Tech in Computer Science\n\nSKILLS:\nReact, TypeScript, JavaScript, HTML, CSS",
        "gt": {"title": "Frontend Developer", "yoe": 9, "skills": ["React", "TypeScript", "JavaScript", "HTML", "CSS"], "education": "BTech", "certifications": []}
    },
    {
        "text": "EMILY CHEN\nemilyc@gmail.com\n\nExperience\nProduct Manager at Uber\nAug 2017 - Present\nDefined product roadmap and led agile teams.\n\nEducation\nMBA, Harvard Business School\n\nSkills\nAgile, Scrum, Product Strategy, JIRA, Confluence\n\nCertifications\nScrum Master",
        "gt": {"title": "Product Manager", "yoe": 8, "skills": ["Agile", "Scrum", "Product Strategy", "JIRA", "Confluence"], "education": "MBA", "certifications": ["Scrum Master"]}
    },
    {
        "text": "Frank Wright\nfrankw@domain.com\n\nCareer:\nFull Stack Engineer - Stripe\n05/2018 to Present\nDeveloped backend APIs in Ruby and frontend in React.\n\nSoftware Engineer - Square\n02/2015 to 04/2018\nBuilt payment processing systems.\n\nEducation:\nBS Computer Science\n\nSkills:\nRuby, React, PostgreSQL, JavaScript, REST APIs",
        "gt": {"title": "Full Stack Engineer", "yoe": 11, "skills": ["Ruby", "React", "PostgreSQL", "JavaScript", "REST APIs"], "education": "BS", "certifications": []}
    },
    {
        "text": "Grace Taylor - Security Engineer\ngrace.t@sec.com\n\nExperience\nSecurity Engineer, CrowdStrike\nJan 2020 - Present\nPerformed penetration testing and vulnerability assessments.\n\nSecurity Analyst, FireEye\nJun 2016 - Dec 2019\nMonitored network traffic.\n\nEducation\nB.S. in Cybersecurity\n\nCertifications\nCISSP, CEH\n\nSkills\nPenetration Testing, Python, Network Security",
        "gt": {"title": "Security Engineer", "yoe": 10, "skills": ["Penetration Testing", "Python", "Network Security"], "education": "BS", "certifications": ["CISSP", "CEH"]}
    },
    {
        "text": "Henry Adams\nhenry.adams@test.org\n\nExperience:\nBackend Developer | Twitter\n2019 - Present\nScaled Scala microservices.\n\nJunior Developer | Tech Corp\n2017 - 2019\nWrote Java applications.\n\nEducation:\nBachelor of Technology\n\nSkills:\nScala, Java, Microservices, Kafka, Redis",
        "gt": {"title": "Backend Developer", "yoe": 9, "skills": ["Scala", "Java", "Microservices", "Kafka", "Redis"], "education": "BTech", "certifications": []}
    },
    {
        "text": "Isabella Moore | Mobile Developer\nisa.moore@mobile.com\n\nEmployment\niOS Developer @ Apple\nMarch 2018 to Present\nDeveloped core iOS features in Swift.\n\nApp Developer @ Startup\nAugust 2015 to February 2018\nBuilt Android apps in Kotlin.\n\nEducation\nMSc in Software Engineering\n\nSkills\nSwift, Kotlin, iOS, Android, Mobile Development",
        "gt": {"title": "iOS Developer", "yoe": 10, "skills": ["Swift", "Kotlin", "iOS", "Android", "Mobile Development"], "education": "MSc", "certifications": []}
    },
    {
        "text": "Jack Wilson - Cloud Architect\njack.w@cloudarch.com\n\nWork Experience\nCloud Architect, AWS\nJanuary 2017 - Current\nDesigned multi-region cloud architectures.\n\nEducation\nB.E. Computer Engineering\n\nCertifications\nAWS Certified Solutions Architect\n\nSkills\nAWS, Cloud Architecture, Terraform, Kubernetes",
        "gt": {"title": "Cloud Architect", "yoe": 9, "skills": ["AWS", "Cloud Architecture", "Terraform", "Kubernetes"], "education": "BE", "certifications": ["AWS Certified Solutions Architect"]}
    },
    {
        "text": "Karen Thomas\nkaren.t@data.io\n\nExperience:\nData Engineer, Snowflake\nMay 2019 - Present\nBuilt data pipelines using Python and SQL.\n\nData Analyst, RetailCo\nJune 2016 - April 2019\nCreated reports.\n\nEducation:\nBachelors in Computer Science\n\nSkills:\nPython, SQL, Data Pipelines, ETL, Snowflake",
        "gt": {"title": "Data Engineer", "yoe": 10, "skills": ["Python", "SQL", "Data Pipelines", "ETL", "Snowflake"], "education": "BS", "certifications": []}
    },
    {
        "text": "Leo Garcia | Machine Learning Engineer\nleo.g@ai.com\n\nExperience\nMachine Learning Engineer - DeepMind\nFeb 2020 - Present\nResearched reinforcement learning models.\n\nSoftware Engineer - Google\nJan 2018 - Jan 2020\nDeveloped backend systems.\n\nEducation\nPh.D. Computer Science\n\nSkills\nMachine Learning, Python, TensorFlow, Reinforcement Learning, C++",
        "gt": {"title": "Machine Learning Engineer", "yoe": 8, "skills": ["Machine Learning", "Python", "TensorFlow", "Reinforcement Learning", "C++"], "education": "PhD", "certifications": []}
    },
    {
        "text": "Mia Martinez - QA Automation Engineer\nmia.m@qa.com\n\nEmployment History\nQA Automation Engineer | Selenium Inc\nMarch 2017 - Present\nWrote automated test scripts using Python and Selenium.\n\nEducation\nDiploma in Software Testing\n\nSkills\nSelenium, Python, Cypress, Automated Testing",
        "gt": {"title": "QA Automation Engineer", "yoe": 9, "skills": ["Selenium", "Python", "Cypress", "Automated Testing"], "education": "Diploma", "certifications": []}
    },
    {
        "text": "Nathan White\nnathan.white@crypto.io\n\nExperience:\nBlockchain Developer at Coinbase\n2018 - Present\nDeveloped smart contracts in Solidity.\n\nEducation:\nBTech Information Technology\n\nSkills:\nSolidity, Blockchain, Ethereum, JavaScript",
        "gt": {"title": "Blockchain Developer", "yoe": 8, "skills": ["Solidity", "Blockchain", "Ethereum", "JavaScript"], "education": "BTech", "certifications": []}
    },
    {
        "text": "Olivia Hall | UI/UX Designer\nolivia.h@design.com\n\nExperience\nUI/UX Designer, Figma\nAugust 2019 - Present\nDesigned user interfaces.\n\nGraphic Designer, AdAgency\nMay 2016 - July 2019\nCreated marketing materials.\n\nEducation\nBachelor of Arts in Design\n\nSkills\nUI/UX, Figma, Adobe XD, Sketch",
        "gt": {"title": "UI/UX Designer", "yoe": 10, "skills": ["UI/UX", "Figma", "Adobe XD", "Sketch"], "education": "BA", "certifications": []}
    },
    {
        "text": "Paul King - SRE\npaul.king@sre.com\n\nWork\nSite Reliability Engineer @ GitHub\nJan 2020 - Present\nMaintained high availability.\n\nSysadmin @ ServerHub\nJan 2015 - Dec 2019\nManaged servers.\n\nEducation\nB.S. Computer Science\n\nSkills\nLinux, Kubernetes, Go, Python, SRE",
        "gt": {"title": "Site Reliability Engineer", "yoe": 11, "skills": ["Linux", "Kubernetes", "Go", "Python", "SRE"], "education": "BS", "certifications": []}
    },
    {
        "text": "Quinn Scott\nquinn.s@network.com\n\nExperience:\nNetwork Engineer, Cisco\nMar 2016 - Present\nConfigured enterprise networks.\n\nEducation:\nB.E. Electronics\n\nCertifications:\nCCNA, CCNP\n\nSkills:\nNetworking, Cisco, BGP, OSPF",
        "gt": {"title": "Network Engineer", "yoe": 10, "skills": ["Networking", "Cisco", "BGP", "OSPF"], "education": "BE", "certifications": ["CCNA", "CCNP"]}
    },
    {
        "text": "Rachel Green - Data Analyst\nrachel.g@data.net\n\nEXPERIENCE\nData Analyst | Tableau\nJun 2018 - Present\nBuilt business intelligence dashboards.\n\nEDUCATION\nMaster of Science in Analytics\n\nSKILLS\nTableau, SQL, Data Analysis, Excel",
        "gt": {"title": "Data Analyst", "yoe": 8, "skills": ["Tableau", "SQL", "Data Analysis", "Excel"], "education": "MS", "certifications": []}
    },
    {
        "text": "Samuel Baker | Game Developer\nsam.baker@games.com\n\nExperience\nGame Developer, Epic Games\nJan 2019 - Present\nDeveloped gameplay mechanics in Unreal Engine.\n\nJunior Programmer, Indie Studio\nJul 2016 - Dec 2018\nWrote Unity scripts.\n\nEducation\nBachelors in Game Design\n\nSkills\nC++, Unreal Engine, Unity, C#",
        "gt": {"title": "Game Developer", "yoe": 9, "skills": ["C++", "Unreal Engine", "Unity", "C#"], "education": "BS", "certifications": []}
    },
    {
        "text": "Tina Adams - IT Support Specialist\ntina.a@it.com\n\nExperience:\nIT Support Specialist, TechCare\nFeb 2017 - Present\nProvided Tier 2 support.\n\nEducation:\nDiploma in Computer Applications\n\nSkills:\nIT Support, Troubleshooting, Windows Server, Active Directory",
        "gt": {"title": "IT Support Specialist", "yoe": 9, "skills": ["IT Support", "Troubleshooting", "Windows Server", "Active Directory"], "education": "Diploma", "certifications": []}
    },
    {
        "text": "Uma Patel | Solutions Architect\numa.p@solutions.com\n\nWork History\nSolutions Architect - Microsoft\nNov 2018 - Present\nDesigned Azure architectures.\n\nEducation\nM.Tech in Computer Science\n\nCertifications\nAzure Fundamentals\n\nSkills\nAzure, Cloud Computing, System Design",
        "gt": {"title": "Solutions Architect", "yoe": 7, "skills": ["Azure", "Cloud Computing", "System Design"], "education": "MTech", "certifications": ["Azure Fundamentals"]}
    },
    {
        "text": "Victor Cruz - Embedded Systems Engineer\nvictor.cruz@hardware.com\n\nExperience\nEmbedded Engineer, Intel\nJan 2015 - Present\nDeveloped firmware for IoT devices.\n\nEducation\nB.E. Electrical Engineering\n\nSkills\nC, C++, Firmware, IoT, Microcontrollers",
        "gt": {"title": "Embedded Engineer", "yoe": 11, "skills": ["C", "C++", "Firmware", "IoT", "Microcontrollers"], "education": "BE", "certifications": []}
    },
    {
        "text": "Wendy Hill\nwendy.h@software.com\n\nExperience:\nSoftware Engineer, IBM\nOct 2017 - Present\nMaintained enterprise Java applications.\n\nEducation:\nBS Computer Science\n\nSkills:\nJava, Spring, Enterprise Software",
        "gt": {"title": "Software Engineer", "yoe": 8, "skills": ["Java", "Spring", "Enterprise Software"], "education": "BS", "certifications": []}
    },
    {
        "text": "Xavier Long | Tech Lead\nxavier.l@startup.io\n\nExperience\nTech Lead @ FastGrowth\nJan 2021 - Present\nLed a team of 10 engineers.\n\nSenior Developer @ MediumCorp\nMar 2015 - Dec 2020\nBuilt core infrastructure.\n\nEducation\nPh.D. in Computer Science\n\nSkills\nLeadership, System Architecture, Node.js, React",
        "gt": {"title": "Tech Lead", "yoe": 11, "skills": ["Leadership", "System Architecture", "Node.js", "React"], "education": "PhD", "certifications": []}
    },
    {
        "text": "Yara Silva - Web Developer\nyara.s@webdev.com\n\nWork Experience\nWeb Developer, Digital Agency\nApril 2019 - Present\nCreated WordPress sites.\n\nEducation\nBA Graphic Design\n\nSkills\nWordPress, PHP, HTML, CSS",
        "gt": {"title": "Web Developer", "yoe": 7, "skills": ["WordPress", "PHP", "HTML", "CSS"], "education": "BA", "certifications": []}
    }
]

async def run_validation():
    # Dummy job req
    job_req = {
        "title": "Software Engineer",
        "family": "Software Engineer",
        "title_terms": ["software", "engineer", "backend", "frontend", "developer"],
        "req_skills": ["python", "aws", "react", "java", "sql", "docker", "javascript"],
        "min_experience": 5,
        "education": "BS"
    }

    gt_cands = []
    parsed_cands = []
    
    precisions = []
    recalls = []
    title_accs = []
    yoe_errs = []

    all_fps = []
    all_fns = []

    out = "# REAL RESUME VALIDATION RAW DATA\n\n"

    for i, r in enumerate(MANUAL_RESUMES):
        text = r["text"]
        gt = r["gt"]
        
        parsed = await AIPipeline.parse_resume(text)
        
        ext_skills = [s["name"] for s in parsed.get("skills", [])]
        ext_title = parsed.get("current_title", "")
        ext_yoe = parsed.get("total_years_of_experience", 0)
        
        # Calculate metrics
        gt_s = set(s.lower() for s in gt["skills"])
        ext_s = set(s.lower() for s in ext_skills)
        tp = gt_s & ext_s
        fp = ext_s - gt_s
        fn = gt_s - ext_s
        
        for fp_skill in fp: all_fps.append(fp_skill)
        for fn_skill in fn: all_fns.append(fn_skill)
        
        prec = len(tp)/len(ext_s) if ext_s else 0
        rec = len(tp)/len(gt_s) if gt_s else 0
        
        precisions.append(prec)
        recalls.append(rec)
        
        # Fuzzy title match
        title_acc = 1 if any(word.lower() in ext_title.lower() for word in gt["title"].split()) else 0
        title_accs.append(title_acc)
        
        yoe_errs.append(abs(ext_yoe - gt["yoe"]))
        
        # Output raw data for user
        out += f"## Resume {i+1}\n"
        out += "### Raw Extracted Text\n```text\n" + text + "\n```\n\n"
        out += "### Parsed JSON\n```json\n" + json.dumps(parsed, indent=2) + "\n```\n\n"
        out += f"**Extracted Skills**: {ext_skills}\n"
        out += f"**Extracted Experience**: {len(parsed.get('experiences', []))} entries\n"
        out += f"**Extracted Education**: {[e['degree'] for e in parsed.get('education', [])]}\n"
        out += f"**Extracted Certifications**: {parsed.get('certifications', [])}\n\n"

        # Prepare for ranking
        # Ground Truth candidate
        # Map GT to dict expected by V2 ranker
        yoe = gt["yoe"]
        sy = 2026 - yoe
        exps = [
            {
                "title": gt["title"],
                "company": "Company",
                "start_date": f"Jan {sy}",
                "end_date": "Present",
                "duration_months": yoe * 12,
                "bullets": ["Work"]
            }
        ]
        gt_mapped = {
            "current_title": gt["title"],
            "total_years_of_experience": yoe,
            "skills": [{"name": s, "type": "hard"} for s in gt["skills"]],
            "education": [{"degree": gt["education"], "institution": "University"}],
            "certifications": gt["certifications"],
            "experiences": exps,
        }
        gt_cands.append({"id": f"gt_{i}", "parsed_data": gt_mapped})
        
        # Parsed candidate
        parsed_cands.append({"id": f"pa_{i}", "parsed_data": parsed})

    # Ranking
    ranked_gt = await rank_candidates_for_job("test", job_req, gt_cands)
    ranked_pa = await rank_candidates_for_job("test", job_req, parsed_cands)

    gt_ranks = {r["id"]: r["rank"] for r in ranked_gt["results"]}
    pa_ranks = {r["id"]: r["rank"] for r in ranked_pa["results"]}

    shifts = []
    for i in range(25):
        gt_id = f"gt_{i}"
        pa_id = f"pa_{i}"
        gt_r = gt_ranks[gt_id]
        pa_r = pa_ranks[pa_id]
        shifts.append(abs(gt_r - pa_r))
        
    shifts.sort()
    mean_shift = sum(shifts) / len(shifts)
    median_shift = shifts[len(shifts)//2]
    p95_shift = shifts[int(len(shifts)*0.95)]
    max_shift = shifts[-1]

    mean_prec = sum(precisions) / len(precisions)
    mean_rec = sum(recalls) / len(recalls)
    mean_title = sum(title_accs) / len(title_accs)
    mean_yoe = sum(yoe_errs) / len(yoe_errs)

    out += "## COMPUTED METRICS\n"
    out += f"Skill Precision: {mean_prec*100:.2f}%\n"
    out += f"Skill Recall: {mean_rec*100:.2f}%\n"
    out += f"Title Accuracy: {mean_title*100:.2f}%\n"
    out += f"Years of Experience Error: {mean_yoe:.2f} years\n\n"
    
    out += "## RANK SHIFTS\n"
    out += f"Mean Rank Shift: {mean_shift:.2f}\n"
    out += f"Median Rank Shift: {median_shift:.2f}\n"
    out += f"P95 Rank Shift: {p95_shift}\n"
    out += f"Max Rank Shift: {max_shift}\n\n"

    from collections import Counter
    fp_counts = Counter(all_fps)
    fn_counts = Counter(all_fns)
    
    out += "## TOP FALSE NEGATIVES\n"
    for k, v in fn_counts.most_common(20):
        out += f"- {k} ({v})\n"
        
    out += "\n## TOP FALSE POSITIVES\n"
    for k, v in fp_counts.most_common(20):
        out += f"- {k} ({v})\n"

    with open("real_validation_output.txt", "w", encoding="utf-8") as f:
        f.write(out)

if __name__ == "__main__":
    asyncio.run(run_validation())
