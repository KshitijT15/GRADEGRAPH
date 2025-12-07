📊✨ GRADEGRAPH — Student Performance Analysis & Insights

GRADEGRAPH is a Python-based academic performance analysis system that reads student data from an Excel sheet 📘, processes subject-wise marks 📚, identifies weak/average/bright learners 🎯, and generates meaningful insights along with visualizations 📈.

Designed for teachers, mentors, coordinators, and students, GRADEGRAPH provides a clear, data-driven picture of academic performance.

🚀✨ Features

📥 Import student data directly from Excel

🧮 Automatic learner classification: Weak → W, Average → OK, Bright → D

📊 Subject-wise analysis with personalized recommendations

🏆 Identify Top 10 performers

🚨 Identify Students needing attention

📘 Subject difficulty insights using class averages

🧩 Clean and modular architecture

💻 Easy Streamlit integration for dashboard UI

📁 Folder Structure
GRADEGRAPH/
├── app.py                     # Main UI & routing (Streamlit)
├── processor.py               # Core logic for analysis & classification
├── requirements.txt           # Dependencies
├── README.md                  # Documentation
└── sample/                    # (Optional) Sample datasets & exports

📥🧾 Excel Dataset Used

Add your dataset link or file here.

Dataset Name: Gradegraph Dataset
📌 (https://docs.google.com/spreadsheets/d/1C_knPEfpg2FyuutvDw-VlXP0NPnNIExM/edit?usp=sharing&ouid=114272333005547331230&rtpof=true&sd=true)

📐 Expected Dataset Format

The Excel sheet should include:

🧑‍🎓 Student details

📘 Subject-wise marks:

Subject → ISE, MSE, ESE, Practical

💻 Coding skill levels

📊 Additional academic metrics (if available)

📋 Example Column Structure
Column
SR.No.
Student Name
Mathematics – ISE
Mathematics – MSE
Mathematics – ESE
Physics – ISE
Physics – MSE
… and more
⚙️ Installation
⬇️ 1. Clone the Repository
git clone https://github.com/KshitijT15/GRADEGRAPH
cd GRADEGRAPH

📦 2. Install Dependencies
pip install -r requirements.txt

▶️ Running the Application
🖥️ Standard Python Execution
python app.py

🌐 Streamlit Dashboard
streamlit run app.py

🧠🔍 How It Works (High-Level Overview)

📥 Excel Import

Reads data starting at the SR.No. column

Flattens hierarchical headers automatically

🛠️ Data Processing

Cleaning, transformation, and subject-wise normalization

🎯 Classification
Learners are categorized as:

❗ W → Weak

⚪ OK → Average

🌟 D → Bright

📊 Insights Generated

🏆 Top performers

🚨 Students needing attention

📘 Subject difficulty levels

💡 Student-wise recommendations

📈 Visualization

Streamlined charts and performance graphs

Exportable insights

📈 Key Insights
🏆 Top Performers

Students with the highest academic percentage.

🚨 Students Needing Attention

Learners who fall below performance thresholds.

📘 Subject Difficulty

Low class average → Higher difficulty.

💡 Recommendations

Personalized subject-wise suggestions for weak learners.

📦 Dependencies

Example requirements.txt:

pandas
numpy
matplotlib
openpyxl
streamlit

📸 Screenshots / Demo

<img width="1588" height="906" alt="Screenshot 2025-12-01 233439" src="https://github.com/user-attachments/assets/547e3df0-4a1e-46fb-923c-2b018a496f53" />

Link- https://gradegraph-computerdepartment.streamlit.app/

Contributions are always welcome! 💙
