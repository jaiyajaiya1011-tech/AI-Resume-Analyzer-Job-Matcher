import streamlit as st
import re
from PyPDF2 import PdfReader

st.set_page_config(
    page_title="AI Resume Analyzer & Job Matcher",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #E8D3B9;
}

h1, h2, h3, h4, h5, h6, p, label {
    color: black !important;
}

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    margin-bottom: 30px;
}

.card {
    background-color: #F7EBDD;
    padding: 22px;
    border-radius: 15px;
    margin: 18px 0;
    border: 1px solid #C8A987;
}

.score {
    font-size: 50px;
    font-weight: bold;
    text-align: center;
}

.job-card {
    background-color: #F7EBDD;
    padding: 18px;
    border-radius: 12px;
    margin: 12px 0;
    border-left: 5px solid #8B5E3C;
}

.apply-button {
    background-color: #8B5E3C;
    color: white !important;
    padding: 8px 18px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    display: inline-block;
}
</style>
""", unsafe_allow_html=True)


def normalize_text(text):
    text = text.replace("\xa0", " ")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def unique(items):
    result = []
    seen = set()

    for item in items:
        item = item.strip()
        key = item.lower()

        if item and key not in seen:
            seen.add(key)
            result.append(item)

    return result


def extract_pdf_text(file):
    reader = PdfReader(file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return normalize_text(text)


def extract_email(text):
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

    matches = re.findall(pattern, text)

    return unique(matches)


def extract_phone(text):
    patterns = [
        r"(?:\+91[\s.-]?)?[6-9]\d{9}",
        r"\+\d{1,3}[\s.-]?\d{6,14}"
    ]

    phones = []

    for pattern in patterns:
        matches = re.findall(pattern, text)

        for number in matches:
            digits = re.sub(r"\D", "", number)

            if 10 <= len(digits) <= 15:
                phones.append(number.strip())

    return unique(phones)


def extract_linkedin(text):
    pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/[A-Za-z0-9_./%-]+"

    matches = re.findall(
        pattern,
        text,
        re.IGNORECASE
    )

    results = []

    for url in matches:
        url = url.rstrip(".,;:)]}")

        if not url.startswith("http"):
            url = "https://" + url

        results.append(url)

    return unique(results)


def extract_github(text):
    pattern = r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?"

    matches = re.findall(
        pattern,
        text,
        re.IGNORECASE
    )

    results = []

    for url in matches:
        url = url.rstrip(".,;:)]}")

        if not url.startswith("http"):
            url = "https://" + url

        results.append(url)

    return unique(results)


def extract_name(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    ignore = [
        "resume",
        "curriculum vitae",
        "email",
        "phone",
        "mobile",
        "linkedin",
        "github",
        "portfolio",
        "education",
        "skills",
        "experience",
        "projects"
    ]

    candidates = []

    for index, line in enumerate(lines[:15]):

        lower = line.lower()

        if any(word in lower for word in ignore):
            continue

        if "@" in line or "http" in lower:
            continue

        if re.search(r"\d{7,}", line):
            continue

        if not re.fullmatch(
            r"[A-Za-z][A-Za-z .'-]{1,60}",
            line
        ):
            continue

        words = line.split()

        if 2 <= len(words) <= 5:

            score = 15 - index

            if all(
                word[0].isupper()
                for word in words
                if word
            ):
                score += 5

            candidates.append(
                (score, line)
            )

    if candidates:
        candidates.sort(
            reverse=True
        )
        return candidates[0][1]

    return "Not detected"
SECTION_ALIASES = {
    "education": [
        "education",
        "academic background",
        "educational background",
        "academic qualifications",
        "qualifications"
    ],
    "skills": [
        "skills",
        "technical skills",
        "core skills",
        "key skills",
        "technical expertise"
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "internship",
        "internships",
        "work history"
    ],
    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "project experience"
    ],
    "certifications": [
        "certifications",
        "certificates",
        "courses",
        "certifications and courses"
    ],
    "languages": [
        "languages",
        "language proficiency"
    ]
}


def normalize_heading(line):
    line = line.lower().strip()
    line = re.sub(r"[^a-z0-9& ]", "", line)
    line = re.sub(r"\s+", " ", line)
    return line


def detect_section(line):
    normalized = normalize_heading(line)

    for section, headings in SECTION_ALIASES.items():
        for heading in headings:
            if normalized == heading:
                return section

    return None


def extract_sections(text):
    sections = {
        "education": [],
        "skills": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "languages": []
    }

    current_section = None

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        detected = detect_section(line)

        if detected:
            current_section = detected
            continue

        if current_section:
            sections[current_section].append(line)

    for key in sections:
        sections[key] = unique(sections[key])

    return sections


SKILL_ALIASES = {
    "Python": [
        "python"
    ],
    "SQL": [
        "sql",
        "mysql",
        "postgresql"
    ],
    "Excel": [
        "excel",
        "microsoft excel"
    ],
    "Power BI": [
        "power bi",
        "powerbi"
    ],
    "Tableau": [
        "tableau"
    ],
    "Pandas": [
        "pandas"
    ],
    "NumPy": [
        "numpy"
    ],
    "Matplotlib": [
        "matplotlib"
    ],
    "Seaborn": [
        "seaborn"
    ],
    "Java": [
        "java"
    ],
    "C++": [
        "c++"
    ],
    "C": [
        "c programming",
        "c language"
    ],
    "HTML": [
        "html",
        "html5"
    ],
    "CSS": [
        "css",
        "css3"
    ],
    "JavaScript": [
        "javascript",
        "js"
    ],
    "Git": [
        "git"
    ],
    "GitHub": [
        "github"
    ],
    "Streamlit": [
        "streamlit"
    ],
    "Arduino": [
        "arduino"
    ],
    "IoT": [
        "iot",
        "internet of things"
    ],
    "Embedded Systems": [
        "embedded systems",
        "embedded system"
    ],
    "UI/UX": [
        "ui/ux",
        "ui ux",
        "user interface",
        "user experience"
    ],
    "Figma": [
        "figma"
    ],
    "Canva": [
        "canva"
    ],
    "Cybersecurity": [
        "cybersecurity",
        "cyber security"
    ],
    "Machine Learning": [
        "machine learning",
        "ml"
    ],
    "Artificial Intelligence": [
        "artificial intelligence",
        "ai"
    ],
    "Data Analytics": [
        "data analytics",
        "data analysis"
    ],
    "Data Science": [
        "data science"
    ],
    "Data Visualization": [
        "data visualization",
        "data visualisation"
    ]
}


def extract_skills(text, skill_section):
    combined_text = text + "\n" + " ".join(skill_section)
    clean = clean_text(combined_text)

    found = []

    for skill, aliases in SKILL_ALIASES.items():

        for alias in aliases:

            alias_clean = alias.lower()

            if alias_clean in clean:
                found.append(skill)
                break

    return unique(found)


def extract_education(section_lines):
    if not section_lines:
        return ["Not detected"]

    education = []

    for line in section_lines:

        if len(line.strip()) >= 3:
            education.append(line.strip())

    return unique(education)


def extract_experience(section_lines):
    if not section_lines:
        return ["Not detected"]

    experience = []

    for line in section_lines:

        if len(line.strip()) >= 3:
            experience.append(line.strip())

    return unique(experience)


def extract_projects(section_lines):
    if not section_lines:
        return ["Not detected"]

    projects = []

    for line in section_lines:

        if len(line.strip()) >= 3:
            projects.append(line.strip())

    return unique(projects)


def extract_certifications(section_lines):
    if not section_lines:
        return ["Not detected"]

    certifications = []

    for line in section_lines:

        if len(line.strip()) >= 3:
            certifications.append(line.strip())

    return unique(certifications)


def extract_languages(section_lines, text):
    languages = []

    language_names = [
        "English",
        "Tamil",
        "Hindi",
        "Telugu",
        "Malayalam",
        "Kannada",
        "French",
        "German",
        "Spanish"
    ]

    combined = clean_text(
        " ".join(section_lines) + " " + text
    )

    for language in language_names:

        if language.lower() in combined:
            languages.append(language)

    return unique(languages)


def extract_portfolio(text):
    patterns = [
        r"(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.(?:vercel\.app|netlify\.app|github\.io|pages\.dev)[A-Za-z0-9_./%-]*",
        r"(?:https?://)?(?:www\.)?portfolio\.[a-zA-Z0-9.-]+[A-Za-z0-9_./%-]*"
    ]

    results = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for url in matches:

            url = url.rstrip(".,;:)]}")

            if not url.startswith("http"):
                url = "https://" + url

            results.append(url)

    return unique(results)


def extract_resume_details(text):
    sections = extract_sections(text)

    details = {}

    details["name"] = extract_name(text)

    emails = extract_email(text)
    details["email"] = emails if emails else ["Not detected"]

    phones = extract_phone(text)
    details["phone"] = phones if phones else ["Not detected"]

    linkedin = extract_linkedin(text)
    details["linkedin"] = linkedin if linkedin else ["Not detected"]

    github = extract_github(text)
    details["github"] = github if github else ["Not detected"]

    portfolio = extract_portfolio(text)
    details["portfolio"] = portfolio if portfolio else ["Not detected"]

    details["skills"] = extract_skills(
        text,
        sections["skills"]
    )

    if not details["skills"]:
        details["skills"] = ["Not detected"]

    details["education"] = extract_education(
        sections["education"]
    )

    details["experience"] = extract_experience(
        sections["experience"]
    )

    details["projects"] = extract_projects(
        sections["projects"]
    )

    details["certifications"] = extract_certifications(
        sections["certifications"]
    )

    details["languages"] = extract_languages(
        sections["languages"],
        text
    )

    if not details["languages"]:
        details["languages"] = ["Not detected"]

    return details


ROLE_SKILLS = {
    "Data Analyst": [
        "Python",
        "SQL",
        "Excel",
        "Power BI",
        "Tableau",
        "Pandas",
        "Data Analytics",
        "Data Visualization"
    ],

    "Python Developer": [
        "Python",
        "SQL",
        "Git",
        "GitHub",
        "Streamlit"
    ],

    "Business Analyst": [
        "Excel",
        "SQL",
        "Power BI",
        "Data Analytics",
        "Data Visualization"
    ],

    "Data Scientist": [
        "Python",
        "SQL",
        "Pandas",
        "NumPy",
        "Machine Learning",
        "Data Science",
        "Data Visualization"
    ],

    "UI/UX Designer": [
        "UI/UX",
        "Figma",
        "Canva"
    ],

    "IoT / Embedded Systems": [
        "C",
        "C++",
        "Arduino",
        "IoT",
        "Embedded Systems"
    ]
}


def calculate_role_matches(skills):
    user_skills = set(
        skill.lower()
        for skill in skills
    )

    results = []

    for role, required_skills in ROLE_SKILLS.items():

        matched = []

        for skill in required_skills:

            if skill.lower() in user_skills:
                matched.append(skill)

        if required_skills:
            percentage = round(
                len(matched) /
                len(required_skills) * 100
            )
        else:
            percentage = 0

        results.append({
            "role": role,
            "score": percentage,
            "matched": matched,
            "required": required_skills
        })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results


def calculate_ats_score(text, details):
    score = 0
    clean = clean_text(text)

    if details["name"] != "Not detected":
        score += 10

    if details["email"] != ["Not detected"]:
        score += 10

    if details["phone"] != ["Not detected"]:
        score += 10

    if details["linkedin"] != ["Not detected"]:
        score += 5

    if details["github"] != ["Not detected"]:
        score += 5

    if details["skills"] != ["Not detected"]:
        score += 15

    if details["education"] != ["Not detected"]:
        score += 10

    if details["experience"] != ["Not detected"]:
        score += 10

    if details["projects"] != ["Not detected"]:
        score += 10

    if details["certifications"] != ["Not detected"]:
        score += 5

    important_keywords = [
        "summary",
        "objective",
        "skills",
        "education",
        "experience",
        "projects",
        "certifications"
    ]

    keyword_count = sum(
        1
        for keyword in important_keywords
        if keyword in clean
    )

    score += min(
        keyword_count * 1,
        10
    )

    return min(score, 100)


def generate_suggestions(details, ats_score):
    suggestions = []

    if ats_score < 60:
        suggestions.append(
            "Improve the resume structure and include relevant job keywords."
        )

    if details["email"] == ["Not detected"]:
        suggestions.append(
            "Add a professional email address."
        )

    if details["phone"] == ["Not detected"]:
        suggestions.append(
            "Add a valid contact number."
        )

    if details["linkedin"] == ["Not detected"]:
        suggestions.append(
            "Add your LinkedIn profile URL."
        )

    if details["github"] == ["Not detected"]:
        suggestions.append(
            "Add your GitHub profile if you have coding projects."
        )

    if details["skills"] == ["Not detected"]:
        suggestions.append(
            "Add a dedicated Technical Skills section."
        )

    if details["projects"] == ["Not detected"]:
        suggestions.append(
            "Add 2–4 relevant projects with technologies and outcomes."
        )

    if details["certifications"] == ["Not detected"]:
        suggestions.append(
            "Add relevant certifications and completed courses."
        )

    if details["experience"] == ["Not detected"]:
        suggestions.append(
            "Add internship or practical experience details if available."
        )

    if not suggestions:
        suggestions.append(
            "Your resume contains the main sections expected in an ATS-friendly resume. Keep improving keywords and measurable achievements."
        )

    return unique(suggestions)
st.markdown(
    '<div class="main-title">🤖 AI Resume Analyzer & Job Matcher</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Upload your resume and get an instant resume analysis, ATS estimate and job-role matching.</div>',
    unsafe_allow_html=True
)


uploaded_file = st.file_uploader(
    "📄 Upload your Resume PDF",
    type=["pdf"]
)


if uploaded_file is not None:

    st.success(
        f"Resume uploaded successfully: {uploaded_file.name}"
    )

    try:

        resume_text = extract_pdf_text(
            uploaded_file
        )

        if not resume_text:

            st.error(
                "No readable text was found in this PDF. "
                "Please upload a text-based PDF resume."
            )

        else:

            details = extract_resume_details(
                resume_text
            )

            ats_score = calculate_ats_score(
                resume_text,
                details
            )

            role_matches = calculate_role_matches(
                details["skills"]
            )

            suggestions = generate_suggestions(
                details,
                ats_score
            )

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("👤 Personal Information")

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**Name:** {details['name']}"
                )

                st.write(
                    f"**Email:** {', '.join(details['email'])}"
                )

                st.write(
                    f"**Phone:** {', '.join(details['phone'])}"
                )

            with col2:

                st.write(
                    f"**LinkedIn:** {', '.join(details['linkedin'])}"
                )

                st.write(
                    f"**GitHub:** {', '.join(details['github'])}"
                )

                st.write(
                    f"**Portfolio:** {', '.join(details['portfolio'])}"
                )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("📊 ATS Resume Score")

            score_col1, score_col2, score_col3 = st.columns(
                [1, 2, 1]
            )

            with score_col2:

                st.markdown(
                    f'<div class="score">{ats_score}/100</div>',
                    unsafe_allow_html=True
                )

                st.progress(
                    ats_score / 100
                )

                st.caption(
                    "Estimated ATS compatibility score based on resume structure, contact information, skills, projects and common resume sections."
                )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("🛠️ Skills")

            if details["skills"] != ["Not detected"]:

                skill_text = " • ".join(
                    details["skills"]
                )

                st.write(skill_text)

            else:

                st.warning(
                    "No technical skills detected."
                )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("🎓 Education")

            for item in details["education"]:
                st.write("• " + item)

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("💼 Experience / Internships")

            for item in details["experience"]:
                st.write("• " + item)

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("🚀 Projects")

            for item in details["projects"]:
                st.write("• " + item)

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("🏆 Certifications / Courses")

            for item in details["certifications"]:
                st.write("• " + item)

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("🌐 Languages")

            st.write(
                " • ".join(details["languages"])
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("🎯 Job Role Matching")

            st.caption(
                "Role matching is based on the skills detected from your resume."
            )

            for result in role_matches:

                role = result["role"]
                score = result["score"]
                matched = result["matched"]

                st.markdown(
                    f"### {role}"
                )

                st.progress(
                    score / 100
                )

                st.write(
                    f"**Match:** {score}%"
                )

                if matched:

                    st.write(
                        "**Matched skills:** "
                        + ", ".join(matched)
                    )

                else:

                    st.write(
                        "**Matched skills:** None detected"
                    )

                st.divider()

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("💡 Resume Improvement Suggestions")

            for suggestion in suggestions:

                st.write(
                    "✅ " + suggestion
                )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("🇮🇳 Job Search – India")

            st.write(
                "Use these trusted job platforms to search and apply for current openings."
            )

            jobs = [
                (
                    "LinkedIn Jobs",
                    "https://www.linkedin.com/jobs/"
                ),
                (
                    "Naukri",
                    "https://www.naukri.com/"
                ),
                (
                    "Indeed India",
                    "https://in.indeed.com/"
                ),
                (
                    "Internshala",
                    "https://internshala.com/"
                ),
                (
                    "National Career Service",
                    "https://www.ncs.gov.in/"
                )
            ]

            for name, url in jobs:

                st.markdown(
                    f"""
                    <div class="job-card">
                        <h3>{name}</h3>
                        <a class="apply-button"
                           href="{url}"
                           target="_blank">
                           Search & Apply
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("📌 Resume Analysis Summary")

            st.write(
                "The analyzer extracts information available in the uploaded PDF and provides an estimated ATS score, skill-based role matching and improvement suggestions."
            )

            st.info(
                "Note: The ATS score is an estimate created by this project. It is not an official score from any company's ATS system."
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )


    except Exception as error:

        st.error(
            "Something went wrong while reading the PDF."
        )

        st.write(
            f"Error details: {error}"
        )


else:

    st.info(
        "👆 Upload your resume PDF above to start the analysis."
    )