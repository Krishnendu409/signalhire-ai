# PHASE 7 — 200-RESUME VALIDATION REPORT

**Execution Timestamp**: 2026-06-13T17:56:18Z  
**Parser Runtime (200 docs)**: 20269.9 ms  
**Ranking Runtime (400 candidates)**: 383.0 ms  
**Total Runtime**: 20658.3 ms  

## COMPUTED METRICS
- Skill Precision: 85.71%
- Skill Recall: 95.19%
- Title Accuracy: 62.00%
- YOE Mean Error: 0.04 years

## RANK SHIFTS
- Mean: 16.70
- Median: 11.00
- P95: 55
- Max: 174

## TARGET VS ACTUAL
| Metric | Target | Actual | Pass? |
|--------|--------|--------|-------|
| Skill Precision | >=95% | 85.7% | FAIL |
| Skill Recall | >=95% | 95.2% | PASS |
| Title Accuracy | >=95% | 62.0% | FAIL |
| YOE Error | <=0.5yr | 0.04yr | PASS |
| Mean Rank Shift | <=2 | 16.70 | FAIL |
| Median Rank Shift | <=1 | 11.00 | FAIL |
| P95 Rank Shift | <=5 | 55 | FAIL |

## PER-RESUME EXTRACTION (ALL 200)
| ID | Extracted Title | GT Title | Title Match | Ext YOE | GT YOE | YOE Err | Skills Ext | Skills GT | Precision | Recall | Edu | Cert |
|----|----|----|----|----|----|----|----|----|----|----|----|-----|
| R001 | Senior Software Engineer | Senior Software Engineer | YES | 11 | 11 | 0 | 7 | 7 | 0.86 | 0.86 | 4 | 0 |
| R002 | Backend Engineer | Backend Engineer | YES | 9 | 9 | 0 | 6 | 6 | 1.00 | 1.00 | 4 | 0 |
| R003 | Full Stack Engineer | Full Stack Engineer | YES | 11 | 11 | 0 | 8 | 5 | 0.62 | 1.00 | 2 | 0 |
| R004 | Frontend Engineer | Frontend Developer | NO | 8 | 9 | 1 | 7 | 7 | 1.00 | 1.00 | 2 | 0 |
| R005 | Principal Engineer | Principal Engineer | YES | 11 | 11 | 0 | 5 | 5 | 1.00 | 1.00 | 3 | 0 |
| R006 | DevOps Engineer | DevOps Engineer | YES | 9 | 10 | 1 | 13 | 7 | 0.54 | 1.00 | 2 | 2 |
| R007 | Security Engineer | Security Engineer | YES | 9 | 10 | 1 | 9 | 5 | 0.56 | 1.00 | 3 | 2 |
| R008 | Cloud Architect | Cloud Architect | YES | 13 | 13 | 0 | 6 | 5 | 0.83 | 1.00 | 1 | 1 |
| R009 | iOS Developer | iOS Developer | YES | 11 | 11 | 0 | 5 | 5 | 1.00 | 1.00 | 3 | 0 |
| R010 | Data Engineer | Data Engineer | YES | 10 | 10 | 0 | 7 | 7 | 1.00 | 1.00 | 2 | 0 |
| R011 | Machine Learning Engineer | Machine Learning Engineer | YES | 8 | 8 | 0 | 6 | 6 | 1.00 | 1.00 | 3 | 0 |
| R012 | QA Automation Engineer | QA Automation Engineer | YES | 9 | 9 | 0 | 7 | 5 | 0.71 | 1.00 | 2 | 0 |
| R013 | Blockchain Developer | Blockchain Developer | YES | 8 | 8 | 0 | 5 | 5 | 1.00 | 1.00 | 3 | 0 |
| R014 | UI/UX Designer | UI/UX Designer | YES | 10 | 10 | 0 | 4 | 4 | 1.00 | 1.00 | 2 | 0 |
| R015 | Site Reliability Engineer | Site Reliability Engineer | YES | 10 | 11 | 1 | 9 | 7 | 0.78 | 1.00 | 3 | 0 |
| R016 | Network Engineer | Network Engineer | YES | 10 | 10 | 0 | 8 | 6 | 0.75 | 1.00 | 2 | 2 |
| R017 | Product Manager | Product Manager | YES | 9 | 9 | 0 | 6 | 5 | 0.83 | 1.00 | 4 | 0 |
| R018 | Data Analyst | Data Analyst | YES | 8 | 8 | 0 | 8 | 5 | 0.62 | 1.00 | 2 | 0 |
| R019 | Game Developer | Game Developer | YES | 9 | 10 | 1 | 5 | 5 | 1.00 | 1.00 | 4 | 0 |
| R020 | Embedded Systems Engineer | Embedded Systems Engineer | YES | 11 | 11 | 0 | 6 | 7 | 1.00 | 0.86 | 2 | 0 |
| R021 | Solutions Architect | Solutions Architect | YES | 8 | 8 | 0 | 5 | 5 | 1.00 | 1.00 | 2 | 1 |
| R022 | Web Developer | Web Developer | YES | 7 | 7 | 0 | 6 | 6 | 1.00 | 1.00 | 1 | 0 |
| R023 | Software Engineer | Software Engineer | YES | 9 | 9 | 0 | 3 | 4 | 1.00 | 0.75 | 2 | 0 |
| R024 | Tech Lead | Tech Lead | YES | 10 | 11 | 1 | 6 | 6 | 0.83 | 0.83 | 2 | 0 |
| R025 | IT Support Specialist | IT Support Specialist | YES | 9 | 9 | 0 | 5 | 4 | 0.80 | 1.00 | 1 | 0 |
| R026 | Data Scientist | Data Scientist | YES | 8 | 8 | 0 | 10 | 7 | 0.70 | 1.00 | 2 | 0 |
| R027 | MLOps Engineer | MLOps Engineer | YES | 5 | 5 | 0 | 9 | 6 | 0.67 | 1.00 | 1 | 1 |
| R028 | NLP Engineer | NLP Engineer | YES | 6 | 7 | 1 | 9 | 6 | 0.67 | 1.00 | 4 | 0 |
| R029 | Computer Vision Engineer | Computer Vision Engineer | YES | 7 | 7 | 0 | 7 | 7 | 1.00 | 1.00 | 1 | 0 |
| R030 | Business Intelligence Analyst | Business Intelligence Ana | YES | 7 | 7 | 0 | 8 | 6 | 0.75 | 1.00 | 2 | 0 |
| R031 | Data Engineer | Data Engineer | YES | 9 | 9 | 0 | 11 | 7 | 0.64 | 1.00 | 3 | 1 |
| R032 | Quantitative Analyst | Quantitative Analyst | YES | 11 | 11 | 0 | 6 | 6 | 1.00 | 1.00 | 2 | 0 |
| R033 | AI Researcher | AI Researcher | YES | 7 | 6 | 1 | 6 | 5 | 0.83 | 1.00 | 2 | 0 |
| R034 | Data Scientist | Data Scientist | YES | 8 | 8 | 0 | 9 | 7 | 0.78 | 1.00 | 1 | 0 |
| R035 | Machine Learning Engineer | Machine Learning Engineer | YES | 3 | 3 | 0 | 8 | 7 | 0.88 | 1.00 | 1 | 0 |
| R036 | Cloud Engineer | Cloud Engineer | YES | 8 | 8 | 0 | 10 | 7 | 0.70 | 1.00 | 1 | 1 |
| R037 | SRE GitLab | Site Reliability Engineer | NO | 5 | 5 | 0 | 10 | 7 | 0.70 | 1.00 | 3 | 0 |
| R038 | Infrastructure Engineer | Infrastructure Engineer | YES | 7 | 7 | 0 | 7 | 7 | 1.00 | 1.00 | 2 | 0 |
| R039 | Systems Architect Microsoft | Solutions Architect | NO | 8 | 8 | 0 | 6 | 5 | 0.83 | 1.00 | 3 | 1 |
| R040 | DevSecOps Engineer | DevOps Engineer | NO | 6 | 6 | 0 | 8 | 7 | 0.88 | 1.00 | 2 | 1 |
| R041 | Penetration Tester | Penetration Tester | YES | 10 | 10 | 0 | 8 | 4 | 0.50 | 1.00 | 3 | 2 |
| R042 | Malware Analyst | Malware Analyst | YES | 8 | 8 | 0 | 6 | 5 | 0.83 | 1.00 | 2 | 1 |
| R043 | Security Analyst | Security Analyst | YES | 9 | 9 | 0 | 7 | 6 | 0.86 | 1.00 | 1 | 1 |
| R044 | Cloud Security Engineer | Security Engineer | YES | 6 | 6 | 0 | 10 | 6 | 0.60 | 1.00 | 2 | 2 |
| R045 | GRC Analyst | GRC Analyst | YES | 8 | 8 | 0 | 4 | 4 | 0.75 | 0.75 | 3 | 1 |
| R046 | Network Administrator | Network Administrator | YES | 9 | 9 | 0 | 9 | 6 | 0.67 | 1.00 | 1 | 2 |
| R047 | Network Automation Engineer No | Network Engineer | NO | 8 | 8 | 0 | 7 | 6 | 0.86 | 1.00 | 2 | 1 |
| R048 | Android Developer | Android Developer | YES | 7 | 7 | 0 | 4 | 4 | 1.00 | 1.00 | 2 | 0 |
| R049 | Mobile Developer | Mobile Developer | YES | 6 | 6 | 0 | 7 | 6 | 0.86 | 1.00 | 2 | 0 |
| R050 | iOS Developer | iOS Developer | YES | 10 | 10 | 0 | 4 | 5 | 1.00 | 0.80 | 2 | 0 |
| R051 | Firmware Engineer | Firmware Engineer | YES | 10 | 10 | 0 | 6 | 7 | 1.00 | 0.86 | 1 | 0 |
| R052 | FPGA Engineer | FPGA Engineer | YES | 11 | 11 | 0 | 5 | 5 | 0.80 | 0.80 | 1 | 0 |
| R053 | ASIC Design Engineer | ASIC Design Engineer | YES | 10 | 10 | 0 | 5 | 6 | 1.00 | 0.83 | 1 | 0 |
| R054 | Embedded Linux Engineer | Embedded Systems Engineer | NO | 8 | 8 | 0 | 6 | 7 | 1.00 | 0.86 | 3 | 0 |
| R055 | Signal Processing Engineer | Signal Processing Enginee | YES | 9 | 9 | 0 | 5 | 5 | 0.80 | 0.80 | 3 | 0 |
| R056 | ADAS Engineer | ADAS Engineer | YES | 9 | 9 | 0 | 6 | 6 | 1.00 | 1.00 | 1 | 0 |
| R057 | Automotive Software Engineer | Automotive Software Engin | YES | 11 | 11 | 0 | 6 | 7 | 1.00 | 0.86 | 3 | 0 |
| R058 | Robotics Engineer | Robotics Engineer | YES | 8 | 8 | 0 | 6 | 6 | 1.00 | 1.00 | 2 | 0 |
| R059 | Manufacturing Engineer | Manufacturing Engineer | YES | 10 | 10 | 0 | 6 | 5 | 0.83 | 1.00 | 3 | 1 |
| R060 | PLC/SCADA Engineer Siemens | Manufacturing Engineer | NO | 11 | 11 | 0 | 4 | 5 | 1.00 | 0.80 | 2 | 0 |
| R061 | Quality Engineer | Quality Engineer | YES | 9 | 9 | 0 | 5 | 4 | 0.80 | 1.00 | 3 | 1 |
| R062 | CAD Engineer | CAD Engineer | YES | 8 | 8 | 0 | 3 | 5 | 0.67 | 0.40 | 2 | 0 |
| R063 | Renewable Energy Engineer Sola | Manufacturing Engineer | NO | 10 | 10 | 0 | 8 | 5 | 0.62 | 1.00 | 2 | 0 |
| R064 | Process Engineer Shell | Manufacturing Engineer | NO | 11 | 11 | 0 | 8 | 6 | 0.75 | 1.00 | 2 | 0 |
| R065 | Power Systems Engineer GE Powe | Manufacturing Engineer | NO | 9 | 9 | 0 | 7 | 5 | 0.71 | 1.00 | 2 | 0 |
| R066 | Software Engineer Finance | Software Engineer Finance | YES | 11 | 11 | 0 | 6 | 6 | 1.00 | 1.00 | 1 | 0 |
| R067 | Financial Analyst | Financial Analyst | YES | 10 | 10 | 0 | 6 | 5 | 0.83 | 1.00 | 4 | 0 |
| R068 | AML Analyst HSBC | Risk Analyst | NO | 8 | 8 | 0 | 7 | 6 | 0.86 | 1.00 | 2 | 0 |
| R069 | Payment Systems Engineer PayPa | Software Engineer | NO | 9 | 9 | 0 | 7 | 6 | 0.86 | 1.00 | 2 | 0 |
| R070 | SAP Consultant Infosys | IT Consultant | NO | 12 | 12 | 0 | 5 | 5 | 0.80 | 0.80 | 3 | 0 |
| R071 | Healthcare IT Engineer | Healthcare IT Engineer | YES | 9 | 9 | 0 | 7 | 5 | 0.71 | 1.00 | 2 | 0 |
| R072 | Bioinformatics Scientist | Bioinformatics Scientist | YES | 10 | 10 | 0 | 6 | 6 | 0.83 | 0.83 | 1 | 0 |
| R073 | Medical Device Engineer | Medical Device Engineer | YES | 11 | 11 | 0 | 6 | 6 | 0.83 | 0.83 | 3 | 0 |
| R074 | Data Analyst | Data Analyst | YES | 9 | 9 | 0 | 8 | 6 | 0.62 | 0.83 | 1 | 0 |
| R075 | Salesforce Developer | Salesforce Developer | YES | 8 | 8 | 0 | 5 | 5 | 1.00 | 1.00 | 1 | 0 |
| R076 | Digital Marketing Manager | Digital Marketing Manager | YES | 9 | 9 | 0 | 7 | 6 | 0.86 | 1.00 | 3 | 0 |
| R077 | Growth Hacker | Software Engineer | NO | 7 | 7 | 0 | 6 | 6 | 1.00 | 1.00 | 2 | 0 |
| R078 | CRM Manager | CRM Manager | YES | 10 | 10 | 0 | 6 | 5 | 0.83 | 1.00 | 1 | 0 |
| R079 | SEO Specialist | SEO Specialist | YES | 8 | 8 | 0 | 6 | 5 | 0.83 | 1.00 | 1 | 0 |
| R080 | Software Sales Engineer | Software Sales Engineer | YES | 9 | 9 | 0 | 6 | 6 | 1.00 | 1.00 | 1 | 0 |
| R081 | Backend Engineer | Backend Engineer | YES | 6 | 6 | 0 | 8 | 7 | 0.88 | 1.00 | 3 | 0 |
| R082 | Full Stack Developer | Full Stack Engineer | NO | 7 | 7 | 0 | 6 | 7 | 1.00 | 0.86 | 2 | 0 |
| R083 | Machine Learning Engineer | Machine Learning Engineer | YES | 6 | 6 | 0 | 6 | 6 | 1.00 | 1.00 | 2 | 0 |
| R084 | DevSecOps Engineer | DevOps Engineer | NO | 7 | 7 | 0 | 8 | 7 | 0.88 | 1.00 | 2 | 1 |
| R085 | Data Architect | Data Architect | YES | 10 | 10 | 0 | 7 | 7 | 1.00 | 1.00 | 2 | 0 |
| R086 | Android Developer | Android Developer | YES | 8 | 8 | 0 | 6 | 6 | 1.00 | 1.00 | 2 | 0 |
| R087 | Game Developer | Game Developer | YES | 6 | 6 | 0 | 5 | 4 | 0.80 | 1.00 | 2 | 0 |
| R088 | Tableau Developer | BI Developer | NO | 8 | 8 | 0 | 8 | 6 | 0.75 | 1.00 | 1 | 0 |
| R089 | Scrum Master | Scrum Master | YES | 10 | 10 | 0 | 6 | 5 | 0.83 | 1.00 | 4 | 1 |
| R090 | Business Analyst | Business Analyst | YES | 10 | 10 | 0 | 6 | 6 | 1.00 | 1.00 | 3 | 0 |
| R091 | Backend Engineer | Backend Engineer | YES | 8 | 8 | 0 | 8 | 7 | 0.75 | 0.86 | 3 | 0 |
| R092 | Frontend Engineer | Frontend Engineer | YES | 7 | 7 | 0 | 6 | 6 | 1.00 | 1.00 | 1 | 0 |
| R093 | Platform Engineer | Platform Engineer | YES | 6 | 6 | 0 | 9 | 7 | 0.78 | 1.00 | 4 | 0 |
| R094 | Spark Developer | Data Engineer | NO | 8 | 8 | 0 | 12 | 7 | 0.58 | 1.00 | 2 | 1 |
| R095 | Full Stack Engineer | Full Stack Engineer | YES | 9 | 9 | 0 | 8 | 7 | 0.88 | 1.00 | 2 | 0 |
| R096 | Software Engineering Manager | Software Engineering Mana | YES | 4 | 4 | 0 | 6 | 5 | 0.67 | 0.80 | 2 | 0 |
| R097 | IT Manager | IT Manager | YES | 12 | 12 | 0 | 7 | 5 | 0.71 | 1.00 | 3 | 1 |
| R098 | Technical Writer | Technical Writer | YES | 9 | 9 | 0 | 4 | 4 | 0.75 | 0.75 | 3 | 0 |
| R099 | Data Scientist | Data Scientist | YES | 9 | 9 | 0 | 9 | 7 | 0.78 | 1.00 | 1 | 0 |
| R100 | CI/CD Engineer CircleCI | DevOps Engineer | NO | 7 | 7 | 0 | 9 | 7 | 0.78 | 1.00 | 2 | 0 |
| R101 | Solutions Architect | Cloud Architect | NO | 9 | 9 | 0 | 9 | 6 | 0.67 | 1.00 | 2 | 1 |
| R102 | Data Engineer | Data Engineer | YES | 8 | 8 | 0 | 10 | 7 | 0.70 | 1.00 | 1 | 1 |
| R103 | Frontend Engineer | Frontend Engineer | YES | 7 | 7 | 0 | 7 | 8 | 1.00 | 0.88 | 1 | 0 |
| R104 | Backend Engineer | Backend Engineer | YES | 8 | 8 | 0 | 8 | 7 | 0.88 | 1.00 | 4 | 0 |
| R105 | NLP Engineer | NLP Engineer | YES | 10 | 10 | 0 | 8 | 7 | 0.88 | 1.00 | 2 | 0 |
| R106 | Identity Management Engineer O | Security Engineer | NO | 8 | 8 | 0 | 5 | 6 | 1.00 | 0.83 | 2 | 0 |
| R107 | Power BI Developer | Power BI Developer | YES | 8 | 8 | 0 | 8 | 6 | 0.75 | 1.00 | 1 | 0 |
| R108 | Kafka Engineer | Data Engineer | NO | 9 | 9 | 0 | 8 | 7 | 0.88 | 1.00 | 2 | 0 |
| R109 | Ruby on Rails Engineer Basecam | Backend Engineer | NO | 9 | 9 | 0 | 7 | 7 | 1.00 | 1.00 | 3 | 0 |
| R110 | iOS Developer | iOS Developer | YES | 11 | 11 | 0 | 5 | 6 | 1.00 | 0.83 | 3 | 0 |
| R111 | Vue.js Developer TikTok | Frontend Engineer | NO | 6 | 6 | 0 | 7 | 7 | 1.00 | 1.00 | 1 | 0 |
| R112 | Backend Python Developer Pinte | Backend Engineer | NO | 10 | 10 | 0 | 6 | 6 | 1.00 | 1.00 | 3 | 0 |
| R113 | Senior UX Designer | UI/UX Designer | NO | 10 | 10 | 0 | 6 | 5 | 0.83 | 1.00 | 3 | 0 |
| R114 | C++ Engineer Qualcomm | Embedded Systems Engineer | NO | 10 | 10 | 0 | 7 | 7 | 0.86 | 0.86 | 2 | 0 |
| R115 | Microservices Architect Lyft | Software Architect | NO | 9 | 9 | 0 | 7 | 7 | 1.00 | 1.00 | 2 | 0 |
| R116 | Terraform Engineer HashiCorp | DevOps Engineer | NO | 8 | 8 | 0 | 7 | 6 | 0.86 | 1.00 | 2 | 1 |
| R117 | Search Engineer | Search Engineer | YES | 9 | 9 | 0 | 6 | 5 | 0.67 | 0.80 | 2 | 0 |
| R118 | PHP Developer | PHP Developer | YES | 8 | 8 | 0 | 7 | 7 | 1.00 | 1.00 | 2 | 0 |
| R119 | Senior Product Manager | Senior Product Manager | YES | 9 | 9 | 0 | 8 | 7 | 0.88 | 1.00 | 3 | 1 |
| R120 | Systems Engineer Mozilla | Software Engineer | NO | 9 | 9 | 0 | 5 | 6 | 1.00 | 0.83 | 2 | 0 |
| R121 | AWS Solutions Engineer Amazon | Cloud Architect | NO | 10 | 10 | 0 | 6 | 6 | 1.00 | 1.00 | 2 | 0 |
| R122 | Data Engineer | Data Engineer | YES | 10 | 10 | 0 | 8 | 6 | 0.75 | 1.00 | 1 | 0 |
| R123 | Data Engineer | Data Engineer | YES | 9 | 9 | 0 | 7 | 7 | 1.00 | 1.00 | 1 | 0 |
| R124 | Penetration Tester | Penetration Tester | YES | 8 | 8 | 0 | 7 | 5 | 0.71 | 1.00 | 3 | 1 |
| R125 | Risk Analyst | Risk Analyst | YES | 11 | 11 | 0 | 6 | 7 | 1.00 | 0.86 | 2 | 0 |
| R126 | RPA Engineer UiPath | Software Engineer | NO | 7 | 7 | 0 | 6 | 5 | 0.83 | 1.00 | 1 | 0 |
| R127 | UI Developer | Frontend Engineer | NO | 8 | 8 | 0 | 7 | 7 | 1.00 | 1.00 | 1 | 0 |
| R128 | Kubernetes Administrator Digit | DevOps Engineer | NO | 9 | 9 | 0 | 9 | 7 | 0.78 | 1.00 | 3 | 1 |
| R129 | Python API Developer Fastly | Backend Engineer | NO | 7 | 7 | 0 | 8 | 7 | 0.88 | 1.00 | 1 | 0 |
| R130 | Supply Chain Engineer | IT Consultant | NO | 10 | 10 | 0 | 7 | 6 | 0.71 | 0.83 | 2 | 0 |
| R131 | Product Designer | Product Designer | YES | 6 | 6 | 0 | 5 | 4 | 0.80 | 1.00 | 2 | 0 |
| R132 | Observability Engineer Datadog | DevOps Engineer | NO | 8 | 8 | 0 | 8 | 7 | 0.88 | 1.00 | 3 | 0 |
| R133 | Mobile Developer | Mobile Developer | YES | 7 | 7 | 0 | 7 | 6 | 0.86 | 1.00 | 2 | 0 |
| R134 | IoT Engineer Bosch | Embedded Systems Engineer | NO | 10 | 10 | 0 | 6 | 7 | 1.00 | 0.86 | 2 | 0 |
| R135 | SAP ABAP Developer SAP | Software Engineer | NO | 12 | 12 | 0 | 5 | 5 | 0.80 | 0.80 | 3 | 0 |
| R136 | HPC Engineer NVIDIA | Software Engineer | NO | 10 | 10 | 0 | 6 | 6 | 1.00 | 1.00 | 1 | 0 |
| R137 | Data Analyst | Data Analyst | YES | 9 | 9 | 0 | 6 | 6 | 1.00 | 1.00 | 1 | 0 |
| R138 | Backend Engineer | Backend Engineer | YES | 8 | 8 | 0 | 9 | 7 | 0.67 | 0.86 | 1 | 0 |
| R139 | Data Analyst | Data Analyst | YES | 10 | 10 | 0 | 6 | 6 | 0.83 | 0.83 | 2 | 0 |
| R140 | Senior DevOps Engineer | Senior DevOps Engineer | YES | 10 | 10 | 0 | 8 | 7 | 0.88 | 1.00 | 2 | 0 |
| R141 | Java Spring Engineer Pivotal | Backend Engineer | NO | 11 | 11 | 0 | 7 | 7 | 1.00 | 1.00 | 1 | 0 |
| R142 | Senior ML Engineer | Senior ML Engineer | YES | 10 | 10 | 0 | 7 | 7 | 1.00 | 1.00 | 2 | 0 |
| R143 | Elixir Developer Discord | Backend Engineer | NO | 8 | 8 | 0 | 6 | 6 | 1.00 | 1.00 | 2 | 0 |
| R144 | Security Architect | Security Architect | YES | 12 | 12 | 0 | 6 | 5 | 0.83 | 1.00 | 3 | 2 |
| R145 | Go Developer HashiCorp | Backend Engineer | NO | 8 | 8 | 0 | 9 | 7 | 0.78 | 1.00 | 2 | 0 |
| R146 | Marketing Automation Specialis | Digital Marketing Manager | NO | 9 | 9 | 0 | 5 | 5 | 1.00 | 1.00 | 1 | 0 |
| R147 | Research Scientist | Computer Vision Engineer | NO | 9 | 9 | 0 | 7 | 7 | 1.00 | 1.00 | 1 | 0 |
| R148 | ERP Consultant Oracle | IT Consultant | NO | 12 | 12 | 0 | 6 | 6 | 0.83 | 0.83 | 3 | 0 |
| R149 | Pipeline Engineer Airbnb | Data Engineer | NO | 8 | 8 | 0 | 9 | 6 | 0.67 | 1.00 | 1 | 0 |
| R150 | Penetration Tester | Penetration Tester | YES | 9 | 9 | 0 | 8 | 6 | 0.75 | 1.00 | 2 | 2 |
| R151 | Data Analyst | Data Analyst | YES | 7 | 7 | 0 | 10 | 6 | 0.60 | 1.00 | 2 | 1 |
| R152 | Django Developer Automattic | Backend Engineer | NO | 8 | 8 | 0 | 6 | 6 | 1.00 | 1.00 | 2 | 0 |
| R153 | UX Researcher Google | UI/UX Designer | NO | 9 | 9 | 0 | 5 | 5 | 0.80 | 0.80 | 2 | 0 |
| R154 | Network Engineer | Network Engineer | YES | 10 | 10 | 0 | 10 | 7 | 0.70 | 1.00 | 1 | 2 |
| R155 | Statistician WHO | Data Analyst | NO | 10 | 10 | 0 | 6 | 6 | 0.83 | 0.83 | 1 | 0 |
| R156 | Machine Learning Engineer | Machine Learning Engineer | YES | 4 | 4 | 0 | 8 | 7 | 0.88 | 1.00 | 1 | 0 |
| R157 | SCADA Engineer ABB | Manufacturing Engineer | NO | 11 | 11 | 0 | 4 | 5 | 1.00 | 0.80 | 2 | 0 |
| R158 | Service Mesh Engineer Lyft | Platform Engineer | NO | 7 | 7 | 0 | 8 | 7 | 0.88 | 1.00 | 3 | 0 |
| R159 | Electron Developer Slack | Frontend Engineer | NO | 8 | 8 | 0 | 6 | 7 | 1.00 | 0.86 | 2 | 0 |
| R160 | LegalTech Engineer Thomson Reu | Software Engineer | NO | 9 | 9 | 0 | 6 | 6 | 1.00 | 1.00 | 2 | 0 |
| R161 | Backend Engineer | Backend Engineer | YES | 8 | 8 | 0 | 7 | 7 | 1.00 | 1.00 | 3 | 0 |
| R162 | Data Engineer | Data Engineer | YES | 10 | 10 | 0 | 8 | 7 | 0.88 | 1.00 | 2 | 0 |
| R163 | WebAssembly Engineer Fastly | Software Engineer | NO | 7 | 7 | 0 | 7 | 6 | 0.86 | 1.00 | 2 | 0 |
| R164 | Medical Informatics Analyst Ma | Healthcare IT Engineer | NO | 10 | 10 | 0 | 9 | 7 | 0.78 | 1.00 | 2 | 0 |
| R165 | Algorithmic Trading Engineer B | Software Engineer Finance | NO | 11 | 11 | 0 | 7 | 6 | 0.86 | 1.00 | 2 | 0 |
| R166 | Power BI Manager Walmart | BI Developer | NO | 9 | 9 | 0 | 9 | 6 | 0.67 | 1.00 | 1 | 0 |
| R167 | Unity Engineer EA Games | Game Developer | NO | 9 | 9 | 0 | 7 | 5 | 0.71 | 1.00 | 2 | 0 |
| R168 | Systems Administrator | Systems Administrator | YES | 12 | 12 | 0 | 7 | 7 | 1.00 | 1.00 | 2 | 1 |
| R169 | Qlik Developer Gartner | BI Developer | NO | 8 | 8 | 0 | 9 | 6 | 0.67 | 1.00 | 1 | 0 |
| R170 | Compliance Officer Barclays | GRC Analyst | NO | 11 | 11 | 0 | 5 | 5 | 0.60 | 0.60 | 3 | 1 |
| R171 | Microcontroller Engineer STMic | Embedded Systems Engineer | NO | 10 | 10 | 0 | 6 | 7 | 1.00 | 0.86 | 2 | 0 |
| R172 | Machine Learning Engineer | Machine Learning Engineer | YES | 3 | 3 | 0 | 8 | 7 | 0.88 | 1.00 | 2 | 0 |
| R173 | Supply Chain Manager Amazon | IT Consultant | NO | 11 | 11 | 0 | 7 | 7 | 0.86 | 0.86 | 2 | 0 |
| R174 | Mainframe Developer IBM | Software Engineer | NO | 16 | 16 | 0 | 5 | 6 | 1.00 | 0.83 | 3 | 0 |
| R175 | NLP Engineer | NLP Engineer | YES | 8 | 8 | 0 | 7 | 7 | 1.00 | 1.00 | 1 | 0 |
| R176 | PHP Developer | PHP Developer | YES | 9 | 9 | 0 | 7 | 7 | 1.00 | 1.00 | 1 | 0 |
| R177 | Analytics Engineer | Analytics Engineer | YES | 7 | 7 | 0 | 9 | 7 | 0.78 | 1.00 | 1 | 0 |
| R178 | CAD Engineer | CAD Engineer | YES | 11 | 11 | 0 | 3 | 5 | 0.67 | 0.40 | 3 | 0 |
| R179 | Malware Analyst | Security Analyst | NO | 8 | 8 | 0 | 7 | 6 | 0.86 | 1.00 | 2 | 1 |
| R180 | Data Engineer | Data Engineer | YES | 9 | 9 | 0 | 10 | 7 | 0.70 | 1.00 | 2 | 0 |
| R181 | iOS Developer | iOS Developer | YES | 11 | 11 | 0 | 5 | 6 | 1.00 | 0.83 | 2 | 0 |
| R182 | Security Engineer | Security Engineer | YES | 7 | 7 | 0 | 8 | 7 | 0.88 | 1.00 | 3 | 1 |
| R183 | GraphQL Engineer Prisma | Backend Engineer | NO | 7 | 7 | 0 | 7 | 7 | 0.86 | 0.86 | 1 | 0 |
| R184 | MLOps Engineer | MLOps Engineer | YES | 8 | 8 | 0 | 9 | 7 | 0.78 | 1.00 | 3 | 0 |
| R185 | Grid Systems Engineer Siemens  | Manufacturing Engineer | NO | 10 | 10 | 0 | 6 | 5 | 0.83 | 1.00 | 2 | 0 |
| R186 | Flutter Senior Developer Googl | Mobile Developer | NO | 7 | 7 | 0 | 8 | 7 | 0.88 | 1.00 | 3 | 0 |
| R187 | C# .NET Engineer Microsoft | Backend Engineer | NO | 11 | 11 | 0 | 7 | 6 | 0.86 | 1.00 | 2 | 0 |
| R188 | Deep Learning Researcher Stanf | AI Researcher | NO | 7 | 7 | 0 | 7 | 7 | 1.00 | 1.00 | 2 | 0 |
| R189 | PCB Design Engineer Cisco Hard | Hardware Engineer | NO | 10 | 10 | 0 | 4 | 4 | 0.75 | 0.75 | 2 | 0 |
| R190 | RPA Developer UiPath | Software Engineer | NO | 7 | 7 | 0 | 5 | 5 | 1.00 | 1.00 | 1 | 0 |
| R191 | Search Engineer | Search Engineer | YES | 8 | 8 | 0 | 8 | 7 | 0.88 | 1.00 | 1 | 0 |
| R192 | Bioinformatics Scientist | Bioinformatics Scientist | YES | 9 | 9 | 0 | 5 | 6 | 1.00 | 0.83 | 2 | 0 |
| R193 | Open Source Developer Apache F | Software Engineer | NO | 11 | 11 | 0 | 8 | 7 | 0.88 | 1.00 | 1 | 0 |
| R194 | Product Owner | Product Owner | YES | 9 | 9 | 0 | 7 | 6 | 0.86 | 1.00 | 3 | 1 |
| R195 | Monitoring Engineer New Relic | DevOps Engineer | NO | 8 | 8 | 0 | 8 | 7 | 0.88 | 1.00 | 3 | 1 |
| R196 | Lean Manufacturing Consultant  | Manufacturing Engineer | NO | 12 | 12 | 0 | 7 | 5 | 0.71 | 1.00 | 3 | 1 |
| R197 | CTO Fintech Startup | CTO | YES | 8 | 8 | 0 | 6 | 6 | 1.00 | 1.00 | 2 | 0 |
| R198 | Data Scientist | Data Scientist | YES | 7 | 7 | 0 | 9 | 7 | 0.78 | 1.00 | 3 | 0 |
| R199 | Platform Engineer | Embedded Systems Engineer | NO | 9 | 9 | 0 | 7 | 8 | 1.00 | 0.88 | 3 | 0 |
| R200 | Full Stack Engineer | Full Stack Engineer | YES | 9 | 9 | 0 | 9 | 8 | 0.78 | 0.88 | 2 | 0 |

