## Setup
### Local Dev
#### MacOs & Linux Install UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
#### Install Python 
```bash
uv python install 3.12 3.13
```

## Matching Pipeline Overview

The matching pipeline is a sophisticated system designed to match users based on various criteria and intents. It consists of two main components:

### 1. Core Matching Logic (`matching.py`)

The core matching logic handles the main matching process through several key functions:

#### `process_matching_request`
- Entry point for matching requests
- Handles different intent types (mentoring, projects, referrals, etc.)
- Validates form content and user data
- Applies model settings and user limits
- Manages error handling and result logging

#### `process_text_to_form_content`
- Converts text input into structured form content
- Handles different intent types and their specific requirements
- Validates and normalizes form data
- Supports both structured and unstructured input

#### `parse_text_for_matching`
- Processes text input for matching purposes
- Extracts relevant information based on intent type
- Handles different form types and their specific requirements
- Supports both structured and unstructured input

### 2. Heuristic Predictor (`heuristic_predictor.py`)

The heuristic predictor implements a rule-based scoring system with the following components:

#### Core Rules
1. **Location Matching**
   - Considers city, country, and region matches
   - Applies different weights for different match levels
   - Handles multiple location sources (profile, LinkedIn)

2. **Interests Matching**
   - Uses Jaccard similarity for interest overlap
   - Considers both direct and category-based matches
   - Aggregates interests from multiple sources

3. **Expertise Matching**
   - Matches expertise areas with weighted scoring
   - Considers technical vs non-technical expertise
   - Handles hierarchical expertise categories

4. **Grade Matching**
   - Implements hierarchical grade comparison
   - Considers seniority levels and experience
   - Applies different weights based on role requirements

5. **Skills Matching**
   - Uses Jaccard similarity for skill overlap
   - Considers both technical and soft skills
   - Aggregates skills from multiple sources

6. **Professional Background**
   - Evaluates work experience quality
   - Considers company size and type
   - Handles position titles and responsibilities

7. **Language Matching**
   - Matches language requirements
   - Considers proficiency levels
   - Handles multiple language sources

#### Intent-Specific Rules

The predictor includes specialized rules for different intent types:

1. **Mock Interviews**
   - Matches interview types and languages
   - Considers required grade levels
   - Evaluates technical expertise

2. **Mentoring**
   - Matches mentor/mentee requirements
   - Considers specialization areas
   - Evaluates experience levels

3. **Projects**
   - Matches project requirements
   - Considers role-specific needs
   - Evaluates technical skills

4. **Referrals**
   - Matches company requirements
   - Considers English level requirements
   - Evaluates professional background

### Scoring System

The matching pipeline uses a sophisticated scoring system:

1. **Base Scores**
   - Each rule contributes to the final score
   - Rules are weighted based on importance
   - Minimum thresholds ensure quality matches

2. **Score Components**
   - Direct matches receive highest scores
   - Partial matches receive proportional scores
   - Category matches receive intermediate scores

3. **Score Aggregation**
   - Weighted combination of rule scores
   - Normalization to 0-1 range
   - Minimum score thresholds

### Data Processing

The pipeline includes robust data processing:

1. **Data Aggregation**
   - Combines data from multiple sources
   - Normalizes different data formats
   - Handles missing or incomplete data

2. **Data Validation**
   - Validates input data
   - Handles edge cases
   - Provides fallback values

3. **Error Handling**
   - Graceful handling of errors
   - Detailed error logging
   - Fallback mechanisms

### Performance Considerations

The pipeline is optimized for performance:

1. **Efficient Processing**
   - Batch processing of matches
   - Optimized data structures
   - Caching mechanisms

2. **Scalability**
   - Handles large datasets
   - Supports parallel processing
   - Memory-efficient operations

3. **Monitoring**
   - Detailed logging
   - Performance metrics
   - Error tracking

## Step-by-Step Pipeline Flow

This section provides a detailed walkthrough of how the matching pipeline processes requests, with examples for different scenarios.

### Basic Flow

1. **Request Initiation**
   ```python
   # Example matching request
   request = {
       "intent_type": "mentoring_mentor",
       "form_content": {
           "required_grade": ["senior"],
           "specialization": ["development__backend"],
           "help_request": {
               "request": ["process_and_teams_management"],
               "custom_request": "Need help with team scaling"
           }
       }
   }
   ```

2. **Form Content Processing**
   ```python
   # The pipeline validates and normalizes the form content
   normalized_content = {
       "required_grade": [EFormMentoringGrade.senior],
       "specialization": [EFormSpecialization.development__backend],
       "help_request": {
           "request": [EFormMentoringHelpRequest.process_and_teams_management],
           "custom_request": "Need help with team scaling"
       }
   }
   ```

3. **Candidate Pool Selection**
   ```python
   # Example candidate features
   candidates = [
       {
           "id": "user1",
           "grade": EGrade.senior,
           "expertise_area": ["development", "team_management"],
           "location": "san_francisco_usa_north_america"
       },
       {
           "id": "user2",
           "grade": EGrade.middle,
           "expertise_area": ["development"],
           "location": "london_uk_europe"
       }
   ]
   ```

