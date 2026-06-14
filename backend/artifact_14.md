# Artifact 14 — REAL RESUME VALIDATION

## Real Resume 1: real_resume_1.pdf
### Raw Extracted Text
```text
JOHN DOE - Senior Developer
john.doe@gmail.com
---
CAREER PROFILE
Over 8 years of creating amazing user experiences using React and Node.js.
WORK HISTORY
- Senior Developer at TechCorp
  August 2018 to Current
  Built scalable microservices in Node.js.
- Developer at WebSolutions
  March 2015 to July 2018
  Maintained React applications.
EDUCATION
Master of Science in Computer Science, State University
2014
SKILLS
React, Node.js, TypeScript, PostgreSQL, AWS...
```

### Parsed Output
```json
{
  "full_name": "---",
  "current_title": "- Senior Developer at TechCorp",
  "total_years_of_experience": 11,
  "current_employment_status": "Employed",
  "open_to_work": true,
  "notice_period": 30,
  "expected_salary": 0,
  "summary": "Deterministically extracted resume profile.",
  "contact": {
    "email": "john.doe@gmail.com",
    "phone": ""
  },
  "experiences": [
    {
      "title": "- Senior Developer at TechCorp",
      "company": "Company",
      "start_date": "August 2018",
      "end_date": "Current",
      "duration_months": 96,
      "bullets": [
        "Built scalable microservices in Node.js. - Developer at WebSolutions"
      ]
    },
    {
      "title": "Built scalable microservices in Node.js.",
      "company": "- Developer at WebSolutions",
      "start_date": "March 2015",
      "end_date": "July 2018",
      "duration_months": 36,
      "bullets": [
        "Maintained React applications."
      ]
    }
  ],
  "education": [
    {
      "degree": "MS",
      "institution": "University"
    }
  ],
  "skills": [
    {
      "name": "AWS",
      "type": "hard"
    },
    {
      "name": "TypeScript",
      "type": "hard"
    },
    {
      "name": "Microservices",
      "type": "hard"
    },
    {
      "name": "PostgreSQL",
      "type": "hard"
    },
    {
      "name": "JavaScript",
      "type": "hard"
    },
    {
      "name": "Node.js",
      "type": "hard"
    },
    {
      "name": "React",
      "type": "hard"
    }
  ],
  "certifications": [],
  "projects": [],
  "career_gaps": [],
  "trajectory_events": []
}
```

**Skills:** ['AWS', 'TypeScript', 'Microservices', 'PostgreSQL', 'JavaScript', 'Node.js', 'React']
**Experiences:** 2 entries, 11 YOE
**Education:** ['MS']
**Certifications:** []

## Real Resume 2: real_resume_10.pdf
### Raw Extracted Text
```text
JAMES ANDERSON - Full Stack Developer
james.a@dev.net
Experience
Full Stack Developer
TechInnovators
Jan 2015 - Present
Built end-to-end features.
Education
MSc Computer Science
Skills
React, Node.js, MongoDB, JavaScript, TypeScript...
```

### Parsed Output
```json
{
  "full_name": "Experience",
  "current_title": "Full Stack Developer",
  "total_years_of_experience": 11,
  "current_employment_status": "Employed",
  "open_to_work": true,
  "notice_period": 30,
  "expected_salary": 0,
  "summary": "Deterministically extracted resume profile.",
  "contact": {
    "email": "james.a@dev.net",
    "phone": ""
  },
  "experiences": [
    {
      "title": "Full Stack Developer",
      "company": "TechInnovators",
      "start_date": "Jan 2015",
      "end_date": "Present",
      "duration_months": 132,
      "bullets": [
        "Built end-to-end features."
      ]
    }
  ],
  "education": [
    {
      "degree": "MSc",
      "institution": "University"
    }
  ],
  "skills": [
    {
      "name": "MongoDB",
      "type": "hard"
    },
    {
      "name": "TypeScript",
      "type": "hard"
    },
    {
      "name": "JavaScript",
      "type": "hard"
    },
    {
      "name": "Node.js",
      "type": "hard"
    },
    {
      "name": "React",
      "type": "hard"
    }
  ],
  "certifications": [],
  "projects": [],
  "career_gaps": [],
  "trajectory_events": []
}
```

**Skills:** ['MongoDB', 'TypeScript', 'JavaScript', 'Node.js', 'React']
**Experiences:** 1 entries, 11 YOE
**Education:** ['MSc']
**Certifications:** []

## Real Resume 3: real_resume_2.pdf
### Raw Extracted Text
```text
JANE SMITH | Data Scientist
janesmith@yahoo.com
Summary
Passionate data professional with 5+ yrs experience.
Experience
Data Scientist | AI Startup
Jan 2019 - Present
Trained deep learning models.
Data Analyst | BigBank
Jun 2016 - Dec 2018
Created SQL dashboards.
Education
BS in Mathematics
Technical Skills
Python, TensorFlow, PyTorch, SQL...
```

