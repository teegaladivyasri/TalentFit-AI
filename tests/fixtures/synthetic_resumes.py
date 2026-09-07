"""Synthetic Resumes and Job Descriptions for System Validation.

These synthetic fixtures contain realistic, safe-to-commit profiles covering
strong matches, moderate matches, weak matches, extra skills, alias-heavy text,
false-positive stress tests, sparse text, unusual headers, and complex technical terms.
"""

# ---------------------------------------------------------------------------
# Synthetic Resumes (A - J)
# ---------------------------------------------------------------------------

RESUME_A_STRONG_MATCH = """
Alex Morgan
alex.morgan@example.com | (555) 234-5678 | San Francisco, CA
linkedin.com/in/alexmorgan-dev | github.com/alexmorgan

Summary
Results-driven Senior Full Stack Engineer with 6+ years of experience building high-throughput web applications and REST APIs using Python, FastAPI, and PostgreSQL. Experienced with Docker containerization and AWS cloud deployments.

Technical Skills
- Languages & Frameworks: Python, FastAPI, React, JavaScript, SQL
- Databases & Storage: PostgreSQL, Redis
- Cloud & DevOps: AWS, Docker, Git, CI/CD

Work Experience
Senior Backend Engineer | CloudScale Tech | 2021 - Present
- Architected high-performance microservices using Python and FastAPI handling 15k requests/sec.
- Designed relational schemas and optimized queries in PostgreSQL, reducing query latency by 40%.
- Containerized backend services using Docker and orchestrated automated deployments with AWS ECS and CI/CD pipelines.
- Integrated REST APIs with React frontend applications.

Software Engineer | NextGen Solutions | 2018 - 2021
- Developed scalable RESTful APIs with Python and Flask.
- Collaborated with frontend engineers to build interactive dashboards using React and JavaScript.
- Managed source code and version control workflows using Git and GitHub.

Education
Bachelor of Science in Computer Science | University of California, Berkeley | 2018

Projects
Real-Time Analytics Engine
- Built a streaming data processing system using Python, FastAPI, PostgreSQL, and Docker.
"""

RESUME_B_MODERATE_MATCH = """
Jordan Lee
jordan.lee@example.com | (555) 345-6789 | Chicago, IL
github.com/jordanlee

Summary
Software Developer with 3 years of experience in Python scripting, MySQL database management, and basic frontend development.

Technical Skills
- Languages: Python, SQL, HTML, CSS, JavaScript
- Databases: MySQL, SQLite
- Tools: Git, GitHub

Work Experience
Junior Software Engineer | DataCorp LLC | 2021 - Present
- Developed automation scripts in Python to streamline ETL workflows and data ingestion.
- Wrote SQL queries and maintained relational databases in MySQL and SQLite.
- Created internal portal pages using HTML, CSS, and vanilla JavaScript.
- Collaborated in an Agile Scrum team using Git for version control.

Education
Bachelor of Science in Information Technology | University of Illinois | 2021
"""

RESUME_C_WEAK_MATCH = """
Samantha Taylor
samantha.taylor@example.com | (555) 456-7890 | New York, NY
linkedin.com/in/samanthataylor-marketing

Summary
Creative Digital Marketing Specialist with 5+ years of experience leading brand campaigns, SEO optimization, and social media marketing.

Core Competencies
- Digital Marketing, Search Engine Optimization (SEO), Content Strategy
- Social Media Management, Google Analytics, Copywriting
- Email Marketing Campaigns, Brand Strategy, Market Research

Professional Experience
Senior Marketing Manager | GrowthBrand Media | 2020 - Present
- Spearheaded multichannel marketing campaigns increasing organic user acquisition by 65%.
- Managed content strategy and SEO keyword research driving 500k monthly website visitors.
- Directed social media strategy across LinkedIn, Instagram, and Twitter.

Marketing Associate | Creative Spark Agency | 2018 - 2020
- Wrote copywriting copy and executed automated email campaigns.
- Monitored engagement metrics using Google Analytics and prepared quarterly performance reports.

Education
Bachelor of Arts in Communications | New York University | 2018
"""

