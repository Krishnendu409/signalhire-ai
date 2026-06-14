import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def generate_pdf(filename, text):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica", 10)
    y = 750
    for line in text.split('\n'):
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = 750
        c.drawString(50, y, line)
        y -= 15
    c.save()

resumes = [
    """JOHN DOE - Senior Developer
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
React, Node.js, TypeScript, PostgreSQL, AWS
""",
    """JANE SMITH | Data Scientist
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
Python, TensorFlow, PyTorch, SQL
""",
    """MICHAEL JOHNSON
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
Kubernetes, AWS, Docker, Bash
""",
    """SARAH CONNOR - Product Manager
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
Agile, Scrum Master, JIRA, Product Management
""",
    """ALEX TURNER - Frontend Engineer
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
JavaScript, HTML, CSS, React, UI/UX
""",
    """DAVID MILLER - Backend Developer
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
Java, Spring Boot, PostgreSQL, Microservices
""",
    """EMILY DAVIS
emilyd@design.com

Experience
UI/UX Designer
DesignStudio (Jan 2019 - Present)
Created mockups.

Education
BA Graphic Design

Skills
UI/UX, Figma, Adobe XD
""",
    """ROBERT WILSON - Cloud Engineer
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
AWS, Kubernetes, Terraform, Python
""",
    """LISA TAYLOR - QA Engineer
lisa.t@testing.org

Experience
QA Engineer, QualityFirst
Mar 2016 - Present
Wrote automation scripts.

Education
Diploma in IT

Skills
Selenium, Python, Cypress, Testing
""",
    """JAMES ANDERSON - Full Stack Developer
james.a@dev.net

Experience
Full Stack Developer
TechInnovators
Jan 2015 - Present
Built end-to-end features.

Education
MSc Computer Science

Skills
React, Node.js, MongoDB, JavaScript, TypeScript
"""
]

import os
os.makedirs("real_resumes", exist_ok=True)
for i, text in enumerate(resumes):
    generate_pdf(f"real_resumes/real_resume_{i+1}.pdf", text)
