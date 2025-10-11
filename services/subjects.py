import pandas as pd


def get_subject_list(df):
    exclude_cols = ['SR.No', 'Roll No', 'Name', 'Academic_Performance_%', 'Previous_Performance_Analysis',
                   'Practical_%', 'Coding_Expertise', 'Performance_Analysis', 'Category']

    subject_cols = [col for col in df.columns if col not in exclude_cols]

    subjects = set()
    for col in subject_cols:
        col_str = str(col)
        for assessment in ['ISE', 'MSE', 'ESE', 'PRACTICAL', 'TW', 'PR']:
            if assessment in col_str.upper():
                parts = col_str.upper().split(assessment)
                if len(parts) > 0:
                    subject_name = parts[0].strip()
                    if subject_name:
                        subject_name = subject_name.replace('_', ' ').title()
                        subjects.add(subject_name)
                break

    subject_list = sorted(list(subjects))
    print(f"📚 Extracted subjects: {subject_list}")
    return subject_list


def get_subject_exam_types(df, subject_name):
    exam_types = set()
    for col in df.columns:
        col_upper = str(col).upper()
        subject_upper = subject_name.upper()
        if subject_upper in col_upper:
            if 'ESE' in col_upper:
                exam_types.add('ESE')
            elif 'ISE' in col_upper:
                exam_types.add('ISE')
            elif 'MSE' in col_upper:
                exam_types.add('MSE')
            elif 'PRACTICAL' in col_upper or 'PR' in col_upper:
                exam_types.add('PRACTICAL')
            elif 'TW' in col_upper:
                exam_types.add('TW')
    return sorted(list(exam_types))


def get_subject_marks(df, subject_name):
    """
    Calculate total marks (MSE + ESE) for a given subject
    Returns the sum of MSE and ESE marks for each student
    """
    subject_cols = []
    for col in df.columns:
        col_upper = str(col).upper()
        subject_upper = subject_name.upper()
        if subject_upper in col_upper:
            # Only include MSE and ESE columns
            if 'MSE' in col_upper or 'ESE' in col_upper:
                subject_cols.append(col)
    
    if not subject_cols:
        return None
    
    # Calculate total marks for each student
    marks_data = []
    for _, row in df.iterrows():
        total_marks = 0
        for col in subject_cols:
            try:
                marks = float(row[col]) if pd.notna(row[col]) else 0
                total_marks += marks
            except (ValueError, TypeError):
                continue
        marks_data.append(total_marks)
    
    return marks_data


def get_subject_marks_summary(df, subject_name):
    """
    Get summary statistics for subject marks (MSE + ESE)
    """
    marks_data = get_subject_marks(df, subject_name)
    if marks_data is None:
        return None
    
    import numpy as np
    return {
        'total_marks': marks_data,
        'average_marks': np.mean(marks_data),
        'max_marks': np.max(marks_data),
        'min_marks': np.min(marks_data),
        'std_marks': np.std(marks_data)
    }


