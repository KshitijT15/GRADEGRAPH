import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from services import (
    process_excel_file,
    get_subject_list,
    get_student_performance,
    get_dynamic_subject_recommendations,
    get_threshold_based_recommendations,
    get_subject_exam_types,
    get_subject_marks,
    get_subject_marks_summary,
    extract_max_marks_from_header,
)
import re
import numpy as np
import json
from datetime import datetime
import io

def _is_practical_col(col_name):
    if not col_name or pd.isna(col_name):
        return False
    col_upper = str(col_name).upper()
    if 'TW' in col_upper and 'PR' not in col_upper:
        return False
    return ('PRACTICAL' in col_upper) or (re.search(r'\bPR\b', col_upper) is not None)

def _row_percentage(row, cols):
    obtained_total = 0.0
    max_total = 0.0
    for c in cols:
        val = row.get(c, np.nan)
        try:
            val = float(val)
        except Exception:
            val = np.nan
        if pd.notna(val):
            obtained_total += val
            max_total += extract_max_marks_from_header(c)
    return (obtained_total / max_total) * 100.0 if max_total > 0 else np.nan

def _get_max_marks_for_subject(subject_name, exam_type=None):
    """
    Get maximum marks for a subject and exam type
    """
    if exam_type:
        exam_upper = exam_type.upper()
        if 'ESE' in exam_upper:
            return 60
        elif 'ISE' in exam_upper or 'MSE' in exam_upper:
            return 25
        elif 'PRACTICAL' in exam_upper or 'PR' in exam_upper:
            return 25
        elif 'TW' in exam_upper:
            return 50
        else:
            return 100
    else:
        # Default max marks for subject (sum of all exam types)
        return 100

