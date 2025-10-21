# Claude Political Language Generator Integration Plan

## Overview
Integration of Claude AI interface into the existing Flask precinct mapping application to generate political language with structured context, limited to subject and length parameters only.

## Prerequisites
- Existing Flask application with user authentication
- Anthropic API key
- Admin/County user access control already implemented

## Implementation Steps

### 1. Dependencies & Configuration

#### 1.1 Add Required Packages
```bash
uv add anthropic
uv add python-dotenv  # if not already present
```

#### 1.2 Environment Variables
Add to `.env` file or environment:
```env
ANTHROPIC_API_KEY=your_claude_api_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20241022  # or preferred model
```

#### 1.3 Update config.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Existing config...
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    CLAUDE_MODEL = os.environ.get('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
```

### 2. Backend Implementation

#### 2.1 Create Claude Service Module
Create `claude_service.py`:
```python
import anthropic
from flask import current_app
import logging

class ClaudeService:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generate_political_content(self, subject, length):
        """
        Generate political language with structured context
        
        Args:
            subject (str): Political topic/subject
            length (str): 'short' | 'medium' | 'long'
        
        Returns:
            dict: Generated content and metadata
        """
        # Implementation details...
```

#### 2.2 Add Forms (WTForms)
Create forms for the Claude interface:
```python
class PoliticalContentForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(min=3, max=200)])
    length = SelectField('Length', 
                        choices=[('short', 'Short (1-2 paragraphs)'),
                                ('medium', 'Medium (3-4 paragraphs)'), 
                                ('long', 'Long (5+ paragraphs)')],
                        validators=[DataRequired()])
    submit = SubmitField('Generate Content')
```

#### 2.3 Add Database Model (Optional)
Store generated content for audit/history:
```python
class GeneratedContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    length = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 3. Routes & Views

#### 3.1 Main Claude Interface Route
```python
@app.route('/claude-generator')
@login_required
@limiter.limit("10 per minute")  # Rate limiting
def claude_generator():
    """Main interface for Claude political content generation"""
    # Access control: admin/county users only
    # Render form template
```

#### 3.2 Content Generation Route
```python
@app.route('/generate-political-content', methods=['POST'])
@login_required
@limiter.limit("5 per minute")  # Stricter rate limiting
def generate_political_content():
    """Process form and generate content via Claude API"""
    # Validate form
    # Call Claude service
    # Return JSON response or render template
```

#### 3.3 Content History Route (Optional)
```python
@app.route('/claude-history')
@login_required
def claude_history():
    """View previously generated content"""
    # Query user's generated content
    # Paginate results
```

### 4. Frontend Templates

#### 4.1 Main Generator Page (`claude_generator.html`)
```html
<!-- Form interface with:
- Subject input field
- Length selection dropdown  
- Generate button
- Loading states
- Results display area
-->
```

#### 4.2 Update Navigation
Add links in:
- `base.html` navigation
- `dashboard.html` admin/county sections

#### 4.3 JavaScript Enhancements
```javascript
// AJAX form submission
// Loading indicators
// Real-time character counts
// Copy-to-clipboard functionality
```

### 5. Security & Access Control

#### 5.1 User Permissions
```python
def claude_access_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.is_admin or current_user.is_county):
            flash('Access denied. Claude generator is available to administrators and county users only.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
```

#### 5.2 Rate Limiting
- Per-user request limits
- API quota management
- Abuse prevention

#### 5.3 Content Validation
- Input sanitization
- Output filtering
- Inappropriate content detection

### 6. Claude Integration Details

#### 6.1 Prompt Engineering
```python
def create_political_prompt(subject, length):
    """
    Create structured prompt for political content generation
    
    Context limitations:
    - Subject: User-provided political topic
    - Length: Short/Medium/Long specification only
    - No additional context parameters allowed
    """
    system_prompt = """
    You are a professional political content writer specializing in balanced, 
    informative political communication. Generate content that is:
    - Factual and well-researched
    - Balanced in perspective
    - Appropriate for civic engagement
    - Professional in tone
    """
    
    user_prompt = f"""
    Generate political content about: {subject}
    Length requirement: {length}
    
    Please provide well-structured, informative content suitable for 
    civic engagement and political communication.
    """
```

#### 6.2 Response Processing
- Content formatting
- Error handling
- Token usage tracking

### 7. Configuration & Deployment

#### 7.1 Environment Setup
```bash
# Production environment variables
export ANTHROPIC_API_KEY="your_production_key"
export CLAUDE_MODEL="claude-3-5-sonnet-20241022"
export FLASK_ENV="production"
```

#### 7.2 Database Migration
```bash
# If using GeneratedContent model
flask db migrate -m "Add Claude generated content model"
flask db upgrade
```

### 8. Testing Strategy

#### 8.1 Unit Tests
```python
class TestClaudeService(unittest.TestCase):
    def test_generate_political_content(self):
        # Test API integration
        # Test input validation
        # Test error handling
```

#### 8.2 Integration Tests
- Form submission workflows
- Authentication/authorization
- Rate limiting behavior

#### 8.3 Security Testing
- Input injection attempts
- Access control bypasses
- API key exposure

### 9. Monitoring & Logging

#### 9.1 Usage Tracking
- API call counts
- User activity logs
- Cost monitoring

#### 9.2 Error Monitoring
- API failures
- Rate limit hits
- Content generation errors

### 10. Documentation

#### 10.1 User Guide
- How to use the Claude interface
- Subject guidelines
- Length specifications

#### 10.2 Admin Documentation
- API key management
- Usage monitoring
- Troubleshooting guide

## File Structure Changes

```
precinct/
├── claude_service.py          # New: Claude API integration
├── forms.py                   # New: WTForms for Claude interface
├── main.py                    # Modified: Add Claude routes
├── models.py                  # Modified: Add GeneratedContent model
├── config.py                  # Modified: Add Claude configuration
├── templates/
│   ├── claude_generator.html  # New: Main Claude interface
│   ├── claude_history.html    # New: Content history view
│   ├── base.html             # Modified: Add navigation
│   └── dashboard.html        # Modified: Add Claude links
├── static/
│   ├── css/
│   │   └── claude.css        # New: Claude-specific styles
│   └── js/
│       └── claude.js         # New: Claude interface JavaScript
└── requirements.txt          # Modified: Add anthropic dependency
```

## Estimated Implementation Time
- Backend development: 4-6 hours
- Frontend templates: 3-4 hours  
- Testing & debugging: 2-3 hours
- Documentation: 1-2 hours
- **Total: 10-15 hours**

## Considerations
- API costs and usage limits
- Content moderation requirements
- User training needs
- Backup/fallback mechanisms
- Compliance with political communication regulations