4. **Rule Application**
   Each rule is applied with specific weights:

   ```python
   # Example rule weights
   rules = [
       {
           "name": "grade_match",
           "type": "grade",
           "weight": 0.3,
           "params": {"base_score": 0.5}
       },
       {
           "name": "expertise_match",
           "type": "expertise",
           "weight": 0.4,
           "params": {"technical_bonus": 0.2}
       },
       {
           "name": "location_match",
           "type": "location",
           "weight": 0.3,
           "params": {"city_penalty": 0.2}
       }
   ]
   ```

5. **Score Calculation**
   ```python
   # Example score calculation
   user1_scores = {
       "grade_match": 1.0,      # Exact senior match
       "expertise_match": 0.9,   # Strong expertise match
       "location_match": 0.7     # Good location match
   }
   user1_final_score = 0.87     # Weighted average

   user2_scores = {
       "grade_match": 0.6,      # Lower grade
       "expertise_match": 0.7,   # Partial expertise match
       "location_match": 0.7     # Good location match
   }
   user2_final_score = 0.67     # Weighted average
   ```

### Intent-Specific Examples

#### 1. Mock Interview Matching

```python
# Request
mock_interview_request = {
    "intent_type": "mock_interview",
    "form_content": {
        "interview_type": ["technical"],
        "language": {"langs": ["english"]},
        "required_grade": ["senior"]
    }
}

# Candidate Scoring Example
candidate_features = {
    "grade": "senior",
    "linkedin_profile": {
        "languages": ["English", "Spanish"],
        "work_experience": [
            {
                "title": "Senior Software Engineer",
                "duration_years": 5
            }
        ]
    }
}

# Score Components
scores = {
    "grade_match": 1.0,        # Exact grade match
    "language_match": 1.0,     # Required language match
    "experience_match": 0.9    # Strong experience in technical role
}
final_score = 0.95            # High overall match
```

#### 2. Mentoring Match

```python
# Request
mentoring_request = {
    "intent_type": "mentoring_mentor",
    "form_content": {
        "required_grade": ["senior"],
        "specialization": ["development__backend"],
        "help_request": {
            "request": ["career_growth"],
            "custom_request": "Cloud architecture guidance"
        }
    }
}

# Candidate Scoring Example
mentor_features = {
    "grade": "lead",
    "expertise_area": ["backend", "cloud"],
    "specialisation": ["development__backend", "development__cloud"],
    "linkedin_profile": {
        "current_position_title": "Lead Cloud Architect",
        "work_experience": [
            {"title": "Senior Backend Engineer", "duration_years": 4},
            {"title": "Lead Cloud Architect", "duration_years": 3}
        ]
    }
}

# Score Components
scores = {
    "grade_match": 1.0,            # Exceeds required grade
    "specialization_match": 1.0,   # Exact specialization match
    "expertise_match": 0.9,        # Strong expertise alignment
    "experience_match": 0.95       # Relevant experience
}
final_score = 0.96                 # Excellent overall match
```

#### 3. Project Collaboration

```python
# Request
project_request = {
    "intent_type": "projects_find_contributor",
    "form_content": {
        "project_state": "mvp",
        "skills": ["python", "fastapi", "postgresql"],
        "specialization": ["development__backend"]
    }
}

# Candidate Scoring Example
contributor_features = {
    "grade": "middle",
    "skills": ["python", "django", "fastapi", "postgresql"],
    "specialisation": ["development__backend"],
    "linkedin_profile": {
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "work_experience": [
            {"title": "Backend Developer", "duration_years": 3}
        ]
    }
}

# Score Components
scores = {
    "skills_match": 0.9,          # Strong skills overlap
    "specialization_match": 1.0,  # Exact specialization match
    "experience_match": 0.8,      # Relevant experience
    "grade_match": 0.7           # Acceptable grade for MVP stage
}
final_score = 0.85               # Good overall match
```

### Score Interpretation

The final scores are interpreted as follows:

- **0.9 - 1.0**: Excellent match
  - Example: Senior mentor with exact expertise match
  - Example: Technical interviewer with perfect language and grade match

- **0.75 - 0.89**: Strong match
  - Example: Project contributor with most required skills
  - Example: Mentor with related but not exact specialization

- **0.6 - 0.74**: Good match
  - Example: Mentor with lower grade but strong expertise
  - Example: Contributor with partial skill match but strong experience

- **Below 0.6**: Weak match
  - Example: Significant grade mismatch
  - Example: Missing critical required skills

### Error Handling Examples

```python
# Example: Missing Required Data
try:
    if not request.form_content.get("required_grade"):
        raise ValueError("Required grade must be specified for mentoring requests")
except ValueError as e:
    log.error(f"Validation error: {str(e)}")
    return {"error": "Invalid request format", "details": str(e)}

# Example: Invalid Grade Level
try:
    if grade not in [g.value for g in EGrade]:
        raise ValueError(f"Invalid grade level: {grade}")
except ValueError as e:
    log.error(f"Grade validation error: {str(e)}")
    return {"error": "Invalid grade specified", "details": str(e)}
```