### Parsed Output
```json
{
  "full_name": "Summary",
  "current_title": "Data Scientist | AI Startup",
  "total_years_of_experience": 9,
  "current_employment_status": "Employed",
  "open_to_work": true,
  "notice_period": 30,
  "expected_salary": 0,
  "summary": "Deterministically extracted resume profile.",
  "contact": {
    "email": "janesmith@yahoo.com",
    "phone": ""
  },
  "experiences": [
    {
      "title": "Data Scientist | AI Startup",
      "company": "Company",
      "start_date": "Jan 2019",
      "end_date": "Present",
      "duration_months": 84,
      "bullets": [
        "Trained deep learning models. Data Analyst | BigBank"
      ]
    },
    {
      "title": "Trained deep learning models.",
      "company": "Data Analyst | BigBank",
      "start_date": "Jun 2016",
      "end_date": "Dec 2018",
      "duration_months": 24,
      "bullets": [
        "Created SQL dashboards."
      ]
    }
  ],
  "education": [
    {
      "degree": "BS",
      "institution": "University"
    }
  ],
  "skills": [
    {
      "name": "SQL",
      "type": "hard"
    },
    {
      "name": "Deep Learning",
      "type": "hard"
    }
  ],
  "certifications": [],
  "projects": [],
  "career_gaps": [],
  "trajectory_events": []
}
```

**Skills:** ['SQL', 'Deep Learning']
**Experiences:** 2 entries, 9 YOE
**Education:** ['BS']
**Certifications:** []

## Real Resume 4: real_resume_3.pdf
### Raw Extracted Text
```text
MICHAEL JOHNSON
mjohnson@outlook.com
Objective: Seeking a DevOps Engineer role.
Experience:
DevOps Engineer, CloudOps Inc. (Jan 2020 to Present)
Managed Kubernetes clusters.
SysAdmin, OnPrem Corp. (Feb 2017 to Dec 2019)
Administered Linux servers.
Education:
BTech
Certifications:
AWS Certified Solutions Architect
Skills:
Kubernetes, AWS, Docker, Bash...
```

### Parsed Output
```json
{
  "full_name": "MICHAEL JOHNSON",
  "current_title": "DevOps Engineer, CloudOps Inc. (",
  "total_years_of_experience": 8,
  "current_employment_status": "Employed",
  "open_to_work": true,
  "notice_period": 30,
  "expected_salary": 0,
  "summary": "Deterministically extracted resume profile.",
  "contact": {
    "email": "mjohnson@outlook.com",
    "phone": ""
  },
  "experiences": [
    {
      "title": "DevOps Engineer, CloudOps Inc. (",
      "company": "Company",
      "start_date": "Jan 2020",
      "end_date": "Present",
      "duration_months": 72,
      "bullets": [
        ") Managed Kubernetes clusters. SysAdmin, OnPrem Corp. ("
      ]
    },
    {
      "title": "Managed Kubernetes clusters.",
      "company": "SysAdmin, OnPrem Corp. (",
      "start_date": "Feb 2017",
      "end_date": "Dec 2019",
      "duration_months": 24,
      "bullets": [
        ") Administered Linux servers."
      ]
    }
  ],
  "education": [
    {
      "degree": "BTech",
      "institution": "University"
    }
  ],
  "skills": [
    {
      "name": "AWS",
      "type": "hard"
    },
    {
      "name": "Linux",
      "type": "hard"
    },
    {
      "name": "Kubernetes",
      "type": "hard"
    },
    {
      "name": "Docker",
      "type": "hard"
    }
  ],
  "certifications": [
    "AWS Certified Solutions Architect"
  ],
  "projects": [],
  "career_gaps": [],
  "trajectory_events": []
}
```

**Skills:** ['AWS', 'Linux', 'Kubernetes', 'Docker']
**Experiences:** 2 entries, 8 YOE
**Education:** ['BTech']
**Certifications:** ['AWS Certified Solutions Architect']

## Real Resume 5: real_resume_4.pdf
### Raw Extracted Text
```text
SARAH CONNOR - Product Manager
sarahc@example.com
EXPERIENCE
Product Manager
InnovateTech | Jan 2018 - Present
Led agile teams.
Business Analyst
Consulting LLC | Mar 2015 - Dec 2017
Gathered requirements.
EDUCATION
MBA - Business School
SKILLS
Agile, Scrum Master, JIRA, Product Management...
```

