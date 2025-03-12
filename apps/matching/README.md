# Matching

## Setup
### Local Dev
#### MacOs & Linux Install UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
#### Setup venv
```bash
uv sync
```

#### Run tests
```bash
uv run pytest
```

## Docker
### Build 
```bash
docker build -t matching .
```

### Run
```bash
docker run -d -p 8080:8080 matching
```

### Compose
```bash
docker compose up -d --build
```

## Intent Type Processing Documentation

The matching service uses a heuristic-based approach to match users based on various intent types. Each intent type has specific matching logic tailored to its requirements. Below is a detailed documentation of how each intent type is processed.

### 1. Mock Interview Matching

**Purpose**: Match users for mock interview sessions.

**Processing Logic**:
- **Grade Matching (40%)**: Prioritizes users with the required grade level
- **Language Matching (40%)**: Matches based on required interview languages
- **Expertise Matching (40%)**: Matches interviewer expertise with requested interview type
- **Senior Experience Bonus (20%)**: Additional points for senior-level experience

**Key Factors**:
- Interview type (technical, behavioral, role-playing)
- Required languages
- Required grade level
- Senior experience

### 2. Social Circle Expansion (Connects)

**Purpose**: Connect users for social networking.

**Processing Logic**:
- **Base Score (50%)**: Initial matching score
- **Topic Matching (30%)**: Shared expertise areas and topics
- **Custom Topics (20%)**: Additional matching for custom topics
- **Location (20%)**: Priority for same city/country in offline meetings
- **Network Quality (20%)**: LinkedIn profile completeness

**Key Factors**:
- Meeting format (online/offline)
- Topics of interest
- Custom topics
- Location (for offline meetings)
- Network quality

### 3. Professional Networking (Connects)

**Purpose**: Connect users for professional networking.

**Processing Logic**:
- **Base Score (60%)**: Higher base score for professional connections
- **Topic Matching**: Expertise areas matching
- **Expertise Scoring**: Emphasis on senior/lead positions
- **Position Matching**: Job titles and seniority levels

**Key Factors**:
- Professional topics (development, analytics)
- Expertise requirements
- Grade and position seniority
- Specialization matching

### 4. Mentoring - Mentor Matching

**Purpose**: Match mentees with potential mentors.

**Processing Logic**:
- **Grade Matching**: Required grade level or higher
- **Specialization Matching**: Mentor expertise areas
- **Help Request Processing**:
  - Relocation adaptation: Target country matching
  - Process/team management: Leadership experience priority
  - Custom requests: Expertise matching
- **Professional Background (60%)**: Work experience evaluation

**Key Factors**:
- Grade level requirements
- Specialization areas
- Help request type
- Location (for relocation)
- Leadership experience

### 5. Mentoring - Mentee Matching

**Purpose**: Match mentors with potential mentees.

**Processing Logic**:
- **Specialization Matching**: Hierarchical specialization matching
- **Grade Matching**: Higher grade level prioritization
- **Help Request Processing**: Location and experience matching
- **Professional Background (60%)**: Experience evaluation

**Key Factors**:
- Mentor specialization
- Mentee grade level
- Help request type
- Location requirements
- Multi-location experience

### 6. Projects - Contributor/Cofounder Matching

**Purpose**: Match project owners with contributors or cofounders.

**Processing Logic**:
- **Base Score (60%)**: Higher initial score
- **Skills Matching**: LinkedIn skill evaluation
- **Role-Specific Scoring**:
  - Cofounders: Broad expertise focus
  - Contributors: Specific skills focus
- **Project State Consideration**: Experience requirements based on project stage
- **Expertise Bonus (20%)**: Project specialization matching

**Key Factors**:
- Project state (idea, prototype, MVP, scaling)
- Required skills
- Project specialization
- Role type (contributor/cofounder)
- Grade level

### 7. Referrals Recommendation

**Purpose**: Match users for job referrals.

**Processing Logic**:
- **English Level Matching**: Language proficiency evaluation
- **Company Type Matching**: Company experience matching
- **Location Consideration**: Local community prioritization
- **Expert Type Consideration**: Senior position focus
- **Professional Background (60%)**: Work experience evaluation

**Key Factors**:
- English level requirements
- Company type
- Local community requirements
- Expert type requirements
- Location preferences

### Common Processing Elements

All intent types share these common processing rules:

1. **Network Quality**
   - LinkedIn profile completeness
   - Follower count
   - Work experience quality

2. **Location Matching**
   - City priority
   - Country fallback
   - Region consideration

3. **Professional Background**
   - Employment status
   - Position similarity
   - Industry matching

4. **Grade Matching**
   - Seniority level weighting
   - Context-specific grade requirements

5. **Expertise Matching**
   - Technical area focus
   - Core skill weighting

### Scoring Mechanism

Final match scores are calculated using:
- Individual rule scores (0-1 range)
- Intent-specific rule weights
- Weighted average combination
- Score normalization to 0-1 range