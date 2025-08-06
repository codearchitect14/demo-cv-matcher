import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class SkillMatcher:
    """Advanced skill matching service with semantic similarity"""
    
    def __init__(self):
        """Initialize the skill matcher"""
        self.skill_taxonomy = self._load_skill_taxonomy()
        self.skill_aliases = self._build_skill_aliases()
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            max_features=1000
        )
        self.skill_vectors = None
        self.skill_names = []
        self._build_skill_vectors()
    
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
            logger.info(f"✅ Loaded {len(all_skills)} skill categories for matching")
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
    
    def _build_skill_aliases(self) -> Dict[str, str]:
        """Build skill aliases mapping"""
        aliases = {}
        
        # Common skill aliases
        alias_mappings = {
            "Python": ["py", "python3", "python3.x"],
            "JavaScript": ["js", "ecmascript", "javascript"],
            "Java": ["jdk", "jvm", "java8", "java11"],
            "C++": ["cpp", "cplusplus"],
            "C#": ["csharp", "dotnet"],
            "Go": ["golang"],
            "Rust": ["rustlang"],
            "TypeScript": ["ts", "typescript"],
            "PHP": ["php"],
            "Ruby": ["ruby"],
            "SQL": ["sql", "structured query language"],
            "PostgreSQL": ["postgres", "psql", "postgresql"],
            "MySQL": ["mysql", "mariadb"],
            "MongoDB": ["mongo", "mongodb"],
            "Redis": ["redis"],
            "React": ["reactjs", "react.js", "react"],
            "Vue.js": ["vue", "vuejs", "vue.js"],
            "Angular": ["angularjs", "angular"],
            "Django": ["django"],
            "Flask": ["flask"],
            "Spring": ["springboot", "spring-boot", "spring"],
            "Express.js": ["express", "expressjs", "express.js"],
            "Laravel": ["laravel"],
            "Ruby on Rails": ["rails", "ror", "ruby on rails"],
            "AWS": ["amazon", "amazon-web-services", "aws"],
            "Azure": ["microsoft-azure", "azure"],
            "Google Cloud": ["gcp", "google-cloud-platform", "google cloud"],
            "Docker": ["docker"],
            "Kubernetes": ["k8s", "kube", "kubernetes"],
            "Jenkins": ["jenkins"],
            "Git": ["git"],
            "Terraform": ["terraform"],
            "TensorFlow": ["tensorflow"],
            "PyTorch": ["pytorch"],
            "Scikit-learn": ["sklearn", "scikit-learn"],
            "Pandas": ["pandas"],
            "NumPy": ["numpy"],
            "Matplotlib": ["matplotlib"],
            "HTML": ["html5", "html"],
            "CSS": ["css3", "css"],
            "Node.js": ["node", "nodejs", "node.js"],
            "REST API": ["rest", "api", "restful"],
            "GraphQL": ["graphql"],
            "Leadership": ["lead", "management", "leadership"],
            "Communication": ["communication"],
            "Problem Solving": ["problem-solving", "analytical", "problem solving"],
            "Teamwork": ["collaboration", "team", "teamwork"],
            "Agile": ["scrum", "kanban", "agile"]
        }
        
        for skill, alias_list in alias_mappings.items():
            for alias in alias_list:
                aliases[alias.lower()] = skill
        
        return aliases
    
    def _build_skill_vectors(self):
        """Build TF-IDF vectors for all skills"""
        all_skills = []
        self.skill_names = []
        
        for category, skills in self.skill_taxonomy.items():
            for skill in skills:
                all_skills.append(f"{skill} {category}")
                self.skill_names.append(skill)
        
        # Add aliases to the corpus
        for alias, skill in self.skill_aliases.items():
            all_skills.append(f"{alias} {skill}")
        
        if all_skills:
            self.skill_vectors = self.vectorizer.fit_transform(all_skills)
            logger.info(f"✅ Built vectors for {len(self.skill_names)} skills")
        else:
            logger.warning("⚠️ No skills found for vectorization")
    
    def find_skill_matches(self, query_skill: str, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Find skill matches using semantic similarity"""
        if not self.skill_vectors or not self.skill_names:
            return []
        
        # Vectorize the query
        query_vector = self.vectorizer.transform([query_skill])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.skill_vectors).flatten()
        
        # Find matches above threshold
        matches = []
        for i, similarity in enumerate(similarities):
            if similarity >= threshold and i < len(self.skill_names):
                matches.append((self.skill_names[i], float(similarity)))
        
        # Sort by similarity score
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def normalize_skill_name(self, skill_name: str) -> str:
        """Normalize skill name using aliases"""
        normalized = skill_name.lower().strip()
        
        # Check aliases
        if normalized in self.skill_aliases:
            return self.skill_aliases[normalized]
        
        # Check exact match
        for skill in self.skill_names:
            if skill.lower() == normalized:
                return skill
        
        # Try semantic matching
        matches = self.find_skill_matches(skill_name, threshold=0.5)
        if matches:
            return matches[0][0]
        
        return skill_name
    
    def expand_skill_matches(self, skills: List[str], threshold: float = 0.4) -> List[str]:
        """Expand skill list with semantic matches"""
        expanded_skills = set(skills)
        
        for skill in skills:
            matches = self.find_skill_matches(skill, threshold)
            for matched_skill, similarity in matches:
                if similarity >= threshold:
                    expanded_skills.add(matched_skill)
        
        return list(expanded_skills)
    
    def calculate_skill_overlap(self, required_skills: List[str], candidate_skills: List[str]) -> Dict[str, float]:
        """Calculate skill overlap between required and candidate skills"""
        overlap_scores = {}
        
        # Normalize skill names
        normalized_required = [self.normalize_skill_name(skill) for skill in required_skills]
        normalized_candidate = [self.normalize_skill_name(skill) for skill in candidate_skills]
        
        for req_skill in normalized_required:
            best_match_score = 0.0
            
            for cand_skill in normalized_candidate:
                # Exact match
                if req_skill.lower() == cand_skill.lower():
                    best_match_score = 1.0
                    break
                
                # Semantic match
                matches = self.find_skill_matches(req_skill, threshold=0.3)
                for matched_skill, similarity in matches:
                    if matched_skill.lower() == cand_skill.lower():
                        best_match_score = max(best_match_score, similarity)
                        break
            
            overlap_scores[req_skill] = best_match_score
        
        return overlap_scores
    
    def get_skill_category(self, skill_name: str) -> str:
        """Get the category for a skill"""
        normalized_skill = self.normalize_skill_name(skill_name)
        
        for category, skills in self.skill_taxonomy.items():
            if normalized_skill in skills:
                return category
        
        return "other"
    
    def get_related_skills(self, skill_name: str, threshold: float = 0.3) -> List[str]:
        """Get related skills based on semantic similarity"""
        matches = self.find_skill_matches(skill_name, threshold)
        return [skill for skill, score in matches if skill != skill_name]
    
    def validate_skill_requirements(self, job_skills: List[Dict], candidate_skills: List[Dict]) -> Dict[str, Dict]:
        """Validate candidate skills against job requirements"""
        validation_results = {}
        
        for job_skill in job_skills:
            skill_name = job_skill['name']
            min_years = job_skill.get('min_years_experience', 0)
            
            # Find matching candidate skill
            candidate_match = None
            for cand_skill in candidate_skills:
                if self.normalize_skill_name(cand_skill['name']) == self.normalize_skill_name(skill_name):
                    candidate_match = cand_skill
                    break
            
            if candidate_match:
                years_experience = candidate_match.get('years_experience', 0)
                meets_requirement = years_experience >= min_years
                
                validation_results[skill_name] = {
                    'required_years': min_years,
                    'candidate_years': years_experience,
                    'meets_requirement': meets_requirement,
                    'proficiency_level': candidate_match.get('proficiency_level', 'beginner'),
                    'last_used': candidate_match.get('last_used')
                }
            else:
                validation_results[skill_name] = {
                    'required_years': min_years,
                    'candidate_years': 0,
                    'meets_requirement': False,
                    'proficiency_level': None,
                    'last_used': None
                }
        
        return validation_results
    
    def calculate_overall_match_score(self, validation_results: Dict[str, Dict]) -> float:
        """Calculate overall match score based on skill validation"""
        if not validation_results:
            return 0.0
        
        total_skills = len(validation_results)
        matching_skills = sum(1 for result in validation_results.values() if result['meets_requirement'])
        
        # Base score from matching skills
        base_score = matching_skills / total_skills
        
        # Bonus for exceeding requirements
        bonus_score = 0.0
        for result in validation_results.values():
            if result['meets_requirement']:
                excess_years = result['candidate_years'] - result['required_years']
                if excess_years > 0:
                    bonus_score += min(excess_years / 5.0, 0.1)  # Cap bonus at 10% per skill
        
        return min(base_score + bonus_score, 1.0) 