RESUME_D_EXTRA_SKILLS = """
David Chen
david.chen@example.com | (555) 567-8901 | Seattle, WA
github.com/davidchen-ai | linkedin.com/in/davidchen-engineer

Summary
Versatile Lead Engineer & Machine Learning Specialist with expertise in backend systems, distributed infrastructure, and deep learning pipelines.

Technical Skills
- Languages & Frameworks: Python, FastAPI, React, TypeScript, C++, GraphQL
- Data & AI / ML: PyTorch, TensorFlow, Pandas, NumPy, scikit-learn, Machine Learning, Deep Learning, NLP
- Databases: PostgreSQL, MongoDB, Redis, Cassandra
- Cloud & DevOps: AWS, Docker, Kubernetes, Terraform, CI/CD, Linux, Jenkins

Work Experience
Lead Distributed Systems Engineer | AI Enterprise Labs | 2020 - Present
- Architected asynchronous REST APIs and microservices using Python, FastAPI, and PostgreSQL.
- Implemented deep learning and NLP models using PyTorch and scikit-learn for automated text analysis.
- Deployed microservices on Kubernetes clusters configured with Terraform and AWS.
- Built real-time cache layers with Redis and message brokers with Kafka.

Senior Software Engineer | DataStream Inc | 2017 - 2020
- Built full-stack applications with React, TypeScript, and Python.
- Set up Jenkins CI/CD automation pipelines on Linux infrastructure.

Education
Master of Science in Computer Science | University of Washington | 2017
"""

RESUME_E_ALIAS_HEAVY = """
Marcus Vance
marcus.vance@example.com | (555) 678-9012 | Austin, TX

Summary
Full stack developer utilizing modern open source tools and cloud environments.

Skills
python3, postgres, golang, reactjs, nodejs, gcp, fast api, k8s, cicd

Experience
Full Stack Engineer | CloudTech Ventures | 2021 - Present
- Wrote backend services in python3 and fast api connected to postgres database.
- Built microservices using golang and deployed to gcp using k8s and cicd workflows.
- Developed dynamic single-page web applications with reactjs and nodejs.

Education
BS in Computer Science | University of Texas at Austin | 2021
"""

RESUME_F_FALSE_POSITIVE_STRESS = """
Elena Rostova
elena.rostova@example.com | (555) 789-0123 | Boston, MA
linkedin.com/in/elenarostova

Professional Summary
Experienced Technical Program Manager with a background in engineering leadership and cross-functional team coordination.

Core Competencies
- Team Leadership, Agile Coaching, Stakeholder Management
- Process Optimization, Continuous Improvement, Strategic Planning

Professional Experience
Technical Program Manager | Global Software Inc | 2020 - Present
- We communicate clearly with developers across distributed international teams.
- Our team practices continuous improvement in our agile delivery cycles.
- Please go to the Google documentation to review our published interface guidelines.
- The candidate worked with JavaScript applications and modernized legacy tooling.
- The team uses React Native for all iOS and Android mobile development.

Education
Bachelor of Science in Engineering Management | Boston University | 2019
"""

RESUME_G_SPARSE = """
Jane Doe
jane.doe@example.com
Minimal resume. Python developer with some SQL skills.
"""

RESUME_H_STRUCTURED = """
Robert Miller
robert.miller@example.com | (555) 890-1234 | Denver, CO
linkedin.com/in/robertmiller-dev | github.com/robertmiller

Summary
Software Engineer with 4 years of experience building scalable web backends in Python and managing database systems.

Skills
- Programming Languages: Python, JavaScript, SQL
- Frameworks & Libraries: FastAPI, Django, React
- Databases: PostgreSQL, MySQL
- Tools & Platforms: Docker, Git, AWS

Experience
Software Engineer | Rocky Mountain Tech | 2020 - Present
- Developed scalable web services in Python using FastAPI and Django.
- Maintained production PostgreSQL databases and authored complex SQL migrations.
- Collaborated with frontend engineers to build components in React and JavaScript.
- Deployed containerized applications using Docker and AWS.

Education
Bachelor of Science in Software Engineering | Colorado State University | 2020

Projects
Automated Document Classifier
- Built a document categorization tool using Python, FastAPI, and PostgreSQL with Docker deployment.
"""

