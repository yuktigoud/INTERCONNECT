from flask import Flask, render_template, request, redirect, url_for, session
import csv

app = Flask(__name__)
app.secret_key = "secret123"

users = {"admin": "admin"}   # simple in-memory users


def load_jobs():
    jobs = []
    with open("jobs.csv", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        jobs.extend(reader)
    return jobs


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in users and users[u] == p:
            session["user"] = u
            return redirect("/")
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in users:
            error = "User already exists"
        else:
            users[u] = p
            return redirect("/login")

    return render_template("signup.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        session["search_count"] = session.get("search_count", 0) + 1

        recommended = []

        user_skills = request.form["skills"].lower().split(",")
        user_location = request.form["location"].lower()
        user_domain = request.form["interest"].lower()

        resume = request.files.get("resume")
        extracted_skills = []

        if resume:
            content = resume.read().decode(errors="ignore").lower()

            for skill in ["python", "java", "sql", "html", "css", "javascript", "excel"]:
                if skill in content:
                    extracted_skills.append(skill)

        # merge manual + resume skills
        user_skills = list(set(user_skills + extracted_skills))

        for job in load_jobs():
            score = 0
            job_skills = job["skills"].lower().split(",")

            for skill in user_skills:
                if skill.strip() in job_skills:
                    score += 2

            if user_location in job["location"].lower():
                score += 3

            if user_domain in job["domain"].lower():
                score += 2

            if score > 0:
                job_copy = job.copy()
                job_copy["score"] = score
                recommended.append(job_copy)

        recommended.sort(key=lambda x: x["score"], reverse=True)
        return render_template("results.html", jobs=recommended)

    return render_template("index.html")

@app.route("/job/<int:job_id>")
def job_detail(job_id):
    for job in load_jobs():
        if int(job["job_id"]) == job_id:
            return render_template("job.html", job=job, score="Good Match")
@app.route("/apply/<int:job_id>")
def apply_job(job_id):
    return render_template("apply_success.html")
@app.route('/skill-gap', methods=['GET','POST'])
def skill_gap():
    missing = []
    matched = []
    required = []
    role_name = ""
    note = None

    ROLE_SKILLS = {
        "data scientist": ["python", "sql", "ml", "statistics"],
        "web developer": ["html", "css", "javascript", "flask"],
        "ai engineer": ["python", "ml", "deep learning"],
        "data analyst": ["excel", "sql", "python", "data visualization"],
        "frontend developer": ["html", "css", "javascript", "react"]
    }
    ROLE_ALIASES = {
        "data science": "data scientist",
        "data sci": "data scientist",
        "ml engineer": "ai engineer",
        "front end developer": "frontend developer",
        "front-end developer": "frontend developer",
        "web dev": "web developer",
        "frontend": "frontend developer"
    }

    if request.method == 'POST':
        skills = [s.strip() for s in request.form['skills'].lower().split(',') if s.strip()]
        role_input = request.form['role'].lower().strip()
        role_key = ROLE_ALIASES.get(role_input, role_input)
        role_name = role_key

        required = ROLE_SKILLS.get(role_key, [])

        if not required:
            note = "Role not found. Try: Data Scientist, Web Developer, AI Engineer, Data Analyst, Frontend Developer."
        else:
            for s in required:
                if s in skills:
                    matched.append(s)
                else:
                    missing.append(s)

    return render_template(
        'skill_gap.html',
        missing=missing,
        matched=matched,
        required=required,
        role_name=role_name,
        note=note
    )

@app.route('/confidence', methods=['GET','POST'])
def confidence():
    score = None
    feedback = []
    resume_score = None

    KEYWORDS = ["python", "sql", "javascript", "html", "css", "flask", "react", "ml", "excel", "git"]
    ACTION_WORDS = ["built", "developed", "designed", "implemented", "created", "led", "optimized", "deployed"]

    if request.method == 'POST':
        # Confidence score
        skills = int(request.form.get('skills', 0) or 0)
        projects = int(request.form.get('projects', 0) or 0)
        internships = int(request.form.get('internships', 0) or 0)
        score = (skills*0.5) + (projects*0.3) + (internships*0.2)

        # Resume analyzer (simple AI-like logic)
        resume_text = request.form.get('resume_text', '').lower()
        skills_text = request.form.get('skills_text', '').lower()
        combined = f"{resume_text} {skills_text}"

        keyword_hits = [k for k in KEYWORDS if k in combined]
        action_hits = [w for w in ACTION_WORDS if w in resume_text]

        resume_score = min(100, (len(keyword_hits) * 6) + (len(action_hits) * 4) + (projects * 5) + (internships * 7))

        feedback.append(f"Detected skills: {', '.join(keyword_hits) if keyword_hits else 'None found'}")
        feedback.append(f"Action verbs used: {', '.join(action_hits) if action_hits else 'Add action verbs like built, designed, implemented'}")

        if projects < 2:
            feedback.append("Add 2+ projects with measurable outcomes.")
        if internships < 1:
            feedback.append("If possible, include internship or real-world experience.")
        if len(keyword_hits) < 4:
            feedback.append("Include more relevant skills aligned to your target role.")

    return render_template('confidence.html', score=score, resume_score=resume_score, feedback=feedback)

@app.route('/readiness', methods=['GET','POST'])
def readiness():
    result = None

    if request.method == 'POST':
        score = int(request.form['score'])

        if score < 40:
            result = "Go for Internship"
        elif score < 70:
            result = "Internship + Entry Level Jobs"
        else:
            result = "You are Job Ready"

    return render_template('readiness.html', result=result)
@app.route('/learning', methods=['GET','POST'])
def learning():
    resources_list = []

    resources = {
        "python": [
            ("Python Full Course (freeCodeCamp)", "https://www.youtube.com/watch?v=rfscVS0vtbw"),
            ("Official Python Docs", "https://docs.python.org/3/"),
            ("Python Practice", "https://www.hackerrank.com/domains/python")
        ],
        "sql": [
            ("SQL Tutorial (W3Schools)", "https://www.w3schools.com/sql/"),
            ("SQL Practice (LeetCode)", "https://leetcode.com/problemset/database/"),
            ("Mode SQL Tutorial", "https://mode.com/sql-tutorial/")
        ],
        "ml": [
            ("Machine Learning (Coursera)", "https://www.coursera.org/learn/machine-learning"),
            ("Google ML Crash Course", "https://developers.google.com/machine-learning/crash-course"),
            ("ML Glossary", "https://developers.google.com/machine-learning/glossary")
        ],
        "flask": [
            ("Flask Docs", "https://flask.palletsprojects.com/"),
            ("Flask Mega-Tutorial", "https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world"),
            ("Flask Quickstart", "https://flask.palletsprojects.com/en/latest/quickstart/")
        ],
        "javascript": [
            ("JavaScript Guide (MDN)", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"),
            ("JavaScript Info", "https://javascript.info/"),
            ("Eloquent JavaScript", "https://eloquentjavascript.net/")
        ],
        "html": [
            ("HTML Guide (MDN)", "https://developer.mozilla.org/en-US/docs/Web/HTML"),
            ("HTML Tutorial (W3Schools)", "https://www.w3schools.com/html/"),
            ("HTML Crash Course", "https://www.youtube.com/watch?v=UB1O30fR-EE")
        ],
        "css": [
            ("CSS Guide (MDN)", "https://developer.mozilla.org/en-US/docs/Web/CSS"),
            ("CSS Tricks", "https://css-tricks.com/"),
            ("Flexbox Froggy", "https://flexboxfroggy.com/")
        ],
        "react": [
            ("React Docs", "https://react.dev/learn"),
            ("React Tutorial (Scrimba)", "https://scrimba.com/learn/learnreact"),
            ("React Patterns", "https://reactpatterns.com/")
        ],
        "data science": [
            ("Kaggle Learn", "https://www.kaggle.com/learn"),
            ("Pandas Docs", "https://pandas.pydata.org/docs/"),
            ("Data Science Roadmap", "https://roadmap.sh/data-science")
        ]
    }

    if request.method == 'POST':
        skill = request.form['skill'].lower()
        resources_list = resources.get(skill, [])

    return render_template('learning.html', resources=resources_list, skill_query=request.form.get('skill', ''))


@app.route('/resume-analyzer', methods=['GET', 'POST'])
def resume_analyzer():
    return redirect(url_for('confidence'))


@app.route('/domain-switch', methods=['GET', 'POST'])
def domain_switch():
    advice = []
    bridge_skills = []

    DOMAIN_SKILLS = {
        "data science": ["python", "sql", "statistics", "pandas", "ml"],
        "web development": ["html", "css", "javascript", "react", "flask"],
        "software engineering": ["python", "java", "git", "oop", "ds"],
        "ai/ml": ["python", "ml", "deep learning", "tensorflow", "data"]
    }

    if request.method == 'POST':
        current = request.form.get('current_domain', '').lower().strip()
        target = request.form.get('target_domain', '').lower().strip()
        skills = [s.strip() for s in request.form.get('skills', '').lower().split(',') if s.strip()]

        current_skills = DOMAIN_SKILLS.get(current, [])
        target_skills = DOMAIN_SKILLS.get(target, [])

        if not target_skills:
            advice.append("Target domain not found. Try: Data Science, Web Development, Software Engineering, AI/ML.")
        else:
            missing = [s for s in target_skills if s not in skills]
            bridge_skills = missing
            overlap = [s for s in target_skills if s in skills]

            advice.append(f"Your overlapping skills for {target.title()}: {', '.join(overlap) if overlap else 'None yet'}")
            advice.append("Focus on 2-3 bridge skills first, then build projects in the target domain.")

    return render_template('domain_switch.html', advice=advice, bridge_skills=bridge_skills)


@app.route('/location-reality', methods=['GET', 'POST'])
def location_reality():
    result = None
    detail = None

    LOCATION_DEMAND = {
        "hyderabad": ["data science", "software engineering", "web development"],
        "bengaluru": ["data science", "ai/ml", "software engineering", "web development"],
        "pune": ["software engineering", "web development"],
        "chennai": ["software engineering", "data science"],
        "mumbai": ["data science", "web development"]
    }

    if request.method == 'POST':
        location = request.form.get('location', '').lower().strip()
        domain = request.form.get('domain', '').lower().strip()

        if location in LOCATION_DEMAND:
            hot_domains = LOCATION_DEMAND[location]
            if domain in hot_domains:
                result = "High demand"
                detail = "This domain is actively hiring in your location."
            else:
                result = "Moderate demand"
                detail = "Consider adding adjacent skills or applying to nearby hubs."
        else:
            result = "Unknown demand"
            detail = "Location not in list. Try major cities like Bengaluru, Hyderabad, Pune, Chennai, Mumbai."

    return render_template('location_reality.html', result=result, detail=detail)


if __name__ == "__main__":
    app.run(debug=True)
