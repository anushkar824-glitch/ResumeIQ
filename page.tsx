
"use client";

import { useState } from "react";

type Candidate = {
  candidate_resume: string;
  job_title: string;
  matching_score: number;
  similarity_score: number;
  matched_skills: string[];
  missing_skills: string[];
  identified_skills: string[];
  shortlisted: boolean;
  recommendation: string;
  rank?: number;
};

export default function Home() {
  const [jobDescription, setJobDescription] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [jobTitle, setJobTitle] = useState("");
  const [requiredSkills, setRequiredSkills] = useState("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [totalResumes, setTotalResumes] = useState(0);
  const [reportAvailable, setReportAvailable] = useState(false);

  async function handleAnalyze() {
    if (
      files.length === 0 ||
      !jobDescription.trim() ||
      !jobTitle.trim()
    ) {
      setErrorMessage(
        "Please enter the job title, job description and upload at least one resume."
      );
      return;
    }

    setIsUploading(true);
    setErrorMessage("");
    setCandidates([]);
    setReportAvailable(false);

    const formData = new FormData();

    files.forEach((file) => {
      formData.append("files", file);
    });

    formData.append("job_title", jobTitle);
    formData.append("job_description", jobDescription);
    formData.append("required_skills", requiredSkills);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/match-resumes",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Resume analysis failed.");
      }

      setCandidates(data.candidates || []);
      setTotalResumes(data.analyzed_resumes || 0);
      setReportAvailable(data.report_available || false);

      if (data.errors?.length > 0) {
        setErrorMessage(
          data.errors.map((item: any) =>
            `${item.filename}: ${item.error}`
          ).join(" | ")
        );
      }
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to connect to the Python backend."
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function downloadReport() {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/download-report"
      );

      if (!response.ok) {
        throw new Error("Unable to download the report.");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = "ResumeIQ_Screening_Report.csv";
      link.click();

      window.URL.revokeObjectURL(url);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Report download failed."
      );
    }
  }

  const shortlistedCount = candidates.filter(
    (candidate) => candidate.shortlisted
  ).length;

  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">

      <header className="bg-white border-b px-8 py-5">
        <h1 className="text-2xl font-bold text-blue-700">
          ResumeIQ
        </h1>
        <p className="text-sm text-slate-500">
          Automated Resume Screening & Recruitment
        </p>
      </header>

      <div className="max-w-6xl mx-auto p-8">

        <h2 className="text-3xl font-bold">
          Recruiter Dashboard
        </h2>

        <p className="text-slate-500 mt-2">
          Screen, analyze and rank candidates smarter.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-8">

          {[
            ["Total Resumes", totalResumes],
            ["Analyzed Resumes", candidates.length],
            ["Shortlisted Candidates", shortlistedCount],
          ].map(([label, value]) => (
            <div
              key={label}
              className="bg-white p-6 rounded-xl shadow-sm"
            >
              <p className="text-slate-500 text-sm">{label}</p>
              <h3 className="text-3xl font-bold mt-3">{value}</h3>
            </div>
          ))}

        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">

          <section className="bg-white p-6 rounded-xl shadow-sm">

            <h3 className="text-xl font-semibold mb-2">
              Upload Resumes
            </h3>

            <p className="text-sm text-slate-500 mb-5">
              Upload one or multiple candidate resumes in PDF or DOCX format.
            </p>

            <label className="border-2 border-dashed border-blue-300 rounded-xl p-10 flex flex-col items-center cursor-pointer hover:bg-blue-50">

              <span className="text-4xl">📄</span>

              <span className="font-medium mt-3">
                Click to select resumes
              </span>

              <span className="text-xs text-slate-400 mt-2">
                PDF or DOCX files
              </span>

              <input
                type="file"
                accept=".pdf,.docx"
                multiple
                className="hidden"
                onChange={(e) => {
                  const selectedFiles = Array.from(
                    e.target.files || []
                  );

                  setFiles(selectedFiles);
                  setCandidates([]);
                  setTotalResumes(0);
                  setReportAvailable(false);
                  setErrorMessage("");
                }}
              />

            </label>

            {files.length > 0 && (
              <div className="mt-4">

                <p className="text-sm font-semibold text-green-700">
                  {files.length} resume(s) selected
                </p>

                <ul className="mt-2 space-y-1">
                  {files.map((file, index) => (
                    <li
                      key={`${file.name}-${index}`}
                      className="text-sm text-slate-600"
                    >
                      📄 {file.name}
                    </li>
                  ))}
                </ul>

              </div>
            )}

          </section>

          <section className="bg-white p-6 rounded-xl shadow-sm">

            <h3 className="text-xl font-semibold mb-2">
              Job Requirements
            </h3>

            <p className="text-sm text-slate-500 mb-5">
              Enter the marketing position requirements.
            </p>

            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="Job Title (e.g. Marketing Executive)"
              className="w-full border rounded-lg p-3 mb-3"
            />

            <textarea
              value={requiredSkills}
              onChange={(e) => setRequiredSkills(e.target.value)}
              placeholder="Required skills (e.g. Communication, Sales, Excel)"
              className="w-full h-24 border rounded-lg p-3 mb-3 resize-none"
            />

            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Enter job description, qualifications and experience..."
              className="w-full h-32 border rounded-lg p-3 resize-none"
            />

            <button
              disabled={
                files.length === 0 ||
                !jobTitle.trim() ||
                !jobDescription.trim() ||
                isUploading
              }
              onClick={handleAnalyze}
              className="w-full mt-4 bg-blue-700 text-white py-3 rounded-lg font-semibold hover:bg-blue-800 disabled:bg-slate-300 disabled:cursor-not-allowed"
            >
              {isUploading
                ? "Analyzing Resumes..."
                : "Analyze Resumes"}
            </button>

            {errorMessage && (
              <p className="text-red-600 text-sm mt-3">
                {errorMessage}
              </p>
            )}

          </section>

        </div>

        <section className="bg-white p-6 rounded-xl shadow-sm mt-8">

          <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">

            <div>
              <h3 className="text-xl font-semibold">
                Candidate Screening Results
              </h3>

              <p className="text-slate-500 text-sm mt-2">
                Ranked candidates with matching scores and skill analysis.
              </p>
            </div>

            {reportAvailable && (
              <button
                onClick={downloadReport}
                className="bg-green-700 text-white px-5 py-3 rounded-lg font-semibold hover:bg-green-800"
              >
                Download CSV Report
              </button>
            )}

          </div>

          {candidates.length > 0 ? (

            <div className="mt-6 space-y-6">

              {candidates.map((candidate, index) => (

                <div
                  key={`${candidate.candidate_resume}-${index}`}
                  className="border rounded-xl p-5"
                >

                  <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-3">

                    <div>
                      <p className="text-sm text-blue-700 font-semibold">
                        Rank #{candidate.rank || index + 1}
                      </p>

                      <h4 className="font-semibold text-lg mt-1">
                        {candidate.candidate_resume}
                      </h4>

                      <p className="text-sm text-slate-500">
                        {candidate.job_title}
                      </p>
                    </div>

                    <div className="text-left md:text-right">
                      <h3 className="text-3xl font-bold text-blue-700">
                        {candidate.matching_score}%
                      </h3>

                      <span
                        className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-semibold ${
                          candidate.shortlisted
                            ? "bg-green-100 text-green-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}
                      >
                        {candidate.recommendation}
                      </span>
                    </div>

                  </div>

                  <div className="mt-5">

                    <p className="text-sm text-slate-500">
                      Text similarity: {candidate.similarity_score}%
                    </p>

                    <div className="w-full bg-slate-200 rounded-full h-3 mt-2">
                      <div
                        className="bg-blue-600 h-3 rounded-full"
                        style={{
                          width: `${candidate.matching_score}%`
                        }}
                      />
                    </div>

                  </div>

                  <div className="mt-5">

                    <h5 className="font-semibold text-green-700 mb-2">
                      Matched Skills
                    </h5>

                    {candidate.matched_skills.length > 0 ? (

                      <div className="flex flex-wrap gap-2">
                        {candidate.matched_skills.map((skill) => (
                          <span
                            key={skill}
                            className="bg-green-100 text-green-800 px-3 py-2 rounded-lg text-sm"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>

                    ) : (
                      <p className="text-sm text-slate-500">
                        No matching skills found.
                      </p>
                    )}

                  </div>

                  <div className="mt-4">

                    <h5 className="font-semibold text-red-700 mb-2">
                      Missing Skills
                    </h5>

                    {candidate.missing_skills.length > 0 ? (

                      <div className="flex flex-wrap gap-2">
                        {candidate.missing_skills.map((skill) => (
                          <span
                            key={skill}
                            className="bg-red-100 text-red-800 px-3 py-2 rounded-lg text-sm"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>

                    ) : (
                      <p className="text-sm text-slate-500">
                        No missing required skills.
                      </p>
                    )}

                  </div>

                  <div className="mt-4">

                    <h5 className="font-semibold text-slate-700 mb-2">
                      Skills Identified in Resume
                    </h5>

                    <p className="text-sm text-slate-600">
                      {candidate.identified_skills.length > 0
                        ? candidate.identified_skills.join(", ")
                        : "No marketing skills identified."}
                    </p>

                  </div>

                </div>

              ))}

            </div>

          ) : (

            <div className="text-center py-12 text-slate-400">
              <span className="text-4xl">📊</span>
              <p className="mt-3">
                No candidates analyzed yet.
              </p>
            </div>

          )}

        </section>

      </div>

    </main>
  );
}