RESUME_I_UNUSUAL_SECTIONS = """
Michael Chang
michael.chang@example.com | (555) 901-2345 | San Jose, CA
github.com/mchang-tech

Professional Background
Senior Backend Developer with 7 years of engineering experience in enterprise application design.

Technical Expertise
- Core Tech: Python, Java, FastAPI, PostgreSQL, Docker, Git, REST API

Academic History
Master of Science in Software Engineering | San Jose State University | 2017
Bachelor of Science in Computer Engineering | UC Davis | 2015

Selected Work
Distributed Inventory Manager
- Engineered resilient REST APIs in Python using FastAPI and PostgreSQL.
- Implemented Docker containerization for seamless cloud portability.
"""

RESUME_J_MIXED_TECH_TERMS = """
Kiran Patel
kiran.patel@example.com | (555) 012-3456 | Atlanta, GA
github.com/kiranpatel-dev | linkedin.com/in/kiranpatel

Summary
Polyglot Systems Engineer with 8 years of experience in high-performance computing, web technologies, and machine learning.

Technical Skills
- Languages: C++, C#, Python, JavaScript, TypeScript
- Frameworks & Platforms: .NET, Node.js, React Native, REST API
- DevOps & AI / ML: CI/CD, scikit-learn, Docker, Linux

Work Experience
Senior Systems Engineer | Enterprise Tech Corp | 2019 - Present
- Developed low-latency simulation engines in C++ and backend enterprise services in C# with .NET.
- Implemented machine learning classification models using scikit-learn and Python.
- Built cross-platform mobile interfaces using React Native and JavaScript.
- Maintained continuous integration and delivery using CI/CD pipelines on Linux servers.
- Designed high-throughput REST API endpoints in Node.js.

Education
Bachelor of Science in Computer Science | Georgia Institute of Technology | 2016
"""

# ---------------------------------------------------------------------------
# Synthetic Job Descriptions (1 - 3)
# ---------------------------------------------------------------------------

JD_1_PYTHON_BACKEND = """
Senior Python / Backend Engineer
Location: Remote / San Francisco, CA

About the Role
We are looking for an experienced Senior Python Backend Engineer to build high-scale microservices and data pipelines for our core platform.

Requirements:
- Strong proficiency in Python with 4+ years of professional backend experience
- Hands-on experience developing REST APIs using FastAPI or Flask
- Solid understanding of relational databases, especially PostgreSQL
- Experience designing RESTful APIs and microservice architectures
- Proficiency with Git version control

Preferred Qualifications:
- Experience with Docker containerization and Kubernetes
- Familiarity with AWS cloud services (EC2, S3)
- Experience setting up CI/CD automation pipelines
"""

JD_2_FRONTEND_JAVASCRIPT = """
Frontend Web Developer
Location: New York, NY

Role Summary
Seeking a creative Frontend Web Developer to build responsive user interfaces and modern web applications.

Required Qualifications:
- Proficient in JavaScript, HTML, and CSS
- 3+ years of hands-on experience with React
- Experience integrating with backend REST APIs
- Familiarity with Node.js and modern package managers

Nice to Have:
- Experience with TypeScript
- Experience with Next.js or Tailwind CSS
- Familiarity with MongoDB
"""

JD_3_GENERIC_UNSTRUCTURED = """
Software Engineer Needed
We need a smart developer to join our growing product team. You will work across our stack writing code, fixing bugs, and deploying features.
We use Python, PostgreSQL, and Docker daily. Some experience with React or frontend JavaScript is helpful.
Must be a team player with good problem solving skills and familiarity with Git.
"""
