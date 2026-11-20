
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from uuid import uuid4
from typing import List
from io import BytesIO
from datetime import datetime
import csv
import re

import pdfplumber
from docx import Document
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


app = FastAPI(
    title="ResumeIQ - Automated Resume Screening",
    description="Marketing Resume Screening and Recruitment System",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_FOLDER = Path(__file__).resolve().parent.parent
DATA_FOLDER = BASE_FOLDER / "data"
OUTPUT_FOLDER = BASE_FOLDER / "outputs"

DATA_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

REPORT_PATH = OUTPUT_FOLDER / "resume_screening_report.csv"

# Marketing-focused skill library and common variations.
SKILL_ALIASES = {
    "Digital Marketing": ["digital marketing", "online marketing"],
    "SEO": ["seo", "search engine optimization", "search engine optimisation"],
    "SEM": ["sem", "search engine marketing"],
    "Social Media": ["social media", "social media management"],
    "Content Creation": ["content creation", "content writing", "content development"],
    "Communication": ["communication", "verbal communication", "written communication"],
    "Sales": ["sales", "selling", "sales management"],
    "Market Research": ["market research", "marketing research"],
    "Email Marketing": ["email marketing", "e-mail marketing"],
    "Google Ads": ["google ads", "google adwords"],
    "Facebook Ads": ["facebook ads", "meta ads"],
    "Instagram Marketing": ["instagram marketing", "instagram advertising"],
    "Brand Management": ["brand management", "brand building"],
    "Campaign Management": ["campaign management", "marketing campaigns"],
    "Analytics": ["analytics", "marketing analytics", "web analytics"],
    "MS Excel": ["excel", "ms excel", "microsoft excel"],
    "Power BI": ["power bi", "powerbi"],
    "Market Planning": ["marketing strategy", "marketing planning"],
    "Customer Relationship Management": ["crm", "customer relationship management"],
    "Lead Generation": ["lead generation", "lead management"],
    "Graphic Design": ["graphic design", "canva", "adobe photoshop"],
    "Video Editing": ["video editing", "video production"],
    "Public Relations": ["public relations", "pr"],
    "Product Marketing": ["product marketing", "product promotion"],
    "Event Marketing": ["event marketing", "event promotion"],
    "Influencer Marketing": ["influencer marketing", "influencer campaigns"],
    "Copywriting": ["copywriting", "advertising copy"],
    "Market Segmentation": ["market segmentation", "customer segmentation"],
    "Customer Engagement": ["customer engagement", "client engagement"],
    "Microsoft PowerPoint": ["powerpoint", "ms powerpoint"],
}

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contains_phrase(text, phrase):
    pattern = r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None


def extract_resume_text(filename, content):
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        with pdfplumber.open(BytesIO(content)) as pdf:
            text = "\n".join(
                page.extract_text() or ""
                for page in pdf.pages
            )

    elif extension == ".docx":
        document = Document(BytesIO(content))
        paragraphs = [
            paragraph.text for paragraph in document.paragraphs
        ]

        table_text = []
        for table in document.tables:
            for row in table.rows:
                table_text.append(
                    " ".join(cell.text for cell in row.cells)
                )

        text = "\n".join(paragraphs + table_text)

    else:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported."
        )

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text found in resume."
        )

    return text


def extract_skills(text):
    normalized = normalize_text(text)
    found = []

    for skill, aliases in SKILL_ALIASES.items():
        if any(contains_phrase(normalized, alias) for alias in aliases):
            found.append(skill)

    return found


def calculate_similarity(resume_text, job_text):
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        vectors = vectorizer.fit_transform(
            [resume_text, job_text]
        )

        score = cosine_similarity(
            vectors[0:1],
            vectors[1:2]
        )[0][0]

        return float(score * 100)

    except ValueError:
        return 0.0