## TOP 25 FALSE NEGATIVES (missed skills)
- c (15)
- node.js (10)
- r (6)
- erp (5)
- swiftui (3)
- iso 27001 (2)
- catia (2)
- fea (2)
- solidworks (2)
- enterprise software (1)
- rtl design (1)
- digital design (1)
- documentation (1)
- security (1)
- kibana (1)
- user research (1)
- gdpr (1)

## TOP 25 FALSE POSITIVES (extra skills)
- apache (10)
- power platform (8)
- javascript (7)
- aws certified solutions architect (7)
- monitoring (7)
- statistics (7)
- git (6)
- cissp (6)
- data science (6)
- research (5)
- enterprise resource planning (5)
- payment systems (4)
- devops (4)
- ccnp (4)
- data analysis (4)
- plc programming (4)
- cka (3)
- ceh (3)
- ccna (3)
- databricks (3)
- sql (3)
- llms (3)
- google cloud platform (3)
- aws (3)
- financial analysis (3)

## RESUME SOURCE LIST
Source: 200 Manually Curated Resumes — Multi-industry (Software, Data, Cloud, Security, Networking, Mobile, Embedded, Automotive, Manufacturing, Energy, Finance, Healthcare, Sales, Marketing)
Format: Plain text resume layouts (not generated by reportlab, not synthetic benchmark)