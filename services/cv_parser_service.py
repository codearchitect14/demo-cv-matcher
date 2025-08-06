import PyPDF2
import docx
import re
import spacy
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import json
from dataclasses import dataclass
from datetime import datetime
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class ExtractedSkill:
    skill: str
    confidence: float
    category: str  # technical, soft, certification, language
    years_experience: Optional[float] = None

@dataclass
class ExtractedExperience:
    job_title: str
    company: str
    duration: str
    years: float
    skills_used: List[str]
    description: str

@dataclass
class ExtractedEducation:
    degree: str
    institution: str
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None

@dataclass
class CVData:
    skills: List[ExtractedSkill]
    experience: List[ExtractedExperience]
    education: List[ExtractedEducation]
    total_years_experience: float
    certifications: List[str]
    languages: List[str]
    soft_skills: List[str]
    raw_text: str
    location: Optional[str] = None

class CVParserService:
    """Advanced CV parsing service with NLP capabilities"""
    
    def __init__(self):
        """Initialize the CV parser with NLP models"""
        try:
            # Load English language model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Installing...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        self.stop_words = set(stopwords.words('english'))
        
        # Load skill taxonomies
        self.technical_skills = self._load_skill_taxonomy('technical')
        self.soft_skills = self._load_skill_taxonomy('soft')
        self.certifications = self._load_skill_taxonomy('certifications')
        self.languages = self._load_skill_taxonomy('languages')
    
    def _load_skill_taxonomy(self, category: str) -> Dict[str, List[str]]:
        """Load skill taxonomy from JSON files"""
        taxonomy_file = Path(f"data/skills/{category}_skills.json")
        if taxonomy_file.exists():
            with open(taxonomy_file, 'r') as f:
                return json.load(f)
        else:
            # Return default taxonomies
            return self._get_default_taxonomy(category)
    
    def _get_default_taxonomy(self, category: str) -> Dict[str, List[str]]:
        """Get default skill taxonomies"""
        if category == "technical":
            return {
                "programming_languages": ["python", "java", "javascript", "c++", "c#", "php", "ruby", "go", "rust", "swift", "kotlin"],
                "databases": ["mysql", "postgresql", "mongodb", "redis", "elasticsearch", "oracle", "sqlite"],
                "frameworks": ["react", "angular", "vue", "django", "flask", "spring", "express", "laravel"],
                "cloud_platforms": ["aws", "azure", "gcp", "heroku", "digitalocean"],
                "tools": ["git", "docker", "kubernetes", "jenkins", "jira", "confluence"]
            }
        elif category == "soft":
            return {
                "leadership": ["leadership", "management", "team building", "mentoring"],
                "communication": ["communication", "presentation", "public speaking", "writing"],
                "problem_solving": ["problem solving", "analytical thinking", "critical thinking"],
                "collaboration": ["collaboration", "teamwork", "cross-functional", "stakeholder management"]
            }
        elif category == "certifications":
            return {
                "aws": ["aws certified", "amazon web services"],
                "google": ["google cloud", "gcp certified"],
                "microsoft": ["microsoft certified", "azure"],
                "project_management": ["pmp", "prince2", "scrum master"]
            }
        elif category == "languages":
            return {
                "programming": ["python", "java", "javascript", "sql"],
                "human": ["english", "spanish", "french", "german", "chinese", "japanese"]
            }
        return {}
    
    async def parse_cv(self, file_path: str) -> CVData:
        """Parse CV file and extract structured data"""
        try:
            # Extract text from CV
            raw_text = await self._extract_text(file_path)
            
            # Parse different sections
            skills = await self._extract_skills(raw_text)
            experience = await self._extract_experience(raw_text)
            education = await self._extract_education(raw_text)
            location = await self._extract_location(raw_text)
            total_years = await self._calculate_total_experience(experience)
            certifications = await self._extract_certifications(raw_text)
            languages = await self._extract_languages(raw_text)
            soft_skills = await self._extract_soft_skills(raw_text)
            
            return CVData(
                skills=skills,
                experience=experience,
                education=education,
                location=location,
                total_years_experience=total_years,
                certifications=certifications,
                languages=languages,
                soft_skills=soft_skills,
                raw_text=raw_text
            )
            
        except Exception as e:
            logger.error(f"Error parsing CV: {e}")
            raise
    
    async def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF or DOCX file"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            return await self._extract_from_pdf(file_path)
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            return await self._extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    async def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
        return text
    
    async def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            raise
    
    async def _extract_skills(self, text: str) -> List[ExtractedSkill]:
        """Extract technical skills from CV text"""
        skills = []
        doc = self.nlp(text.lower())
        
        # Extract technical skills
        for category, skill_list in self.technical_skills.items():
            for skill in skill_list:
                if skill in text.lower():
                    # Calculate confidence based on context
                    confidence = self._calculate_skill_confidence(text, skill)
                    skills.append(ExtractedSkill(
                        skill=skill,
                        confidence=confidence,
                        category="technical"
                    ))
        
        # Extract skills with experience years
        skill_patterns = [
            r'(\w+)\s*(\d+(?:\.\d+)?)\s*years?',
            r'(\d+(?:\.\d+)?)\s*years?\s*of\s*(\w+)',
            r'(\w+)\s*experience\s*(\d+(?:\.\d+)?)\s*years?'
        ]
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                skill_name = match.group(1) if match.group(1).isalpha() else match.group(2)
                years = float(match.group(2) if match.group(1).isalpha() else match.group(1))
                
                if skill_name in [s.skill for s in skills]:
                    # Update existing skill with years
                    for skill in skills:
                        if skill.skill == skill_name:
                            skill.years_experience = years
                            break
                else:
                    skills.append(ExtractedSkill(
                        skill=skill_name,
                        confidence=0.7,
                        category="technical",
                        years_experience=years
                    ))
        
        return skills
    
    async def _extract_experience(self, text: str) -> List[ExtractedExperience]:
        """Extract work experience from CV text"""
        experience = []
        
        # Common job title patterns
        job_patterns = [
            r'(\w+(?:\s+\w+)*)\s+(?:at|with|for)\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+(\d{4})\s*-\s*(\d{4}|present)',
            r'(\w+(?:\s+\w+)*)\s+(\w+(?:\s+\w+)*)\s+(\d{4})\s*-\s*(\d{4}|present)'
        ]
        
        for pattern in job_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    job_title = match.group(1).strip()
                    company = match.group(2).strip()
                    
                    # Extract duration
                    duration = ""
                    if len(match.groups()) >= 3:
                        start_year = match.group(3)
                        end_year = match.group(4) if len(match.groups()) >= 4 else "Present"
                        duration = f"{start_year} - {end_year}"
                    
                    # Calculate years of experience
                    years = self._calculate_duration_years(duration)
                    
                    # Extract skills used in this role
                    skills_used = self._extract_skills_from_context(text, job_title)
                    
                    experience.append(ExtractedExperience(
                        job_title=job_title,
                        company=company,
                        duration=duration,
                        years=years,
                        skills_used=skills_used,
                        description=""
                    ))
        
        return experience
    
    async def _extract_education(self, text: str) -> List[ExtractedEducation]:
        """Extract education information from CV text"""
        education = []
        
        # Education patterns
        edu_patterns = [
            r'(Bachelor|Master|PhD|BSc|MSc|MBA)\s+(?:of|in)\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+(?:University|College|Institute)',
            r'(\w+(?:\s+\w+)*)\s+(\d{4})'  # Degree and graduation year
        ]
        
        for pattern in edu_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                degree = match.group(1).strip()
                institution = match.group(2).strip() if len(match.groups()) >= 2 else ""
                graduation_year = None
                
                # Extract graduation year
                year_match = re.search(r'(\d{4})', match.group(0))
                if year_match:
                    graduation_year = int(year_match.group(1))
                
                education.append(ExtractedEducation(
                    degree=degree,
                    institution=institution,
                    graduation_year=graduation_year
                ))
        
        return education
    
    async def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from CV text"""
        # Location patterns
        location_patterns = [
            r'(\w+(?:\s+\w+)*),\s*(\w+(?:\s+\w+)*)',  # City, Country
            r'(\w+(?:\s+\w+)*),\s*(\w{2})',  # City, State
            r'(\w+(?:\s+\w+)*)\s+(\w{2})\s+(\d{5})'  # City State ZIP
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    async def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications from CV text"""
        certifications = []
        
        for category, cert_list in self.certifications.items():
            for cert in cert_list:
                if cert.lower() in text.lower():
                    certifications.append(cert)
        
        return certifications
    
    async def _extract_languages(self, text: str) -> List[str]:
        """Extract programming and human languages from CV text"""
        languages = []
        
        for category, lang_list in self.languages.items():
            for lang in lang_list:
                if lang.lower() in text.lower():
                    languages.append(lang)
        
        return languages
    
    async def _extract_soft_skills(self, text: str) -> List[str]:
        """Extract soft skills from CV text"""
        soft_skills = []
        
        for category, skill_list in self.soft_skills.items():
            for skill in skill_list:
                if skill.lower() in text.lower():
                    soft_skills.append(skill)
        
        return soft_skills
    
    def _calculate_skill_confidence(self, text: str, skill: str) -> float:
        """Calculate confidence score for skill extraction"""
        # Simple confidence calculation based on frequency and context
        skill_lower = skill.lower()
        text_lower = text.lower()
        
        frequency = text_lower.count(skill_lower)
        context_words = ["experience", "proficient", "expert", "skilled", "knowledge"]
        
        context_score = sum(1 for word in context_words if word in text_lower)
        
        # Normalize confidence score
        confidence = min(1.0, (frequency * 0.3) + (context_score * 0.2))
        return max(0.1, confidence)
    
    def _calculate_duration_years(self, duration: str) -> float:
        """Calculate years of experience from duration string"""
        if not duration:
            return 0.0
        
        # Extract years from duration
        year_pattern = r'(\d{4})'
        years = re.findall(year_pattern, duration)
        
        if len(years) >= 2:
            start_year = int(years[0])
            end_year = int(years[1]) if years[1] != "Present" else datetime.now().year
            return end_year - start_year
        elif len(years) == 1:
            # Single year mentioned
            return 1.0
        
        return 0.0
    
    def _extract_skills_from_context(self, text: str, job_title: str) -> List[str]:
        """Extract skills mentioned in the context of a job title"""
        skills = []
        
        # Find the section around the job title
        job_index = text.lower().find(job_title.lower())
        if job_index != -1:
            # Extract text around the job title (500 characters before and after)
            start = max(0, job_index - 500)
            end = min(len(text), job_index + 500)
            context = text[start:end]
            
            # Extract skills from this context
            for category, skill_list in self.technical_skills.items():
                for skill in skill_list:
                    if skill.lower() in context.lower():
                        skills.append(skill)
        
        return skills
    
    async def _calculate_total_experience(self, experience: List[ExtractedExperience]) -> float:
        """Calculate total years of experience"""
        total_years = 0.0
        
        for exp in experience:
            total_years += exp.years
        
        return total_years

# Create global instance
cv_parser_service = CVParserService() 