import re
import json
import spacy
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import PyPDF2
from docx import Document
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExtractedSkill:
    """Extracted skill with experience duration"""
    name: str
    category: str
    years_experience: float
    proficiency_level: str
    last_used: Optional[datetime]
    experience_description: Optional[str]
    projects_worked: List[str]

@dataclass
class ExtractedExperience:
    """Extracted work experience"""
    company: str
    job_title: str
    start_date: datetime
    end_date: Optional[datetime]
    duration_months: int
    skills_used: List[str]
    responsibilities: List[str]

@dataclass
class ExtractedEducation:
    """Extracted education information"""
    institution: str
    degree: str
    field_of_study: str
    graduation_date: Optional[datetime]
    gpa: Optional[float]

@dataclass
class EnhancedCVData:
    """Enhanced CV data with skill-specific experience"""
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    total_years_experience: float
    skills: List[ExtractedSkill]
    experiences: List[ExtractedExperience]
    education: List[ExtractedEducation]
    certifications: List[str]
    languages: List[str]
    summary: Optional[str]

class EnhancedCVParser:
    """Enhanced CV parser with NER and skill-specific experience extraction"""
    
    def __init__(self):
        """Initialize the enhanced CV parser"""
        try:
            # Load spaCy model for NER
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("[SUCCESS] spaCy model loaded successfully")
        except OSError:
            logger.warning("⚠️ spaCy model not found. Installing...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Load skill taxonomy
        self.skill_taxonomy = self._load_skill_taxonomy()
        
        # Date patterns for parsing
        self.date_patterns = [
            r'(\w{3}\s+\d{4})\s*[-–]\s*(\w{3}\s+\d{4})',  # Jan 2020 - Dec 2022
            r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4})',  # 01/2020 - 12/2022
            r'(\w+\s+\d{4})\s*[-–]\s*(Present|Current)',  # Jan 2020 - Present
            r'(\d{4})\s*[-–]\s*(\d{4})',  # 2020 - 2022
        ]
        
        # Skill patterns for extraction
        self.skill_patterns = [
            r'\b(Python|JavaScript|Java|C\+\+|C#|Go|Rust|TypeScript|PHP|Ruby)\b',
            r'\b(SQL|PostgreSQL|MySQL|MongoDB|Redis|Oracle)\b',
            r'\b(React|Vue\.js|Angular|Django|Flask|Spring|Express\.js|Laravel)\b',
            r'\b(AWS|Azure|Google Cloud|Docker|Kubernetes|Jenkins|Git|Terraform)\b',
            r'\b(TensorFlow|PyTorch|Scikit-learn|Pandas|NumPy|Matplotlib)\b',
            r'\b(HTML|CSS|Node\.js|REST API|GraphQL)\b',
        ]
    
    def _load_skill_taxonomy(self) -> Dict[str, List[str]]:
        """Load skill taxonomy from JSON files"""
        try:
            # Load technical skills
            with open('data/skills/technical_skills.json', 'r') as f:
                technical_skills = json.load(f)
            
            # Load soft skills
            with open('data/skills/soft_skills.json', 'r') as f:
                soft_skills = json.load(f)
            
            # Combine all skills
            all_skills = {}
            for category, skills in technical_skills.items():
                all_skills[category] = skills
            
            all_skills.update(soft_skills)
            logger.info(f"[SUCCESS] Loaded {len(all_skills)} skill categories")
            return all_skills
            
        except FileNotFoundError:
            logger.warning("⚠️ Skill taxonomy files not found. Using default skills.")
            return {
                "programming": ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust"],
                "database": ["SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis"],
                "framework": ["React", "Vue.js", "Angular", "Django", "Flask"],
                "cloud": ["AWS", "Azure", "Google Cloud"],
                "devops": ["Docker", "Kubernetes", "Jenkins", "Git"],
                "ml": ["TensorFlow", "PyTorch", "Scikit-learn"],
                "soft_skills": ["Leadership", "Communication", "Problem Solving", "Teamwork"]
            }
    
    def parse_cv(self, file_path: str) -> EnhancedCVData:
        """Parse CV file and extract enhanced data"""
        try:
            # Extract text from CV
            text = self._extract_text(file_path)
            
            # Parse basic information
            basic_info = self._extract_basic_info(text)
            
            # Extract experiences with skill mapping
            experiences = self._extract_experiences(text)
            
            # Extract skills with experience duration
            skills = self._extract_skills_with_experience(text, experiences)
            
            # Extract education
            education = self._extract_education(text)
            
            # Extract certifications and languages
            certifications = self._extract_certifications(text)
            languages = self._extract_languages(text)
            
            # Calculate total experience
            total_experience = sum(skill.years_experience for skill in skills)
            
            return EnhancedCVData(
                full_name=basic_info.get('name', ''),
                email=basic_info.get('email'),
                phone=basic_info.get('phone'),
                location=basic_info.get('location'),
                total_years_experience=total_experience,
                skills=skills,
                experiences=experiences,
                education=education,
                certifications=certifications,
                languages=languages,
                summary=basic_info.get('summary')
            )
            
        except Exception as e:
            logger.error(f"[ERROR] Error parsing CV: {e}")
            raise
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF or DOCX file"""
        if file_path.lower().endswith('.pdf'):
            return self._extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            return self._extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"[ERROR] Error extracting text from PDF: {e}")
            raise
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"[ERROR] Error extracting text from DOCX: {e}")
            raise
    
    def _extract_basic_info(self, text: str) -> Dict[str, str]:
        """Extract basic information using NER"""
        doc = self.nlp(text)
        
        # Extract name (first PERSON entity)
        name = ""
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text
                break
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        email = email_match.group() if email_match else None
        
        # Extract phone
        phone_pattern = r'(\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})'
        phone_match = re.search(phone_pattern, text)
        phone = phone_match.group() if phone_match else None
        
        # Extract location (GPE entities)
        locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
        location = locations[0] if locations else None
        
        # Extract summary (first few sentences)
        sentences = list(doc.sents)
        summary = sentences[0].text if sentences else None
        
        return {
            'name': name,
            'email': email,
            'phone': phone,
            'location': location,
            'summary': summary
        }
    
    def _extract_experiences(self, text: str) -> List[ExtractedExperience]:
        """Extract work experiences with dates and skills"""
        experiences = []
        
        # Split text into sections
        sections = text.split('\n\n')
        
        for section in sections:
            # Look for date patterns
            for pattern in self.date_patterns:
                matches = re.finditer(pattern, section, re.IGNORECASE)
                
                for match in matches:
                    try:
                        start_date_str = match.group(1)
                        end_date_str = match.group(2)
                        
                        # Parse dates
                        start_date = self._parse_date(start_date_str)
                        end_date = None if end_date_str.lower() in ['present', 'current'] else self._parse_date(end_date_str)
                        
                        # Extract company and job title
                        company, job_title = self._extract_company_and_title(section)
                        
                        # Calculate duration
                        duration_months = self._calculate_duration_months(start_date, end_date)
                        
                        # Extract skills used in this role
                        skills_used = self._extract_skills_from_text(section)
                        
                        # Extract responsibilities
                        responsibilities = self._extract_responsibilities(section)
                        
                        experience = ExtractedExperience(
                            company=company,
                            job_title=job_title,
                            start_date=start_date,
                            end_date=end_date,
                            duration_months=duration_months,
                            skills_used=skills_used,
                            responsibilities=responsibilities
                        )
                        
                        experiences.append(experience)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing experience: {e}")
                        continue
        
        return experiences
    
    def _extract_skills_with_experience(self, text: str, experiences: List[ExtractedExperience]) -> List[ExtractedSkill]:
        """Extract skills with their experience duration"""
        skills_dict = {}
        
        # Extract all skills from text
        all_skills = self._extract_skills_from_text(text)
        
        for skill_name in all_skills:
            # Find skill category
            category = self._find_skill_category(skill_name)
            
            # Calculate experience duration for this skill
            years_experience = self._calculate_skill_experience(skill_name, experiences)
            
            # Determine proficiency level
            proficiency_level = self._determine_proficiency_level(years_experience)
            
            # Find last used date
            last_used = self._find_last_used_date(skill_name, experiences)
            
            # Create skill object
            skill = ExtractedSkill(
                name=skill_name,
                category=category,
                years_experience=years_experience,
                proficiency_level=proficiency_level,
                last_used=last_used,
                experience_description=self._generate_skill_description(skill_name, experiences),
                projects_worked=self._find_projects_for_skill(skill_name, experiences)
            )
            
            skills_dict[skill_name] = skill
        
        return list(skills_dict.values())
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from text using patterns and NER"""
        skills = set()
        
        # Use skill patterns
        for pattern in self.skill_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skills.add(match.group(1))
        
        # Use skill taxonomy
        for category, skill_list in self.skill_taxonomy.items():
            for skill in skill_list:
                if skill.lower() in text.lower():
                    skills.add(skill)
        
        return list(skills)
    
    def _find_skill_category(self, skill_name: str) -> str:
        """Find the category for a skill"""
        for category, skills in self.skill_taxonomy.items():
            if skill_name in skills:
                return category
        return "other"
    
    def _calculate_skill_experience(self, skill_name: str, experiences: List[ExtractedExperience]) -> float:
        """Calculate total years of experience for a skill"""
        total_months = 0
        
        for experience in experiences:
            if skill_name in experience.skills_used:
                total_months += experience.duration_months
        
        return total_months / 12.0
    
    def _determine_proficiency_level(self, years_experience: float) -> str:
        """Determine proficiency level based on years of experience"""
        if years_experience < 1:
            return "beginner"
        elif years_experience < 3:
            return "intermediate"
        elif years_experience < 7:
            return "advanced"
        else:
            return "expert"
    
    def _find_last_used_date(self, skill_name: str, experiences: List[ExtractedExperience]) -> Optional[datetime]:
        """Find when the skill was last used"""
        last_used = None
        
        for experience in experiences:
            if skill_name in experience.skills_used:
                if experience.end_date:
                    if not last_used or experience.end_date > last_used:
                        last_used = experience.end_date
                else:
                    # Currently using this skill
                    last_used = datetime.now()
        
        return last_used
    
    def _generate_skill_description(self, skill_name: str, experiences: List[ExtractedExperience]) -> str:
        """Generate description of experience with a skill"""
        descriptions = []
        
        for experience in experiences:
            if skill_name in experience.skills_used:
                desc = f"{skill_name} at {experience.company} ({experience.job_title})"
                descriptions.append(desc)
        
        return "; ".join(descriptions)
    
    def _find_projects_for_skill(self, skill_name: str, experiences: List[ExtractedExperience]) -> List[str]:
        """Find projects where the skill was used"""
        projects = []
        
        for experience in experiences:
            if skill_name in experience.skills_used:
                project = f"{experience.company} - {experience.job_title}"
                projects.append(project)
        
        return projects
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        try:
            return date_parser.parse(date_str)
        except:
            # Try common date formats
            formats = ['%b %Y', '%m/%Y', '%Y', '%B %Y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
            raise ValueError(f"Could not parse date: {date_str}")
    
    def _extract_company_and_title(self, text: str) -> Tuple[str, str]:
        """Extract company name and job title from text"""
        # Simple extraction - can be enhanced with NER
        lines = text.split('\n')
        company = "Unknown Company"
        job_title = "Unknown Title"
        
        for line in lines:
            if any(word in line.lower() for word in ['inc', 'corp', 'ltd', 'company', 'tech']):
                company = line.strip()
            elif any(word in line.lower() for word in ['developer', 'engineer', 'manager', 'analyst', 'specialist']):
                job_title = line.strip()
        
        return company, job_title
    
    def _calculate_duration_months(self, start_date: datetime, end_date: Optional[datetime]) -> int:
        """Calculate duration in months"""
        if not end_date:
            end_date = datetime.now()
        
        delta = relativedelta(end_date, start_date)
        return delta.years * 12 + delta.months
    
    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract responsibilities from text"""
        responsibilities = []
        
        # Look for bullet points or numbered lists
        lines = text.split('\n')
        for line in lines:
            if line.strip().startswith(('•', '-', '*', '1.', '2.', '3.')):
                responsibility = line.strip().lstrip('•-*1234567890. ')
                if responsibility:
                    responsibilities.append(responsibility)
        
        return responsibilities
    
    def _extract_education(self, text: str) -> List[ExtractedEducation]:
        """Extract education information"""
        education = []
        
        # Look for education section
        education_patterns = [
            r'education',
            r'degree',
            r'university',
            r'college',
            r'bachelor',
            r'master',
            r'phd'
        ]
        
        # Simple extraction - can be enhanced
        return education
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        certifications = []
        
        cert_patterns = [
            r'\b(AWS|Azure|Google Cloud)\s+Certified',
            r'\b(CISSP|CISM|CISA)\b',
            r'\b(PMP|PRINCE2)\b',
            r'\b(CCNA|CCNP|CCIE)\b',
            r'\b(CompTIA|A\+|Network\+|Security\+)\b'
        ]
        
        for pattern in cert_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                certifications.append(match.group())
        
        return certifications
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract programming and human languages"""
        languages = []
        
        # Programming languages
        prog_languages = ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust']
        for lang in prog_languages:
            if lang.lower() in text.lower():
                languages.append(lang)
        
        # Human languages
        human_languages = ['English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese']
        for lang in human_languages:
            if lang.lower() in text.lower():
                languages.append(lang)
        
        return languages 