# Configure Streamlit page
st.set_page_config(
    page_title="GradeGraph - Student Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS with black and blue theme (#0149ac)
st.markdown("""
<style>
    /* Main App Background */
    .stApp {
        background-color: #0f1115;
        color: #ffffff;
    }
    
    /* Simple Header */
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #0149ac;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background-color: #0149ac;
    }
    
    /* Button Styling */
    .stButton > button {
        background-color: #0149ac;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #013a8a;
        color: white;
    }
    
    /* Selectbox Styling */
    .stSelectbox > div > div {
        background-color: #0f1115;
        color: #ffffff;
        border: 2px solid #0149ac;
        border-radius: 6px;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #013a8a;
    }
    
    /* File Uploader Styling */
    .stFileUploader > div {
        background-color: #0f1115;
        color: #ffffff;
        border: 2px dashed #0149ac;
        border-radius: 6px;
    }
    
    .stFileUploader > div:hover {
        border-color: #013a8a;
        background-color: #f8f9ff;
    }
    
    /* Metric Cards */
    .metric-container {
        background-color: #141821;
        border: 1px solid rgba(1,73,172,0.35);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
        color: #ffffff;
    }
    
    /* Success Messages */
    .stSuccess {
        background-color: rgba(1,73,172,0.12);
        border-left: 4px solid #0149ac;
        color: #cfe2ff;
    }
    
    /* Info Messages */
    .stInfo {
        background-color: rgba(1,73,172,0.12);
        border-left: 4px solid #0149ac;
        color: #cfe2ff;
    }
    
    /* Warning Messages */
    .stWarning {
        background-color: #332a19;
        border-left: 4px solid #f59e0b;
        color: #f8d7a0;
    }
    
    /* Error Messages */
    .stError {
        background-color: #3a1f20;
        border-left: 4px solid #ef4444;
        color: #f8d7da;
    }
</style>
""", unsafe_allow_html=True)

# Main title - GradeGraph
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem; padding: 2rem 0;">
    <h1 style="font-size: 4rem; font-weight: 800; color: #0149ac; margin: 0; letter-spacing: 2px; text-shadow: 2px 2px 8px rgba(1, 73, 172, 0.4);">
        🎓 GradeGraph
    </h1>
    <h3 style="font-size: 1.4rem; font-weight: 400; color: #b0b8c4; margin: 0.8rem 0 0 0; font-style: italic; letter-spacing: 1px;">
        Student Performance Analyzer
    </h3>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'df_full' not in st.session_state:
    st.session_state.df_full = None
if 'df_suggestions' not in st.session_state:
    st.session_state.df_suggestions = None

# Simple Sidebar Navigation
st.sidebar.markdown("### 📊 Navigation")

# Simple navigation options
navigation_options = {
    "📤 Upload": "Upload Excel files",
    "📈 Dashboard": "Analytics dashboard", 
    "👥 Students": "Student analysis",
    "📊 Subjects": "Subject analysis",
    "🎯 Insights": "Performance insights",
    "📋 Reports": "Export reports"
}

page = st.sidebar.selectbox(
    "Select Page", 
    list(navigation_options.keys())
)

# Simple theme selector
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 Theme")
theme = st.sidebar.selectbox("Choose Theme", ["Default", "Dark Mode"])

# Apply theme-specific CSS
if theme == "Dark Mode":
    st.markdown("""
    <style>
        .stApp {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        .main-header {
            color: #ffffff !important;
        }
        .metric-card {
            background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
            color: #ffffff;
        }
        .interactive-card {
            background: #2d2d2d;
            color: #ffffff;
        }
        .stButton > button {
            background-color: #0149ac;
            color: white;
        }
        .stButton > button:hover {
            background-color: #013a8a;
        }
        .css-1d391kg {
            background-color: #0149ac;
        }
    </style>
    """, unsafe_allow_html=True)

# Simple data management section
if st.session_state.get('df_full') is not None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔄 Data Management")
    if st.sidebar.button("🔄 Refresh Data", help="Reload and reprocess current data"):
        st.session_state.df_full = None
        st.session_state.df_suggestions = None
        st.rerun()


# Persistent dashboard snapshot in sidebar
if st.session_state.get('df_full') is not None and st.session_state.get('df_suggestions') is not None:
    df_full_sidebar = st.session_state.df_full
    df_sugg_sidebar = st.session_state.df_suggestions
    with st.sidebar.expander("📊 Dashboard Snapshot", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Students", len(df_full_sidebar))
        with col_b:
            st.metric("Subjects", len(get_subject_list(df_full_sidebar)))
        col_c, col_d = st.columns(2)
        with col_c:
            bright = (df_full_sidebar['Category'] == 'Bright').sum() if 'Category' in df_full_sidebar.columns else 0
            st.metric("Bright", int(bright))
        with col_d:
            weak = (df_full_sidebar['Category'] == 'Weak').sum() if 'Category' in df_full_sidebar.columns else 0
            st.metric("Weak", int(weak))

# File upload section
if page == "📤 Upload":
    uploaded_file = st.file_uploader(
        "Choose an Excel file",
        type=["xlsx"],
        help="Upload an Excel file containing student performance data starting with 'SR.No.' row"
    )

    if uploaded_file:
        try:
            with st.spinner("🔄 Processing Excel file..."):
                df_full, df_suggestions = process_excel_file(uploaded_file)

            # Store in session state
            st.session_state.df_full = df_full
            st.session_state.df_suggestions = df_suggestions

            st.success("✅ File processed successfully!")

            # Calculate counts with debugging
            if 'Category' in df_full.columns:
                bright_count = len(df_full[df_full['Category'] == 'Bright'])
                weak_count = len(df_full[df_full['Category'] == 'Weak'])
                
                # Debug information
                st.info(f"🔍 Debug Info: Category column found. Bright: {bright_count}, Weak: {weak_count}")
                st.info(f"Available categories: {df_full['Category'].value_counts().to_dict()}")
            else:
                bright_count = 0
                weak_count = 0
                st.error("❌ Category column not found in dataframe!")
                st.info(f"Available columns: {list(df_full.columns)}")
            
            # Prominent display of bright learners count
            st.markdown(f"""
            <div style="text-align: center; margin: 2rem 0; padding: 1.5rem; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); border-radius: 12px; box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);">
                <h2 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700;">
                    🌟 {bright_count} BRIGHT LEARNERS
                </h2>
                <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                    Out of {len(df_full)} total students ({bright_count/len(df_full)*100:.1f}% if len(df_full) > 0 else 0%)
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Display basic statistics (REMOVED avg and excellence scores)
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("📚 Total Students", len(df_full))

            with col2:
                subjects = get_subject_list(df_full)
                st.metric("📖 Subjects", len(subjects))

            with col3:
                bright_count = len(df_full[df_full['Category'] == 'Bright']) if 'Category' in df_full.columns else 0
                st.metric("🌟 Bright Learners", bright_count)

            with col4:
                weak_count = len(df_full[df_full['Category'] == 'Weak']) if 'Category' in df_full.columns else 0
                st.metric("⚠️ Weak Learners", weak_count)

            # Calculation Logic Explanation
            st.info("""
            **Calculation Logic:**
            - Academic Performance %: Ratio of total marks obtained vs. total maximum marks possible
            - Practical Performance %: Calculated from practical assessments (PRACTICAL/PR columns)
            - Student Classification: Based on Academic Performance and Coding Expertise levels
            """)

            # Show preview of processed data
            with st.expander("📋 Preview Processed Data", expanded=False):
                st.subheader("🔍 Full Processed Data (Sample)")
                st.dataframe(df_full.head(10), use_container_width=True)

                st.subheader("📊 Learner Classification")
                st.dataframe(df_suggestions, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error while processing file: {e}")
            st.error("Please ensure your Excel file follows the expected format with 'SR.No.' as the starting row.")

    else:
        st.info("📌 Please upload a student Excel file to begin analysis.")

# Enhanced Dashboard page with modern features
elif page == "📈 Dashboard":
    if st.session_state.df_full is not None:
        df_full = st.session_state.df_full
        df_suggestions = st.session_state.df_suggestions

        st.header("📈 Performance Dashboard")
        
        # Calculate bright learners count with debugging
        if 'Category' in df_full.columns:
            bright_count = len(df_full[df_full['Category'] == 'Bright'])
            weak_count = len(df_full[df_full['Category'] == 'Weak'])
            
            # Debug information
            with st.expander("🔍 Debug Information", expanded=False):
                st.info(f"Category column found. Bright: {bright_count}, Weak: {weak_count}")
                st.info(f"Available categories: {df_full['Category'].value_counts().to_dict()}")
                st.dataframe(df_full[['Name', 'Category', 'Academic_Performance_%']].head(10))
        else:
            bright_count = 0
            weak_count = 0
            st.error("❌ Category column not found in dataframe!")
            st.info(f"Available columns: {list(df_full.columns)}")
        
        # Prominent display of bright learners count
        st.markdown(f"""
        <div style="text-align: center; margin: 2rem 0; padding: 1.5rem; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); border-radius: 12px; box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);">
            <h2 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700;">
                🌟 {bright_count} BRIGHT LEARNERS
            </h2>
            <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                Out of {len(df_full)} total students ({bright_count/len(df_full)*100:.1f}% if len(df_full) > 0 else 0%)
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key Performance Indicators
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_students = len(df_full)
            st.metric(
                "👥 Total Students", 
                total_students,
                help="Total number of students in the dataset"
            )
        
        with col2:
            subjects_count = len(get_subject_list(df_full))
            st.metric(
                "📚 Subjects", 
                subjects_count,
                help="Total number of subjects analyzed"
            )
        
        with col3:
            if 'Academic_Performance_%' in df_full.columns:
                avg_performance = df_full['Academic_Performance_%'].mean()
                st.metric(
                    "📈 Avg Performance", 
                    f"{avg_performance:.1f}%",
                    help="Average academic performance across all students"
                )
            else:
                st.metric("📈 Avg Performance", "N/A")
        
        with col4:
            bright_count = len(df_full[df_full['Category'] == 'Bright']) if 'Category' in df_full.columns else 0
            st.metric(
                "🌟 Bright Students", 
                bright_count,
                delta=f"{bright_count/total_students*100:.1f}%" if total_students > 0 else "0%",
                help="Number of bright performing students"
            )
        
        with col5:
            weak_count = len(df_full[df_full['Category'] == 'Weak']) if 'Category' in df_full.columns else 0
            st.metric(
                "⚠️ Weak Students", 
                weak_count,
                delta=f"{weak_count/total_students*100:.1f}%" if total_students > 0 else "0%",
                help="Number of students needing attention"
            )
        
        
        # Use full dataset without filters
        filtered_df = df_full
        
        # Interactive Visualizations
        st.subheader("📊 Interactive Visualizations")
        
        # Main charts row
        col1, col2 = st.columns(2)

        with col1:
            # Category distribution with donut chart
            category_counts = df_suggestions['Category'].value_counts()
            fig_donut = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="📊 Student Category Distribution",
                hole=0.4,
                color_discrete_map={
                    'Bright': '#28a745',
                    'Average': '#ffc107',
                    'Weak': '#dc3545',
                    'Unknown': '#6c757d'
                }
            )
            fig_donut.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_donut, use_container_width=True)

        with col2:
            # Performance distribution with box plot
            if 'Academic_Performance_%' in filtered_df.columns:
                fig_box = px.box(
                    filtered_df,
                    y='Academic_Performance_%',
                    title="📈 Academic Performance Distribution",
                    color_discrete_sequence=['#667eea']
                )
                fig_box.update_layout(
                    yaxis_title="Academic Performance %",
                    showlegend=False
                )
                st.plotly_chart(fig_box, use_container_width=True)
            else:
                st.info("Academic Performance data not available")

        # Performance Leaders & Areas for Improvement
        st.subheader("🏆 Performance Leaders & Areas for Improvement")
        
        col3, col4 = st.columns(2)

        with col3:
            if 'Academic_Performance_%' in filtered_df.columns:
                weak_count_matched = int((df_suggestions['Category'] == 'Weak').sum())
                matched_top_count = min(weak_count_matched, len(filtered_df)) if weak_count_matched > 0 else 0
                st.markdown(f"### 🏆 Bright Learners (Top {matched_top_count} matched to Weak)")

                if matched_top_count > 0:
                    bright_learners_matched = filtered_df.nlargest(matched_top_count, 'Academic_Performance_%')[['SR.No', 'Name', 'Academic_Performance_%', 'Category']].copy()
                    bright_learners_matched['Academic_Performance_%'] = bright_learners_matched['Academic_Performance_%'].round(2)

                    # Add ranking
                    bright_learners_matched['Rank'] = range(1, len(bright_learners_matched) + 1)
                    bright_learners_display = bright_learners_matched[['Rank', 'Name', 'Academic_Performance_%', 'Category']]

                    st.dataframe(
                        bright_learners_display,
                        use_container_width=True,
                        hide_index=True
                    )

                    csv_matched = bright_learners_matched.to_csv(index=False)
                    st.download_button(
                        "📥 Download Bright Learners (Matched)",
                        csv_matched,
                        "bright_learners_matched.csv",
                        "text/csv"
                    )
                else:
                    st.info("No weak learners detected, so no matched Bright learners list to display.")
            else:
                st.info("Performance data not available")

        with col4:
            st.markdown("### ⚠️ Students Needing Attention")
            if 'Academic_Performance_%' in filtered_df.columns:
                # Show ALL weak learners, sorted by lowest performance first
                if 'Category' in filtered_df.columns:
                    weak_learners = filtered_df[filtered_df['Category'] == 'Weak'][['SR.No', 'Name', 'Academic_Performance_%', 'Category']]
                    if len(weak_learners) > 0:
                        weak_learners = weak_learners.sort_values('Academic_Performance_%', ascending=True).copy()
                        weak_learners['Academic_Performance_%'] = weak_learners['Academic_Performance_%'].round(2)

                        # Add ranking
                        weak_learners['Rank'] = range(1, len(weak_learners) + 1)
                        weak_learners = weak_learners[['Rank', 'Name', 'Academic_Performance_%', 'Category']]

                        st.dataframe(
                            weak_learners,
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No weak students identified in the current dataset.")
                else:
                    st.info("Category data not available to determine weak learners.")
            else:
                st.info("Performance data not available")

    else:
        st.warning("📤 Please upload and process an Excel file first.")

# Student search page
elif page == "👥 Students":
    if st.session_state.df_full is not None:
        df_full = st.session_state.df_full

        st.header("👥 Individual Student Analysis")

        # Search options
        search_col1, search_col2 = st.columns([2, 1])

        with search_col1:
            search_query = st.text_input(
                "🔍 Search Student",
                placeholder="Enter SR.No, Roll No, or Name",
                help="You can search by student number or name"
            )

        with search_col2:
            search_button = st.button("🔍 Search", type="primary")

        if search_query and search_button:
            student_data = get_student_performance(df_full, search_query)

            if student_data:
                st.success(f"✅ Found student: {student_data['Name']}")

                # Student basic info
                info_col1, info_col2, info_col3 = st.columns(3)

                with info_col1:
                    st.metric("📝 SR.No", str(student_data['SR.No']))

                with info_col2:
                    roll_no = student_data.get('Roll No', 'N/A')
                    st.metric("🎓 Roll No", str(roll_no))

                with info_col3:
                    category = student_data.get('Category', 'Unknown')
                    st.metric("📊 Category", str(category))

                # Performance metrics (REMOVED Overall Average)
                perf_col1, perf_col2 = st.columns(2)

                with perf_col1:
                    academic_perf = student_data.get('Academic_Performance_%', 0)
                    if pd.notna(academic_perf) and academic_perf > 0:
                        st.metric("🎯 Academic %", f"{float(academic_perf):.1f}%")
                    else:
                        st.metric("🎯 Academic %", "N/A")

                with perf_col2:
                    coding_expertise = student_data.get('Coding_Expertise', 'N/A')
                    if pd.notna(coding_expertise):
                        coding_full = {'A': 'Advanced', 'I': 'Intermediate', 'B': 'Beginner'}.get(str(coding_expertise), str(coding_expertise))
                        st.metric("💻 Coding Level", coding_full)
                    else:
                        st.metric("💻 Coding Level", "N/A")

                # Subject-wise performance
                st.subheader("📚 Subject-wise Performance")

                # Get subject columns
                exclude_cols = ['SR.No', 'Roll No', 'Name', 'Academic_Performance_%', 'Previous_Performance_Analysis',
                               'Practical_%', 'Coding_Expertise', 'Performance_Analysis', 'Category']

                subject_cols = []
                for col in student_data.keys():
                    if col not in exclude_cols and pd.notna(student_data[col]):
                        try:
                            # Check if it's a numeric value and greater than 0
                            val = float(student_data[col])
                            if val > 0:
                                subject_cols.append(col)
                        except (ValueError, TypeError):
                            continue

                if subject_cols:
                    # Subject performance table only (graph removed as requested)
                    subject_entries = []
                    for col in subject_cols:
                        clean_name = col.replace('_', ' ').title()
                        subject_entries.append({
                            'Subject': clean_name,
                            'Score': float(student_data[col])
                        })

                    subject_df = pd.DataFrame(subject_entries).sort_values('Score', ascending=False)
                    st.dataframe(subject_df, use_container_width=True)
                else:
                    st.info("No subject-wise performance data available for this student.")

            else:
                st.error("❌ Student not found. Please check the search query.")

        elif search_query and not search_button:
            st.info("👆 Click the Search button to find the student.")

    else:
        st.warning("📤 Please upload and process an Excel file first.")

# Subject analysis page
elif page == "📊 Subjects":
    if st.session_state.df_full is not None:
        df_full = st.session_state.df_full
        subjects = get_subject_list(df_full)

        st.header("📊 Subject-wise Analysis")

        if subjects:
            selected_subject = st.selectbox("📚 Select Subject", subjects)

            if selected_subject:
                # Get all columns for the selected subject
                subject_cols = []
                for col in df_full.columns:
                    # More flexible subject matching
                    col_upper = col.upper()
                    subject_upper = selected_subject.upper()

                    # Check if column starts with subject name or contains it
                    if (col_upper.startswith(subject_upper) or
                        subject_upper in col_upper):
                        # Make sure it's actually a subject column, not metadata
                        exclude_words = ['ACADEMIC', 'PERFORMANCE', 'CODING', 'EXPERTISE', 'CATEGORY']
                        if not any(word in col_upper for word in exclude_words):
                            subject_cols.append(col)

                if subject_cols:
                    st.subheader(f"📈 Analysis for {selected_subject}")

                    # Calculate subject statistics using marks (MSE + ESE)
                    subject_marks = get_subject_marks(df_full, selected_subject)
                    
                    if subject_marks:
                        # Create subject data with marks
                        subject_data = df_full[['Name', 'SR.No', 'Category']].copy()
                        subject_data['Subject_Marks'] = subject_marks
                        
                        # Get summary statistics
                        marks_summary = get_subject_marks_summary(df_full, selected_subject)
                        
                        # Display summary metrics
                        col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
                        
                        with col_summary1:
                            st.metric("📊 Average Marks", f"{marks_summary['average_marks']:.1f}")
                        
                        with col_summary2:
                            st.metric("📈 Max Marks", f"{marks_summary['max_marks']:.1f}")
                        
                        with col_summary3:
                            st.metric("📉 Min Marks", f"{marks_summary['min_marks']:.1f}")
                        
                        with col_summary4:
                            st.metric("📊 Std Deviation", f"{marks_summary['std_marks']:.1f}")

                        # Top and bottom performers in this subject
                        col1, col2 = st.columns(2)

                        with col1:
                            st.subheader(f"🏆 Top Performers in {selected_subject}")
                            top_subject = subject_data.nlargest(10, 'Subject_Marks')[['SR.No', 'Name', 'Subject_Marks']]
                            top_subject['Subject_Marks'] = top_subject['Subject_Marks'].round(1)
                            # Add ranking
                            top_subject['Rank'] = range(1, len(top_subject) + 1)
                            top_subject = top_subject[['Rank', 'Name', 'Subject_Marks']]
                            st.dataframe(top_subject, use_container_width=True, hide_index=True)

                        with col2:
                            st.subheader(f"⚠️ Need Improvement in {selected_subject}")
                            bottom_subject = subject_data.nsmallest(10, 'Subject_Marks')[['SR.No', 'Name', 'Subject_Marks']]
                            bottom_subject['Subject_Marks'] = bottom_subject['Subject_Marks'].round(1)
                            # Add ranking
                            bottom_subject['Rank'] = range(1, len(bottom_subject) + 1)
                            bottom_subject = bottom_subject[['Rank', 'Name', 'Subject_Marks']]
                            st.dataframe(bottom_subject, use_container_width=True, hide_index=True)
                    else:
                        st.warning(f"No MSE or ESE data found for {selected_subject}")
                else:
                    st.warning(f"No assessment data found for {selected_subject}")
        else:
            st.warning("No subjects found in the data.")

    else:
        st.warning("📤 Please upload and process an Excel file first.")

# Performance insights page
elif page == "🎯 Insights":
    if st.session_state.df_full is not None:
        df_full = st.session_state.df_full
        df_suggestions = st.session_state.df_suggestions

        st.header("🎯 Performance Insights & Recommendations")

        # Overall statistics (REMOVED academic percentage as requested)
        st.subheader("📊 Overall Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            total_students = len(df_full)
            st.metric("👥 Total Students", total_students)

        with col2:
            subjects_count = len(get_subject_list(df_full))
            st.metric("📚 Total Subjects", subjects_count)

        with col3:
            if 'Practical_%' in df_full.columns:
                avg_practical = df_full['Practical_%'].mean()
                if pd.notna(avg_practical):
                    st.metric("💻 Avg Practical %", f"{avg_practical:.2f}%")
                else:
                    st.metric("💻 Avg Practical %", "N/A")
            else:
                st.metric("💻 Avg Practical %", "N/A")

        # Category analysis
        st.subheader("📈 Category-wise Analysis")

        category_stats = df_full['Category'].value_counts() if 'Category' in df_full.columns else pd.Series()

        col5, col6 = st.columns(2)

        with col5:
            # Category distribution with recommendations
            fig_donut = px.pie(
                values=category_stats.values,
                names=category_stats.index,
                title="🎯 Student Distribution by Performance Category",
                hole=0.4,
                color_discrete_map={
                    'Bright': '#28a745',
                    'Average': '#ffc107',
                    'Weak': '#dc3545',
                    'Unknown': '#6c757d'
                }
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with col6:
            st.markdown("### 📋 Category Insights")

            for category, count in category_stats.items():
                percentage = (count / total_students) * 100

                if category == 'Bright':
                    st.success(f"🌟 **Bright Learners**: {count} ({percentage:.1f}%)")
                    st.write("💡 Continue challenging these students with advanced topics")

                elif category == 'Average':
                    st.info(f"📊 **Average Learners**: {count} ({percentage:.1f}%)")
                    st.write("🎯 Focus on targeted improvement strategies")

                elif category == 'Weak':
                    st.warning(f"⚠️ **Weak Learners**: {count} ({percentage:.1f}%)")
                    st.write("🆘 Require immediate attention and support")

        # Subject difficulty analysis
        subjects = get_subject_list(df_full)
        if subjects:
            st.subheader("📚 Subject Difficulty Analysis")

            subject_difficulty = []
            for subject in subjects:
                subject_cols = []
                for col in df_full.columns:
                    col_upper = col.upper()
                    subject_upper = subject.upper()

                    if (col_upper.startswith(subject_upper) or subject_upper in col_upper):
                        exclude_words = ['ACADEMIC', 'PERFORMANCE', 'CODING', 'EXPERTISE', 'CATEGORY']
                        if not any(word in col_upper for word in exclude_words):
                            if df_full[col].dtype in ['int64', 'float64']:
                                subject_cols.append(col)

                # Calculate marks for this subject (MSE + ESE only)
                subject_marks = get_subject_marks(df_full, subject)
                
                if subject_marks:
                    avg_marks = np.mean(subject_marks)
                    # Assuming max possible marks for MSE+ESE is 85 (25+60)
                    max_possible_marks = 85
                    fail_rate = (np.array(subject_marks) < (max_possible_marks * 0.4)).sum() / len(subject_marks) * 100

                    difficulty_level = "Easy" if avg_marks >= 60 else "Moderate" if avg_marks >= 40 else "Difficult"

                    subject_difficulty.append({
                        'Subject': subject,
                        'Avg_Marks': round(avg_marks, 2),
                        'Fail_Rate': round(fail_rate, 1),
                        'Difficulty': difficulty_level
                    })

            if subject_difficulty:
                difficulty_df = pd.DataFrame(subject_difficulty).sort_values('Avg_Marks')

                # Difficulty visualization
                fig_difficulty = px.bar(
                    difficulty_df,
                    x='Subject',
                    y='Avg_Marks',
                    color='Difficulty',
                    title="📊 Subject Difficulty Analysis (by Marks - MSE + ESE)",
                    color_discrete_map={
                        'Easy': '#28a745',
                        'Moderate': '#ffc107',
                        'Difficult': '#dc3545'
                    }
                )
                fig_difficulty.update_layout(
                    xaxis_tickangle=-45,
                    yaxis_title="Average Marks (MSE + ESE)"
                )
                st.plotly_chart(fig_difficulty, use_container_width=True)

                st.dataframe(difficulty_df, use_container_width=True)
            else:
                st.warning("No subject difficulty data available.")

        # Actionable Recommendations
        st.subheader("💡 Actionable Recommendations")

        recommendations = []

        # Based on weak learners
        weak_count = category_stats.get('Weak', 0)
        if weak_count > total_students * 0.3:
            recommendations.append({
                'Priority': 'High',
                'Area': 'Academic Support',
                'Recommendation': f'{weak_count} students ({weak_count/total_students*100:.1f}%) need immediate academic intervention',
                'Action': 'Implement remedial classes and peer tutoring programs'
            })

        # Based on subject difficulty
        if subjects and subject_difficulty:
            difficult_subjects = [s for s in subject_difficulty if s['Difficulty'] == 'Difficult']
            if difficult_subjects:
                worst_subject = min(difficult_subjects, key=lambda x: x['Avg_Marks'])
                recommendations.append({
                    'Priority': 'High',
                    'Area': 'Curriculum',
                    'Recommendation': f"{worst_subject['Subject']} shows lowest performance (avg: {worst_subject['Avg_Marks']:.1f} marks)",
                    'Action': 'Review teaching methodology and provide additional resources'
                })

        # Based on pass rate
        if 'Academic_Performance_%' in df_full.columns:
            pass_count = len(df_full[df_full['Academic_Performance_%'] >= 40])
            pass_rate = (pass_count / len(df_full)) * 100 if len(df_full) > 0 else 0
            avg_academic = df_full['Academic_Performance_%'].mean()

            if pass_rate < 80:
                recommendations.append({
                    'Priority': 'High',
                    'Area': 'Pass Rate',
                    'Recommendation': f'Pass rate is {pass_rate:.1f}% - below acceptable threshold',
                    'Action': 'Implement comprehensive support system and early warning mechanisms'
                })
        else:
            pass_rate = 0
            avg_academic = None

        # Display recommendations
        if recommendations:
            for i, rec in enumerate(recommendations):
                priority_color = 'error' if rec['Priority'] == 'High' else 'warning' if rec['Priority'] == 'Medium' else 'info'

                with st.container():
                    st.markdown(f"### {i+1}. {rec['Area']} - {rec['Priority']} Priority")
                    if rec['Priority'] == 'High':
                        st.error(f"🚨 **Issue**: {rec['Recommendation']}")
                        st.error(f"🎯 **Action**: {rec['Action']}")
                    elif rec['Priority'] == 'Medium':
                        st.warning(f"⚠️ **Issue**: {rec['Recommendation']}")
                        st.warning(f"🎯 **Action**: {rec['Action']}")
                    else:
                        st.info(f"ℹ️ **Issue**: {rec['Recommendation']}")
                        st.info(f"🎯 **Action**: {rec['Action']}")
                    st.markdown("---")
        else:
            st.success("🎉 Great! No critical issues identified. Keep up the good work!")

        # Export comprehensive report
        st.subheader("📄 Export Comprehensive Report")

        if st.button("📊 Generate Detailed Report", type="primary"):
            # Create comprehensive report
            report_data = {
                'Overall_Statistics': {
                    'Total_Students': total_students,
                    'Pass_Rate': float(pass_rate) if 'Academic_Performance_%' in df_full.columns else None,
                    'Average_Academic_Performance': float(avg_academic) if 'Academic_Performance_%' in df_full.columns and pd.notna(avg_academic) else None
                },
                'Category_Distribution': category_stats.to_dict(),
                'Subject_Analysis': subject_difficulty if subjects and subject_difficulty else [],
                'Recommendations': recommendations
            }

            # Convert to JSON for download
            import json
            report_json = json.dumps(report_data, indent=2, default=str)

            st.download_button(
                "📥 Download Detailed Report (JSON)",
                report_json,
                "comprehensive_analysis_report.json",
                "application/json"
            )

            st.success("✅ Report generated successfully!")

    else:
        st.warning("📤 Please upload and process an Excel file first.")



# Reports & Export page
elif page == "📋 Reports":
    if st.session_state.df_full is not None:
        df_full = st.session_state.df_full
        df_suggestions = st.session_state.df_suggestions
        
        st.header("📋 Reports & Export Center")
        
        # Report type selection
        report_type = st.selectbox(
            "Select Report Type",
            [
                "📊 Comprehensive Analysis Report",
                "👥 Individual Student Reports", 
                "📚 Subject-wise Reports",
                "🎯 Performance Summary Report",
                "📈 Trend Analysis Report"
            ]
        )
        
        if report_type == "📊 Comprehensive Analysis Report":
            st.subheader("📊 Comprehensive Analysis Report")
            
            # Generate comprehensive report
            if st.button("🚀 Generate Comprehensive Report", type="primary"):
                with st.spinner("Generating comprehensive report..."):
                    # Create report data
                    report_data = {
                        'report_metadata': {
                            'generated_at': datetime.now().isoformat(),
                            'total_students': len(df_full),
                            'total_subjects': len(get_subject_list(df_full)),
                            'report_type': 'Comprehensive Analysis'
                        },
                        'summary_statistics': {},
                        'category_analysis': {},
                        'subject_analysis': {},
                        'recommendations': []
                    }
                    
                    # Summary statistics
                    if 'Academic_Performance_%' in df_full.columns:
                        avg_academic = df_full['Academic_Performance_%'].mean()
                        report_data['summary_statistics'] = {
                            'average_academic_performance': float(avg_academic),
                            'median_academic_performance': float(df_full['Academic_Performance_%'].median()),
                            'std_academic_performance': float(df_full['Academic_Performance_%'].std()),
                            'min_academic_performance': float(df_full['Academic_Performance_%'].min()),
                            'max_academic_performance': float(df_full['Academic_Performance_%'].max())
                        }
                    
                    # Category analysis
                    if 'Category' in df_suggestions.columns:
                        category_counts = df_suggestions['Category'].value_counts()
                        report_data['category_analysis'] = category_counts.to_dict()
                    
                    # Subject analysis
                    subjects = get_subject_list(df_full)
                    subject_analysis = {}
                    for subject in subjects:
                        subject_cols = [col for col in df_full.columns if subject.upper() in col.upper()]
                        if subject_cols:
                            subject_data = df_full[subject_cols].mean(axis=1)
                            subject_analysis[subject] = {
                                'average_performance': float(subject_data.mean()),
                                'std_performance': float(subject_data.std()),
                                'total_students': len(subject_data)
                            }
                    report_data['subject_analysis'] = subject_analysis
                    
                    # Generate recommendations
                    if 'Academic_Performance_%' in df_full.columns:
                        weak_students = len(df_full[df_full['Academic_Performance_%'] < 60])
                        if weak_students > 0:
                            report_data['recommendations'].append({
                                'priority': 'High',
                                'area': 'Academic Support',
                                'description': f'{weak_students} students need additional academic support',
                                'action': 'Implement remedial classes and peer tutoring'
                            })
                    
                    # Display report
                    st.success("✅ Comprehensive report generated successfully!")
                    
                    # Show report preview
                    with st.expander("📋 Report Preview", expanded=True):
                        st.json(report_data)
                    
                    # Download options
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # JSON download
                        json_data = json.dumps(report_data, indent=2, default=str)
                        st.download_button(
                            "📥 Download JSON Report",
                            json_data,
                            f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            "application/json"
                        )
                    
                    with col2:
                        # CSV download
                        csv_data = df_full.to_csv(index=False)
                        st.download_button(
                            "📊 Download Full Data CSV",
                            csv_data,
                            f"full_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv"
                        )
                    
                    with col3:
                        # Summary CSV download
                        summary_csv = df_suggestions.to_csv(index=False)
                        st.download_button(
                            "📋 Download Summary CSV",
                            summary_csv,
                            f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv"
                        )
        
        elif report_type == "👥 Individual Student Reports":
            st.subheader("👥 Individual Student Reports")
            
            # Student selection
            if 'Name' in df_full.columns:
                selected_student = st.selectbox("Select Student", df_full['Name'].tolist())
                
                if selected_student:
                    student_data = df_full[df_full['Name'] == selected_student].iloc[0]
                    
                    # Generate individual report
                    if st.button("📄 Generate Student Report", type="primary"):
                        with st.spinner("Generating student report..."):
                            # Create student report
                            student_report = {
                                'student_info': {
                                    'name': student_data.get('Name', 'N/A'),
                                    'roll_no': student_data.get('Roll No', 'N/A'),
                                    'sr_no': student_data.get('SR.No', 'N/A')
                                },
                                'performance_metrics': {
                                    'academic_performance': float(student_data.get('Academic_Performance_%', 0)),
                                    'practical_performance': float(student_data.get('Practical_%', 0)),
                                    'coding_expertise': student_data.get('Coding_Expertise', 'N/A'),
                                    'category': student_data.get('Category', 'N/A')
                                },
                                'subject_wise_performance': {},
                                'recommendations': []
                            }
                            
                            # Subject-wise performance
                            subjects = get_subject_list(df_full)
                            for subject in subjects:
                                subject_cols = [col for col in df_full.columns if subject.upper() in col.upper()]
                                if subject_cols:
                                    subject_scores = []
                                    for col in subject_cols:
                                        score = student_data.get(col, 0)
                                        if pd.notna(score) and score > 0:
                                            subject_scores.append(float(score))
                                    
                                    if subject_scores:
                                        student_report['subject_wise_performance'][subject] = {
                                            'average_score': float(np.mean(subject_scores)),
                                            'total_scores': subject_scores,
                                            'max_possible': len(subject_scores) * 100  # Assuming max 100 per assessment
                                        }
                            
                            # Generate recommendations
                            academic_perf = student_report['performance_metrics']['academic_performance']
                            if academic_perf < 60:
                                student_report['recommendations'].append({
                                    'priority': 'High',
                                    'area': 'Academic Improvement',
                                    'description': 'Student needs immediate academic support',
                                    'action': 'Schedule regular tutoring sessions'
                                })
                            elif academic_perf < 80:
                                student_report['recommendations'].append({
                                    'priority': 'Medium',
                                    'area': 'Performance Enhancement',
                                    'description': 'Student can improve with targeted support',
                                    'action': 'Provide additional practice materials'
                                })
                            
                            # Display report
                            st.success(f"✅ Report generated for {selected_student}")
                            
                            # Show report preview
                            with st.expander("📋 Student Report Preview", expanded=True):
                                st.json(student_report)
                            
                            # Download student report
                            json_data = json.dumps(student_report, indent=2, default=str)
                            st.download_button(
                                "📥 Download Student Report",
                                json_data,
                                f"student_report_{selected_student.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                "application/json"
                            )
        
        # Bulk export options
        st.markdown("---")
        st.subheader("📦 Bulk Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export All Data", help="Export complete dataset"):
                csv_data = df_full.to_csv(index=False)
                st.download_button(
                    "📥 Download Complete Dataset",
                    csv_data,
                    f"complete_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
        
        with col2:
            if st.button("📋 Export Summary", help="Export summary data"):
                summary_data = df_suggestions.to_csv(index=False)
                st.download_button(
                    "📥 Download Summary Data",
                    summary_data,
                    f"summary_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
        
        with col3:
            if st.button("📈 Export Analytics", help="Export analytics data"):
                # Create analytics summary
                analytics_data = {
                    'total_students': len(df_full),
                    'total_subjects': len(get_subject_list(df_full)),
                    'category_distribution': df_suggestions['Category'].value_counts().to_dict() if 'Category' in df_suggestions.columns else {},
                    'performance_statistics': df_full.describe().to_dict() if len(df_full) > 0 else {}
                }
                
                analytics_json = json.dumps(analytics_data, indent=2, default=str)
                st.download_button(
                    "📥 Download Analytics Data",
                    analytics_json,
                    f"analytics_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )
    
    else:
        st.warning("📤 Please upload and process an Excel file first.")


# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🎓 GradeGraph - Student Performance Analyzer</p>
        <p>Built by Kshitij and Shweta for COMPUTER DEPARTMENT, JSPM's RSCOE.</p>
    </div>
    """,
    unsafe_allow_html=True
)