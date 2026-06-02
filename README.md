# 🎓 GradeGraph — Student Performance Analyzer

A Streamlit-based academic performance analysis dashboard that ingests student mark sheets from Excel, classifies learners, and surfaces subject-wise insights for teachers and department coordinators.

**Live App →** https://gradegraph-computerdepartment.streamlit.app/

---

## Features

- **Excel Import** — reads hierarchical multi-subject mark sheets starting at the `SR.No.` row and flattens headers automatically
- **Learner Classification** — tags each student as **Bright (D)**, **Average (OK)**, or **Weak (W)** using academic performance percentage and coding expertise level
- **Dashboard** — KPI cards, donut chart of category distribution, box plot of performance spread, top-10 bright learners, and a full weak-learner attention list
- **Individual Student Lookup** — search by SR.No. or name; see per-subject scores and coding level
- **Subject-wise Analysis** — average, max, min, std dev for any subject; top and bottom 10 performers per subject
- **Insights & Recommendations** — subject difficulty classification (Easy / Moderate / Difficult based on MSE + ESE averages), actionable priority recommendations, JSON report export
- **Reports & Export** — CSV downloads for bright/weak learner lists, comprehensive JSON report
- **Theming** — Default and Dark Mode toggle in sidebar

---

## Project Structure

```
GRADEGRAPH/
├── app.py              # Streamlit UI — all pages and routing
├── services/           # Core logic (data processing, classification, subject helpers)
├── requirements.txt    # Python dependencies
├── desktop.ini         # Windows metadata (ignore)
└── README.md
```

---

## Dataset Format

The app expects an `.xlsx` file where the first meaningful row contains `SR.No.` as its first cell. Subject marks are organized with hierarchical column headers like:

| SR.No. | Name | Roll No | Mathematics – ISE | Mathematics – MSE | Mathematics – ESE | Mathematics – PR | … | Coding Expertise |
|--------|------|---------|-------------------|-------------------|-------------------|-----------------|---|-----------------|

- **ISE / MSE** — Internal/Mid-Semester Exams (max 25 each)  
- **ESE** — End-Semester Exam (max 60)  
- **PR / PRACTICAL** — Practical assessment (max 25)  
- **TW** — Term Work (max 50)  
- **Coding Expertise** — `A` (Advanced), `I` (Intermediate), `B` (Beginner)

Sample dataset: [Google Sheets link](https://docs.google.com/spreadsheets/d/1C_knPEfpg2FyuutvDw-VlXP0NPnNIExM/edit?usp=sharing)

---

## Classification Logic

| Category | Criteria |
|----------|----------|
| **Bright** | High academic performance % + strong coding expertise |
| **Average** | Mid-range performance |
| **Weak** | Below threshold — flagged for intervention |

Academic Performance % = (total marks obtained) ÷ (total maximum marks possible) × 100  
Practical % is calculated separately from columns matching `PRACTICAL` or `\bPR\b`.

---

## Setup

### 1. Clone

```bash
git clone https://github.com/KshitijT15/GRADEGRAPH
cd GRADEGRAPH
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies include: `streamlit`, `pandas`, `numpy`, `plotly`, `openpyxl`

### 4. Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` by default.

---

## Usage

1. Navigate to **📤 Upload** in the sidebar and upload your `.xlsx` mark sheet.
2. The app processes the file, classifies students, and stores results in session state.
3. Use the sidebar to switch between **Dashboard**, **Students**, **Subjects**, **Insights**, and **Reports**.
4. The sidebar snapshot shows live counts of Bright / Weak students across all pages.
5. To load a new dataset, click **🔄 Refresh Data** in the sidebar.

---

## Deployment (Streamlit Community Cloud)

The app is already deployed. To redeploy your own fork:

1. Push your repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select repo `GRADEGRAPH`, branch `main`, main file `app.py`.
4. Click **Deploy**. No secrets or environment variables required.

---

## Contributors

- **Kshitij Thorat** — [KshitijT15](https://github.com/KshitijT15) — core development
- **Shweta Tate** — [Shwetatate](https://github.com/Shwetatate) — contributor

Contributions welcome — open an issue or pull request!
