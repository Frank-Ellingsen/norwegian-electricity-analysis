# Contributing Guidelines

These guidelines define strict rules for contributing to this repository. All contributors must follow the standards described in `skill.md`.

---

## 1. Repository Structure
All files must remain within the existing structure:

/src
/data
/analysis
/visuals
/docs

Code

Do not create new top‑level directories unless explicitly instructed.

---

## 2. File Rules
- Do not overwrite existing files without explicit approval.
- New files must be placed in the correct directory.
- All file content must be complete and reproducible.
- All code must include imports, logging, and example usage where relevant.

---

## 3. Coding Standards

### Python
- PEP8 formatting.
- Modular functions only.
- Docstrings required.
- Logging required for ETL, modeling, file I/O, and error handling.
- No silent failures.

### SQL
- Use CTEs.
- Explicit column names.
- ISO date formats.
- No ambiguous time zones.

### Data
- CSV is the default storage format.
- SQLite is the analytical store.
- Excel is for inspection only.

---

## 4. Commit Rules

### Allowed commit message format
<type>: <short description>

<optional detailed explanation>

Code

### Allowed commit types
- feat  
- fix  
- docs  
- refactor  
- data  
- analysis  
- visuals  
- chore  

### Prohibited
- Vague messages such as “update”, “misc”, “changes”
- Auto‑generated timestamps
- References to internal agent behavior

---

## 5. Branching Rules

### Allowed branch names
feature/<name>
fix/<name>
analysis/<name>
docs/<name>

Code

Rules:
- Lowercase only.
- Hyphens instead of spaces.
- Maximum length: 40 characters.
- No direct commits to `main` unless explicitly instructed.

---

## 6. Pull Request Rules

### Required PR Template
Summary
Short explanation of what the PR does.

Changes