def analyze_candidate(filename, content, job_title,
                      job_description, required_skills):

    resume_text = extract_resume_text(filename, content)
    resume_normalized = normalize_text(resume_text)

    resume_skills = extract_skills(resume_text)

    matched_skills = []
    missing_skills = []

    for skill in required_skills:
        aliases = SKILL_ALIASES.get(
            skill,
            [skill.lower()]
        )

        if any(
            contains_phrase(resume_normalized, alias)
            for alias in aliases
        ):
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    job_text = (
        job_title + " " +
        job_description + " " +
        " ".join(required_skills)
    )

    similarity_score = calculate_similarity(
        resume_text,
        job_text
    )

    if required_skills:
        skill_score = (
            len(matched_skills) / len(required_skills)
        ) * 100

        final_score = (
            similarity_score * 0.70 +
            skill_score * 0.30
        )
    else:
        final_score = similarity_score

    final_score = round(
        max(0, min(100, final_score)),
        2
    )

    shortlisted = (
        final_score >= 70 and
        len(missing_skills) == 0
    )

    saved_filename = f"{uuid4().hex}_{Path(filename).name}"
    (DATA_FOLDER / saved_filename).write_bytes(content)

    return {
        "candidate_resume": Path(filename).name,
        "job_title": job_title,
        "matching_score": final_score,
        "similarity_score": round(similarity_score, 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "identified_skills": resume_skills,
        "shortlisted": shortlisted,
        "recommendation": (
            "Shortlisted"
            if shortlisted
            else "Further Evaluation"
        )
    }


def save_csv_report(results):
    with open(
        REPORT_PATH,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as csvfile:

        fieldnames = [
            "Rank",
            "Candidate Resume",
            "Job Title",
            "Matching Score",
            "Matched Skills",
            "Missing Skills",
            "Recommendation"
        ]

        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for rank, result in enumerate(results, start=1):
            writer.writerow({
                "Rank": rank,
                "Candidate Resume": result["candidate_resume"],
                "Job Title": result["job_title"],
                "Matching Score": result["matching_score"],
                "Matched Skills": ", ".join(result["matched_skills"]),
                "Missing Skills": ", ".join(result["missing_skills"]),
                "Recommendation": result["recommendation"]
            })


@app.get("/")
def home():
    return {
        "message": "Welcome to ResumeIQ!",
        "status": "Running"
    }


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    filename = Path(file.filename or "resume").name

    if Path(filename).suffix.lower() not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed."
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    extract_resume_text(filename, content)

    saved_filename = f"{uuid4().hex}_{filename}"
    (DATA_FOLDER / saved_filename).write_bytes(content)

    return {
        "message": "Resume uploaded successfully!",
        "filename": filename
    }


@app.post("/extract-pdf-text")
async def extract_pdf_text(file: UploadFile = File(...)):
    filename = file.filename or ""

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file."
        )

    content = await file.read()

    try:
        return {
            "message": "PDF text extracted successfully!",
            "extracted_text": extract_resume_text(filename, content)
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read PDF file."
        )


@app.post("/extract-docx-text")
async def extract_docx_text(file: UploadFile = File(...)):
    filename = file.filename or ""

    if not filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a DOCX file."
        )

    content = await file.read()

    try:
        return {
            "message": "DOCX text extracted successfully!",
            "extracted_text": extract_resume_text(filename, content)
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read DOCX file."
        )


class JobDescription(BaseModel):
    job_title: str
    description: str
    required_skills: list[str] = Field(default_factory=list)


@app.post("/add-job")
async def add_job(job: JobDescription):
    return {
        "message": "Job description added successfully!",
        "job_title": job.job_title,
        "description": job.description,
        "required_skills": job.required_skills
    }


@app.post("/extract-skills")
async def extract_skills_endpoint(file: UploadFile = File(...)):
    filename = file.filename or ""
    content = await file.read()

    try:
        text = extract_resume_text(filename, content)
        skills = extract_skills(text)

        return {
            "message": "Skills extracted successfully!",
            "identified_skills": skills,
            "total_skills": len(skills)
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to process resume."
        )


@app.post("/match-resume")
async def match_resume(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    required_skills: str = Form("")
):
    filename = Path(file.filename or "resume").name
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded resume is empty."
        )

    skills = list(dict.fromkeys(
        skill.strip()
        for skill in required_skills.split(",")
        if skill.strip()
    ))

    try:
        result = analyze_candidate(
            filename,
            content,
            job_title,
            job_description,
            skills
        )

        return {
            "message": "Resume matching completed!",
            **result
        }

    except HTTPException:
        raise
    except Exception as error:
        print("Resume analysis error:", str(error))
        raise HTTPException(
            status_code=400,
            detail="Unable to process this resume."
        )


@app.post("/match-resumes")
async def match_multiple_resumes(
    files: List[UploadFile] = File(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    required_skills: str = Form("")
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Please upload at least one resume."
        )

    skills = list(dict.fromkeys(
        skill.strip()
        for skill in required_skills.split(",")
        if skill.strip()
    ))

    results = []
    errors = []

    for file in files:
        filename = Path(file.filename or "resume").name
        content = await file.read()

        if not content:
            errors.append({
                "filename": filename,
                "error": "Empty file"
            })
            continue

        try:
            result = analyze_candidate(
                filename,
                content,
                job_title,
                job_description,
                skills
            )
            results.append(result)

        except Exception as error:
            errors.append({
                "filename": filename,
                "error": str(error)
            })

    if not results:
        raise HTTPException(
            status_code=400,
            detail="No resumes could be analyzed. Check the uploaded files."
        )

    results.sort(
        key=lambda item: item["matching_score"],
        reverse=True
    )

    for rank, result in enumerate(results, start=1):
        result["rank"] = rank

    save_csv_report(results)

    return {
        "message": "Multiple resume screening completed!",
        "job_title": job_title,
        "total_resumes": len(files),
        "analyzed_resumes": len(results),
        "shortlisted_candidates": sum(
            1 for result in results if result["shortlisted"]
        ),
        "candidates": results,
        "errors": errors,
        "report_available": True
    }


@app.get("/download-report")
def download_report():
    if not REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No screening report is available. Analyze resumes first."
        )

    return FileResponse(
        path=REPORT_PATH,
        filename="ResumeIQ_Screening_Report.csv",
        media_type="text/csv"
    )
