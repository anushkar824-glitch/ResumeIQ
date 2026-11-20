
# ResumeIQ
### Automated Resume Screening & Recruitment System

ResumeIQ is a web-based resume screening application designed to help recruiters analyze, compare, and rank candidates for marketing positions.

## Project Objective

To simplify the recruitment process by extracting relevant information from resumes and comparing candidates' skills with job requirements.

## Key Features

- Upload multiple resumes in PDF and DOCX formats.
- Extract text from uploaded resumes.
- Identify relevant marketing skills.
- Analyze resumes against job descriptions.
- Calculate candidate matching scores.
- Display matched and missing skills.
- Rank candidates based on matching scores.
- Recommend candidates for shortlisting.
- Generate and download screening reports in CSV format.

## Technologies Used

**Backend**
- Python
- FastAPI
- Scikit-learn
- PDFPlumber
- Python-docx

**Frontend**
- Next.js
- React
- TypeScript

## Project Structure

```text
Automated-Resume-Screening-Tool/
│
├── backend/
│   └── main.py
│
├── frontend/
│   ├── app/
│   │   └── page.tsx
│   └── package.json
│
├── data/
├── outputs/
└── README.md
```

## How It Works

1. The recruiter uploads one or multiple resumes.
2. The system extracts text from the resumes.
3. The recruiter enters the job title, description, and required skills.
4. ResumeIQ compares candidate profiles with job requirements.
5. The system calculates matching scores and identifies matched and missing skills.
6. Candidates are ranked and shortlisting recommendations are displayed.
7. The recruiter can download the screening report in CSV format.

## Matching Methodology

ResumeIQ uses Natural Language Processing techniques and TF-IDF with cosine similarity to compare resume content with job descriptions.

The matching score combines:
- 70% job description similarity.
- 30% required skill coverage.

Shortlisting recommendations are generated using the matching score and required-skill coverage.

## Applications

- Recruitment and talent acquisition.
- Initial resume screening.
- Marketing candidate evaluation.
- Candidate comparison and ranking.

## Disclaimer

ResumeIQ is an academic project and its screening scores are intended to support recruiter evaluation. They should not be used as the sole basis for hiring decisions.

---

**Developed as a Python project – ResumeIQ**