### Parsed Output
```json
{
  "full_name": "EXPERIENCE",
  "current_title": "Product Manager",
  "total_years_of_experience": 10,
  "current_employment_status": "Employed",
  "open_to_work": true,
  "notice_period": 30,
  "expected_salary": 0,
  "summary": "Deterministically extracted resume profile.",
  "contact": {
    "email": "sarahc@example.com",
    "phone": ""
  },
  "experiences": [
    {
      "title": "Product Manager",
      "company": "InnovateTech |",
      "start_date": "Jan 2018",
      "end_date": "Present",
      "duration_months": 96,
      "bullets": [
        "Led agile teams. Business Analyst Consulting LLC |"
      ]
    },
    {
      "title": "Business Analyst",
      "company": "Consulting LLC |",
      "start_date": "Mar 2015",
      "end_date": "Dec 2017",
      "duration_months": 24,
      "bullets": [
        "Gathered requirements."
      ]
    }
  ],
  "education": [
    {
      "degree": "MBA",
      "institution": "University"
    }
  ],
  "skills": [
    {
      "name": "Scrum",
      "type": "hard"
    },
    {
      "name": "Jira",
      "type": "hard"
    },
    {
      "name": "Agile",
      "type": "hard"
    }
  ],
  "certifications": [
    "Scrum Master"
  ],
  "projects": [],
  "career_gaps": [],
  "trajectory_events": []
}
```

**Skills:** ['Scrum', 'Jira', 'Agile']
**Experiences:** 2 entries, 10 YOE
**Education:** ['MBA']
**Certifications:** ['Scrum Master']

## Real Resume 6: real_resume_5.pdf
### Raw Extracted Text
```text
ALEX TURNER - Frontend Engineer
alex.turner@email.com
Employment:
Frontend Engineer - CreativeAgency
01/2021 to Present
Built responsive UIs.
Junior Web Developer - SmallStudio
05/2018 to 12/2020
Wrote HTML and CSS.
Education:
B.E. Computer Engineering
Skills:
JavaScript, HTML, CSS, React, UI/UX...
```

### Parsed Output
```json
{
  "full_name": "Employment:",
  "current_title": "Frontend Engineer - CreativeAgency",
  "total_years_of_experience": 5,
  "current_employment_status": "Employed",
  "open_to_work": true,
  "notice_period": 30,
  "expected_salary": 0,
  "summary": "Deterministically extracted resume profile.",
  "contact": {
    "email": "alex.turner@email.com",
    "phone": ""
  },
  "experiences": [],
  "education": [
    {
      "degree": "BE",
      "institution": "University"
    }
  ],
  "skills": [
    {
      "name": "UI/UX",
      "type": "hard"
    },
    {
      "name": "HTML",
      "type": "hard"
    },
    {
      "name": "JavaScript",
      "type": "hard"
    },
    {
      "name": "CSS",
      "type": "hard"
    },
    {
      "name": "React",
      "type": "hard"
    }
  ],
  "certifications": [],
  "projects": [],
  "career_gaps": [],
  "trajectory_events": []
}
```

**Skills:** ['UI/UX', 'HTML', 'JavaScript', 'CSS', 'React']
**Experiences:** 0 entries, 5 YOE
**Education:** ['BE']
**Certifications:** []

## Real Resume 7: real_resume_6.pdf
### Raw Extracted Text
```text
DAVID MILLER - Backend Developer
david.m@server.com
Profile
Backend specialist with 10 years of experience.
Work
Backend Developer @ SystemsGen
Jan 2014 to Present
Maintained APIs.
Education
Bachelors in CS
Skills
Java, Spring Boot, PostgreSQL, Microservices...
```

### Parsed Output
```json
{
  "full_name": "Profile",
  "current_title": "Backend Developer",
  "total_years_of_experience": 10,
  "current_employment_status": "Employed",
  "open_to_work": true,
  "notice_period": 30,
  "expected_salary": 0,
  "summary": "Deterministically extracted resume profile.",
  "contact": {
    "email": "david.m@server.com",
    "phone": ""
  },
  "experiences": [],
  "education": [
    {
      "degree": "BS",
      "institution": "University"
    }
  ],
  "skills": [
    {
      "name": "Java",
      "type": "hard"
    },
    {
      "name": "Spring",
      "type": "hard"
    },
    {
      "name": "PostgreSQL",
      "type": "hard"
    },
    {
      "name": "Microservices",
      "type": "hard"
    }
  ],
  "certifications": [],
  "projects": [],
  "career_gaps": [],
  "trajectory_events": []
}
```

**Skills:** ['Java', 'Spring', 'PostgreSQL', 'Microservices']
**Experiences:** 0 entries, 10 YOE
**Education:** ['BS']
**Certifications:** []

