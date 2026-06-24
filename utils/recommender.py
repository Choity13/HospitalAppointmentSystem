def get_recommended_department(symptom_text):
    # Import inside function to avoid circular imports
    from extensions import db
    from models import SymptomsMap, Department

    # Step 1: Convert to lowercase and split into words
    symptom_words = symptom_text.strip().lower().split()
    
    if not symptom_words:
        return None

    # Step 2: Query all symptoms_map rows
    all_symptoms = SymptomsMap.query.all()

    # Step 3: Count matches per dept_id
    dept_counts = {}
    matched_keywords_per_dept = {}

    for symptom in all_symptoms:
        keyword = symptom.keyword.lower()
        
        for word in symptom_words:
            if word in keyword or keyword in word:
                dept_id = symptom.dept_id
                
                if dept_id not in dept_counts:
                    dept_counts[dept_id] = 0
                    matched_keywords_per_dept[dept_id] = []
                
                dept_counts[dept_id] += 1
                if keyword not in matched_keywords_per_dept[dept_id]:
                    matched_keywords_per_dept[dept_id].append(keyword)

    if not dept_counts:
        return None

    # Step 4: Find dept with highest count
    best_dept_id = max(dept_counts, key=dept_counts.get)

    # Step 5: Get department name
    best_dept = Department.query.get(best_dept_id)
    if not best_dept:
        return None

    return {
        'dept_id': best_dept.dept_id,
        'dept_name': best_dept.dept_name,
        'matched_keywords': matched_keywords_per_dept[best_dept_id]
    }
