# Ground Truth Validation

## Candidate 41
### A. Raw Extracted Text
```text
Ian Johnson 41
user41@example.com
Summary:
Experienced Frontend Developer with 10 years of experience.
Experience:
Frontend Developer
Company 41
Jan 2016 - Present
Developed multiple applications.
Junior Frontend Developer
Old Company
Feb 2014 - Dec 2015
Maintained legacy systems.
Skills:
Proficient in Kubernetes, PyTorch, SQL, TensorFlow, Node.js, Machine Learning.
Education:
BA Graphic Design
University 41...
```

### B. Ground Truth Profile
```json
{
  "title": "Frontend Developer",
  "years_of_experience": 11,
  "skills": [
    "Kubernetes",
    "PyTorch",
    "SQL",
    "TensorFlow",
    "Node.js",
    "Machine Learning"
  ],
  "education": "BA",
  "certifications": []
}
```

### C. Parsed Profile
```json
{
  "title": "Frontend Developer",
  "years_of_experience": 11,
  "skills": [
    "Machine Learning",
    "Node.js",
    "TensorFlow",
    "Kubernetes",
    "JavaScript",
    "PyTorch",
    "SQL"
  ],
  "education": [
    "BA"
  ],
  "certifications": []
}
```

### D. Exact Field Comparison
- Title Match: True
- YOE Match: True
- Skills Match: False
- Education Match: True
- Certifications Match: True

## Candidate 8
### A. Raw Extracted Text
```text
...
```

### B. Ground Truth Profile
```json
{
  "title": "Software Engineer",
  "years_of_experience": 7,
  "skills": [
    "C++",
    "Machine Learning",
    "Docker",
    "TensorFlow"
  ],
  "education": "BTech",
  "certifications": [
    "Scrum Master",
    "Azure Fundamentals"
  ]
}
```

### C. Parsed Profile
```json
{
  "title": "Software Engineer",
  "years_of_experience": 7,
  "skills": [
    "Machine Learning",
    "C++",
    "TensorFlow",
    "Docker"
  ],
  "education": [
    "BTech"
  ],
  "certifications": [
    "Azure Fundamentals",
    "Scrum Master"
  ]
}
```

### D. Exact Field Comparison
- Title Match: True
- YOE Match: True
- Skills Match: True
- Education Match: True
- Certifications Match: True

## Candidate 2
### A. Raw Extracted Text
```text
...
```

### B. Ground Truth Profile
```json
{
  "title": "Backend Engineer",
  "years_of_experience": 11,
  "skills": [
    "React",
    "TensorFlow",
    "PyTorch",
    "SQL",
    "Node.js",
    "Python"
  ],
  "education": "BA",
  "certifications": [
    "AWS Certified"
  ]
}
```

### C. Parsed Profile
```json
{
  "title": "Backend Engineer",
  "years_of_experience": 11,
  "skills": [
    "Python",
    "Node.js",
    "TensorFlow",
    "React",
    "JavaScript",
    "PyTorch",
    "SQL"
  ],
  "education": [
    "BA"
  ],
  "certifications": []
}
```

### D. Exact Field Comparison
- Title Match: True
- YOE Match: True
- Skills Match: False
- Education Match: True
- Certifications Match: False

## Candidate 18
### A. Raw Extracted Text
```text
...
```

### B. Ground Truth Profile
```json
{
  "title": "Data Scientist",
  "years_of_experience": 17,
  "skills": [
    "Java",
    "React",
    "SQL",
    "Machine Learning",
    "Docker"
  ],
  "education": "PhD",
  "certifications": [
    "Scrum Master",
    "CISSP"
  ]
}
```

### C. Parsed Profile
```json
{
  "title": "Data Scientist",
  "years_of_experience": 17,
  "skills": [
    "SQL",
    "Docker",
    "React",
    "Machine Learning",
    "Java"
  ],
  "education": [
    "PhD"
  ],
  "certifications": [
    "CISSP",
    "Scrum Master"
  ]
}
```

### D. Exact Field Comparison
- Title Match: True
- YOE Match: True
- Skills Match: True
- Education Match: True
- Certifications Match: True

## Candidate 16
### A. Raw Extracted Text
```text
...
```

### B. Ground Truth Profile
```json
{
  "title": "Backend Engineer",
  "years_of_experience": 13,
  "skills": [
    "Node.js",
    "C++",
    "React",
    "AWS"
  ],
  "education": "PhD",
  "certifications": [
    "Scrum Master"
  ]
}
```

### C. Parsed Profile
```json
{
  "title": "Backend Engineer",
  "years_of_experience": 13,
  "skills": [
    "Node.js",
    "React",
    "AWS",
    "JavaScript",
    "C++"
  ],
  "education": [
    "PhD"
  ],
  "certifications": [
    "Scrum Master"
  ]
}
```

### D. Exact Field Comparison
- Title Match: True
- YOE Match: True
- Skills Match: False
- Education Match: True
- Certifications Match: True