## Real Resume 8: real_resume_7.pdf
### Raw Extracted Text
```text
EMILY DAVIS
emilyd@design.com
Experience
UI/UX Designer
DesignStudio (Jan 2019 - Present)
Created mockups.
Education
BA Graphic Design
Skills
UI/UX, Figma, Adobe XD...
```

### Parsed Output
```json
{
  "full_name": "EMILY DAVIS",
  "current_title": "UI/UX Designer",
  "total_years_of_experience": 7,
  "current_employment_status": "Employed",
  "open_to_work": true,
  "notice_period": 30,
  "expected_salary": 0,
  "summary": "Deterministically extracted resume profile.",
  "contact": {
    "email": "emilyd@design.com",
    "phone": ""
  },
  "experiences": [
    {
      "title": "UI/UX Designer",
      "company": "DesignStudio (",
      "start_date": "Jan 2019",
      "end_date": "Present",
      "duration_months": 84,
      "bullets": [
        ") Created mockups."
      ]
    }
  ],
  "education": [
    {
      "degree": "BA",
      "institution": "University"
    }
  ],
  "skills": [
    {
      "name": "UI/UX",
      "type": "hard"
    }
  ],
  "certifications": [],
  "projects": [],
  "career_gaps": [],
  "trajectory_events": []
}
```

**Skills:** ['UI/UX']
**Experiences:** 1 entries, 7 YOE
**Education:** ['BA']
**Certifications:** []

## Real Resume 9: real_resume_8.pdf
### Raw Extracted Text
```text
ROBERT WILSON - Cloud Engineer
robertw@cloud.com
Experience
Cloud Engineer at SkyHigh Cloud
Feb 2018 - Present
Architected AWS infrastructure.
Education
B.S. Information Technology
Certifications
AWS Developer Associate, CKA
Skills
AWS, Kubernetes, Terraform, Python...
```

### Parsed Output
```json
{
  "full_name": "Experience",
  "current_title": "Cloud Engineer at SkyHigh Cloud",
  "total_years_of_experience": 8,
  "current_employment_status": "Employed",
  "open_to_work": true,
  "notice_period": 30,
  "expected_salary": 0,
  "summary": "Deterministically extracted resume profile.",
  "contact": {
    "email": "robertw@cloud.com",
    "phone": ""
  },
  "experiences": [
    {
      "title": "Cloud Engineer at SkyHigh Cloud",
      "company": "Company",
      "start_date": "Feb 2018",
      "end_date": "Present",
      "duration_months": 96,
      "bullets": [
        "Architected AWS infrastructure."
      ]
    }
  ],
  "education": [
    {
      "degree": "BS",
      "institution": "University"
    }
  ],
  "skills": [
    {
      "name": "AWS",
      "type": "hard"
    },
    {
      "name": "Python",
      "type": "hard"
    },
    {
      "name": "Kubernetes",
      "type": "hard"
    },
    {
      "name": "Terraform",
      "type": "hard"
    }
  ],
  "certifications": [
    "AWS Developer Associate",
    "CKA"
  ],
  "projects": [],
  "career_gaps": [],
  "trajectory_events": []
}
```

**Skills:** ['AWS', 'Python', 'Kubernetes', 'Terraform']
**Experiences:** 1 entries, 8 YOE
**Education:** ['BS']
**Certifications:** ['AWS Developer Associate', 'CKA']

## Real Resume 10: real_resume_9.pdf
### Raw Extracted Text
```text
LISA TAYLOR - QA Engineer
lisa.t@testing.org
Experience
QA Engineer, QualityFirst
Mar 2016 - Present
Wrote automation scripts.
Education
Diploma in IT
Skills
Selenium, Python, Cypress, Testing...
```

### Parsed Output
```json
{
  "full_name": "Experience",
  "current_title": "QA Engineer, QualityFirst",
  "total_years_of_experience": 10,
  "current_employment_status": "Employed",
  "open_to_work": true,
  "notice_period": 30,
  "expected_salary": 0,
  "summary": "Deterministically extracted resume profile.",
  "contact": {
    "email": "lisa.t@testing.org",
    "phone": ""
  },
  "experiences": [
    {
      "title": "QA Engineer, QualityFirst",
      "company": "Company",
      "start_date": "Mar 2016",
      "end_date": "Present",
      "duration_months": 120,
      "bullets": [
        "Wrote automation scripts."
      ]
    }
  ],
  "education": [
    {
      "degree": "Diploma",
      "institution": "University"
    }
  ],
  "skills": [
    {
      "name": "Python",
      "type": "hard"
    }
  ],
  "certifications": [],
  "projects": [],
  "career_gaps": [],
  "trajectory_events": []
}
```

**Skills:** ['Python']
**Experiences:** 1 entries, 10 YOE
**Education:** ['Diploma']
**Certifications:** []

