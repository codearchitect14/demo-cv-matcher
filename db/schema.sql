CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title TEXT,
    domain TEXT,
    location TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    total_years_required INTEGER,
    job_description TEXT
);

CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    name TEXT,
    location TEXT,
    expected_salary_min INTEGER,
    expected_salary_max INTEGER,
    domain TEXT
);

CREATE TABLE candidate_experience (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER,
    skill TEXT,
    years INTEGER,
    description TEXT
);

CREATE TABLE job_mandatory_skills (
    id SERIAL PRIMARY KEY,
    job_id INTEGER,
    skill TEXT,
    min_years_required INTEGER
);