## Candidate 15
### A. Raw Extracted Text
```text
Fiona Davis 15
user15@example.com
Summary:
Experienced Frontend Developer with 13 years of experience.
Experience:
Frontend Developer
Company 15
Jan 2013 - Present
Developed multiple applications.
Junior Frontend Developer
Old Company
Feb 2011 - Dec 2012
Maintained legacy systems.
Skills:
Proficient in C++, Java, PyTorch, Machine Learning, Node.js, AWS, Docker.
Education:
PhD Machine Learning
University 15...
```

### B. Ground Truth Profile
```json
{
  "title": "Frontend Developer",
  "years_of_experience": 14,
  "skills": [
    "C++",
    "Java",
    "PyTorch",
    "Machine Learning",
    "Node.js",
    "AWS",
    "Docker"
  ],
  "education": "PhD",
  "certifications": []
}
```

### C. Parsed Profile
```json
{
  "title": "Frontend Developer",
  "years_of_experience": 14,
  "skills": [
    "Node.js",
    "Docker",
    "AWS",
    "JavaScript",
    "C++",
    "PyTorch",
    "Machine Learning",
    "Java"
  ],
  "education": [
    "PhD"
  ],
  "certifications": []
}
```

### D. Exact Field Comparison
- Title Match: True
- YOE Match: True
- Skills Match: False
- Education Match: True
- Certifications Match: True

## Candidate 9
### A. Raw Extracted Text
```text
...
```

### B. Ground Truth Profile
```json
{
  "title": "Backend Engineer",
  "years_of_experience": 16,
  "skills": [
    "TensorFlow",
    "SQL",
    "AWS",
    "JavaScript",
    "Python",
    "Node.js"
  ],
  "education": "BTech",
  "certifications": [
    "AWS Certified"
  ]
}
```

### C. Parsed Profile
```json
{
  "title": "Backend Engineer",
  "years_of_experience": 16,
  "skills": [
    "Python",
    "Node.js",
    "TensorFlow",
    "AWS",
    "JavaScript",
    "SQL"
  ],
  "education": [
    "BTech"
  ],
  "certifications": []
}
```

### D. Exact Field Comparison
- Title Match: True
- YOE Match: True
- Skills Match: True
- Education Match: True
- Certifications Match: False

## Candidate 7
### A. Raw Extracted Text
```text
...
```

### B. Ground Truth Profile
```json
{
  "title": "Data Scientist",
  "years_of_experience": 9,
  "skills": [
    "JavaScript",
    "React",
    "Node.js",
    "SQL",
    "AWS"
  ],
  "education": "PhD",
  "certifications": [
    "AWS Certified",
    "Scrum Master"
  ]
}
```

### C. Parsed Profile
```json
{
  "title": "Data Scientist",
  "years_of_experience": 9,
  "skills": [
    "Node.js",
    "React",
    "AWS",
    "JavaScript",
    "SQL"
  ],
  "education": [
    "PhD"
  ],
  "certifications": [
    "Scrum Master"
  ]
}
```

### D. Exact Field Comparison
- Title Match: True
- YOE Match: True
- Skills Match: True
- Education Match: True
- Certifications Match: False

## Candidate 35
### A. Raw Extracted Text
```text
...
```

### B. Ground Truth Profile
```json
{
  "title": "Software Engineer",
  "years_of_experience": 12,
  "skills": [
    "Docker",
    "JavaScript",
    "Kubernetes",
    "Node.js",
    "React"
  ],
  "education": "MS",
  "certifications": [
    "CISSP",
    "AWS Certified"
  ]
}
```

### C. Parsed Profile
```json
{
  "title": "Software Engineer",
  "years_of_experience": 12,
  "skills": [
    "Node.js",
    "Docker",
    "React",
    "Kubernetes",
    "JavaScript"
  ],
  "education": [
    "MS"
  ],
  "certifications": [
    "CISSP"
  ]
}
```

### D. Exact Field Comparison
- Title Match: True
- YOE Match: True
- Skills Match: True
- Education Match: True
- Certifications Match: False

## Candidate 6
### A. Raw Extracted Text
```text
...
```

### B. Ground Truth Profile
```json
{
  "title": "Frontend Developer",
  "years_of_experience": 5,
  "skills": [
    "Kubernetes",
    "JavaScript",
    "Java",
    "React",
    "AWS",
    "TensorFlow",
    "SQL"
  ],
  "education": "MS",
  "certifications": [
    "CISSP"
  ]
}
```

### C. Parsed Profile
```json
{
  "title": "Frontend Developer",
  "years_of_experience": 5,
  "skills": [
    "TensorFlow",
    "React",
    "Kubernetes",
    "JavaScript",
    "AWS",
    "SQL",
    "Java"
  ],
  "education": [
    "MS"
  ],
  "certifications": [
    "CISSP"
  ]
}
```

### D. Exact Field Comparison
- Title Match: True
- YOE Match: True
- Skills Match: True
- Education Match: True
- Certifications Match: True

