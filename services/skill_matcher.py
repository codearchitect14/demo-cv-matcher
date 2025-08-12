import json
import os
import asyncio
from typing import List, Dict, Tuple, Optional, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class AdvancedSkillMatcher:
    """Advanced skill matching with fuzzy logic, semantic similarity, and context awareness"""
    
    def __init__(self):
        self.skill_taxonomy = self._load_skill_taxonomy()
        self.skill_aliases = self._build_skill_aliases()
        self.skill_vectors = None
        self.skill_names = []
        self.vectorizer = None
        self._build_skill_vectors()
        
        # Thread pool for CPU-intensive operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="skill_matcher")
        
        # Load thresholds from environment variables with defaults
        self.exact_match_threshold = float(os.getenv("SKILL_EXACT_MATCH_THRESHOLD", "100"))
        self.fuzzy_match_threshold = float(os.getenv("SKILL_FUZZY_MATCH_THRESHOLD", "85"))
        self.semantic_match_threshold = float(os.getenv("SKILL_SEMANTIC_MATCH_THRESHOLD", "0.7"))
        self.context_match_threshold = float(os.getenv("SKILL_CONTEXT_MATCH_THRESHOLD", "0.6"))
        self.min_skill_confidence = float(os.getenv("SKILL_MIN_CONFIDENCE", "0.3"))
        self.max_skill_variations = int(os.getenv("SKILL_MAX_VARIATIONS", "5"))
        
        # Skill categories for context-aware matching
        self.skill_categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala'],
            'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle', 'sql server', 'sqlite'],
            'frameworks': ['django', 'flask', 'spring', 'react', 'angular', 'vue', 'express', 'laravel', 'rails'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'gitlab'],
            'ml_ai': ['tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'matplotlib', 'opencv', 'nltk'],
            'tools': ['git', 'jira', 'confluence', 'slack', 'microsoft office', 'adobe creative suite'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem solving', 'time management', 'adaptability']
        }
        
        logger.info(f"Skill matcher initialized with thresholds: exact={self.exact_match_threshold}, "
                   f"fuzzy={self.fuzzy_match_threshold}, semantic={self.semantic_match_threshold}")
    
    def __del__(self):
        """Cleanup thread pool executor"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
    
    async def find_skill_matches_async(self, query_skill: str, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Async wrapper for skill matching with thread pool execution"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.find_skill_matches,
            query_skill,
            threshold
        )
    
    async def calculate_skill_overlap_async(self, required_skills: List[str], candidate_skills: List[str]) -> Dict[str, float]:
        """Async wrapper for skill overlap calculation"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.calculate_skill_overlap,
            required_skills,
            candidate_skills
        )
    
    async def validate_skill_requirements_async(self, job_skills: List[Dict], candidate_skills: List[Dict]) -> Dict[str, Dict]:
        """Async wrapper for skill requirement validation"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.validate_skill_requirements,
            job_skills,
            candidate_skills
        )
    
    async def calculate_overall_match_score_async(self, validation_results: Dict[str, Dict]) -> float:
        """Async wrapper for overall match score calculation"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.calculate_overall_match_score,
            validation_results
        )
    
    async def expand_skill_matches_async(self, skills: List[str], threshold: float = 0.4) -> List[str]:
        """Async wrapper for skill expansion"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.expand_skill_matches,
            skills,
            threshold
        )
    
    async def get_related_skills_async(self, skill_name: str, threshold: float = 0.3) -> List[str]:
        """Async wrapper for related skills lookup"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.get_related_skills,
            skill_name,
            threshold
        )
    
    def _load_skill_taxonomy(self) -> Dict[str, List[str]]:
        """Load skill taxonomy from JSON files"""
        taxonomy = {}
        
        # Load technical skills
        try:
            with open('data/skills/technical_skills.json', 'r') as f:
                technical_skills = json.load(f)
                taxonomy.update(technical_skills)
        except FileNotFoundError:
            logger.warning("Technical skills file not found")
        
        # Load soft skills
        try:
            with open('data/skills/soft_skills.json', 'r') as f:
                soft_skills = json.load(f)
                taxonomy.update(soft_skills)
        except FileNotFoundError:
            logger.warning("Soft skills file not found")
        
        # Load language skills
        try:
            with open('data/skills/languages_skills.json', 'r') as f:
                language_skills = json.load(f)
                taxonomy.update(language_skills)
        except FileNotFoundError:
            logger.warning("Language skills file not found")
        
        # Load certification skills
        try:
            with open('data/skills/certifications_skills.json', 'r') as f:
                cert_skills = json.load(f)
                taxonomy.update(cert_skills)
        except FileNotFoundError:
            logger.warning("Certification skills file not found")
        
        return taxonomy
    
    def _build_skill_aliases(self) -> Dict[str, str]:
        """Build comprehensive skill aliases mapping"""
        aliases = {}
        
        # Programming language aliases
        aliases.update({
            'js': 'javascript',
            'ts': 'typescript',
            'cpp': 'c++',
            'csharp': 'c#',
            'golang': 'go',
            'node': 'node.js',
            'nodejs': 'node.js',
            'reactjs': 'react',
            'angularjs': 'angular',
            'vuejs': 'vue',
            'djangoframework': 'django',
            'flaskframework': 'flask',
            'springframework': 'spring',
            'expressjs': 'express',
            'laravelframework': 'laravel',
            'rubyonrails': 'rails',
            'ror': 'rails',
            'mysql': 'mysql',
            'postgres': 'postgresql',
            'mongo': 'mongodb',
            'elastic': 'elasticsearch',
            'mssql': 'sql server',
            'aws': 'amazon web services',
            'azure': 'microsoft azure',
            'gcp': 'google cloud platform',
            'k8s': 'kubernetes',
            'tf': 'terraform',
            'ci/cd': 'continuous integration',
            'devops': 'devops',
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'nlp': 'natural language processing',
            'cv': 'computer vision',
            'ds': 'data science',
            'ui': 'user interface',
            'ux': 'user experience',
            'api': 'application programming interface',
            'rest': 'rest api',
            'graphql': 'graphql api',
            'microservices': 'microservices architecture',
            'agile': 'agile methodology',
            'scrum': 'scrum methodology',
            'kanban': 'kanban methodology',
            'jira': 'atlassian jira',
            'confluence': 'atlassian confluence',
            'slack': 'slack communication',
            'teams': 'microsoft teams',
            'zoom': 'zoom video conferencing',
            'office': 'microsoft office',
            'excel': 'microsoft excel',
            'word': 'microsoft word',
            'powerpoint': 'microsoft powerpoint',
            'photoshop': 'adobe photoshop',
            'illustrator': 'adobe illustrator',
            'figma': 'figma design',
            'sketch': 'sketch design',
            'invision': 'invision prototyping',
            'zeplin': 'zeplin design handoff',
            'git': 'git version control',
            'github': 'github',
            'gitlab': 'gitlab',
            'bitbucket': 'bitbucket',
            'svn': 'subversion',
            'linux': 'linux administration',
            'unix': 'unix administration',
            'bash': 'bash scripting',
            'shell': 'shell scripting',
            'powershell': 'powershell scripting',
            'python': 'python programming',
            'java': 'java programming',
            'javascript': 'javascript programming',
            'typescript': 'typescript programming',
            'html': 'html markup',
            'css': 'css styling',
            'sass': 'sass styling',
            'less': 'less styling',
            'bootstrap': 'bootstrap framework',
            'tailwind': 'tailwind css',
            'material': 'material design',
            'responsive': 'responsive design',
            'mobile': 'mobile development',
            'ios': 'ios development',
            'android': 'android development',
            'react native': 'react native',
            'flutter': 'flutter development',
            'xamarin': 'xamarin development',
            'ionic': 'ionic framework',
            'cordova': 'apache cordova',
            'phonegap': 'adobe phonegap',
            'pwa': 'progressive web app',
            'spa': 'single page application',
            'ssr': 'server side rendering',
            'csr': 'client side rendering',
            'seo': 'search engine optimization',
            'sem': 'search engine marketing',
            'ppc': 'pay per click',
            'cpc': 'cost per click',
            'cpm': 'cost per mille',
            'ctr': 'click through rate',
            'conversion': 'conversion rate optimization',
            'cro': 'conversion rate optimization',
            'a/b testing': 'ab testing',
            'ab testing': 'a/b testing',
            'analytics': 'web analytics',
            'google analytics': 'google analytics',
            'ga': 'google analytics',
            'gtm': 'google tag manager',
            'hotjar': 'hotjar analytics',
            'mixpanel': 'mixpanel analytics',
            'amplitude': 'amplitude analytics',
            'segment': 'segment analytics',
            'snowplow': 'snowplow analytics',
            'rudderstack': 'rudderstack analytics',
            'airbyte': 'airbyte etl',
            'fivetran': 'fivetran etl',
            'stitch': 'stitch etl',
            'talend': 'talend etl',
            'informatica': 'informatica etl',
            'ssis': 'sql server integration services',
            'datafactory': 'azure data factory',
            'glue': 'aws glue',
            'dataproc': 'google cloud dataproc',
            'databricks': 'databricks platform',
            'snowflake': 'snowflake data warehouse',
            'redshift': 'amazon redshift',
            'bigquery': 'google bigquery',
            'synapse': 'azure synapse analytics',
            'tableau': 'tableau bi',
            'powerbi': 'microsoft power bi',
            'looker': 'looker bi',
            'qlik': 'qlik bi',
            'metabase': 'metabase bi',
            'superset': 'apache superset',
            'grafana': 'grafana monitoring',
            'kibana': 'elasticsearch kibana',
            'prometheus': 'prometheus monitoring',
            'datadog': 'datadog monitoring',
            'newrelic': 'new relic monitoring',
            'splunk': 'splunk monitoring',
            'pagerduty': 'pagerduty alerting',
            'opsgenie': 'atlassian opsgenie',
            'victorops': 'splunk victorops',
            'zendesk': 'zendesk support',
            'salesforce': 'salesforce crm',
            'hubspot': 'hubspot crm',
            'pipedrive': 'pipedrive crm',
            'zoho': 'zoho crm',
            'freshdesk': 'freshdesk support',
            'intercom': 'intercom customer messaging',
            'drift': 'drift conversational marketing',
            'calendly': 'calendly scheduling',
            'zoom': 'zoom video conferencing',
            'teams': 'microsoft teams',
            'slack': 'slack communication',
            'discord': 'discord communication',
            'telegram': 'telegram messaging',
            'whatsapp': 'whatsapp business',
            'wechat': 'wechat messaging',
            'line': 'line messaging',
            'viber': 'viber messaging',
            'signal': 'signal messaging',
            'wire': 'wire secure messaging',
            'element': 'element matrix client',
            'mattermost': 'mattermost team collaboration',
            'rocket.chat': 'rocket.chat team collaboration',
            'chime': 'amazon chime',
            'bluejeans': 'bluejeans video conferencing',
            'webex': 'cisco webex',
            'gotomeeting': 'gotomeeting video conferencing',
            'join.me': 'join.me screen sharing',
            'teamviewer': 'teamviewer remote access',
            'anydesk': 'anydesk remote access',
            'vnc': 'vnc remote access',
            'rdp': 'remote desktop protocol',
            'ssh': 'secure shell',
            'ftp': 'file transfer protocol',
            'sftp': 'secure file transfer protocol',
            'scp': 'secure copy protocol',
            'rsync': 'rsync file synchronization',
            'git': 'git version control',
            'svn': 'subversion version control',
            'mercurial': 'mercurial version control',
            'perforce': 'perforce version control',
            'clearcase': 'ibm clearcase',
            'tfs': 'team foundation server',
            'vsts': 'visual studio team services',
            'azure devops': 'azure devops',
            'gitlab ci': 'gitlab continuous integration',
            'github actions': 'github actions',
            'jenkins': 'jenkins continuous integration',
            'bamboo': 'atlassian bamboo',
            'teamcity': 'jetbrains teamcity',
            'circleci': 'circleci continuous integration',
            'travis ci': 'travis ci continuous integration',
            'codeship': 'codeship continuous integration',
            'semaphore': 'semaphore continuous integration',
            'drone': 'drone continuous integration',
            'concourse': 'concourse continuous integration',
            'spinnaker': 'spinnaker continuous delivery',
            'argo': 'argo continuous delivery',
            'tekton': 'tekton continuous delivery',
            'istio': 'istio service mesh',
            'linkerd': 'linkerd service mesh',
            'consul': 'hashicorp consul',
            'etcd': 'etcd distributed key-value store',
            'zookeeper': 'apache zookeeper',
            'kafka': 'apache kafka',
            'rabbitmq': 'rabbitmq message broker',
            'activemq': 'apache activemq',
            'redis': 'redis cache',
            'memcached': 'memcached cache',
            'hazelcast': 'hazelcast cache',
            'couchbase': 'couchbase nosql database',
            'cassandra': 'apache cassandra',
            'hbase': 'apache hbase',
            'dynamodb': 'amazon dynamodb',
            'cosmos db': 'azure cosmos db',
            'firestore': 'google cloud firestore',
            'firebase': 'google firebase',
            'supabase': 'supabase backend as a service',
            'appwrite': 'appwrite backend as a service',
            'parse': 'parse backend as a service',
            'backendless': 'backendless backend as a service',
            'kinvey': 'kinvey backend as a service',
            'kumulos': 'kumulos backend as a service',
            'heroku': 'heroku platform as a service',
            'vercel': 'vercel platform as a service',
            'netlify': 'netlify platform as a service',
            'surge': 'surge static site hosting',
            'github pages': 'github pages static hosting',
            'gitlab pages': 'gitlab pages static hosting',
            'bitbucket pages': 'bitbucket pages static hosting',
            'aws s3': 'amazon s3 object storage',
            'azure blob': 'azure blob storage',
            'gcs': 'google cloud storage',
            'cloudfront': 'amazon cloudfront cdn',
            'cloudflare': 'cloudflare cdn',
            'akamai': 'akamai cdn',
            'fastly': 'fastly cdn',
            'bunny cdn': 'bunny cdn',
            'keycdn': 'keycdn',
            'stackpath': 'stackpath cdn',
            'limelight': 'limelight cdn',
            'level3': 'level3 cdn',
            'cogent': 'cogent communications',
            'he': 'hurricane electric',
            'telia': 'telia carrier',
            'nordunet': 'nordunet carrier',
            'ams-ix': 'amsterdam internet exchange',
            'linx': 'london internet exchange',
            'de-cix': 'deutsche commercial internet exchange',
            'equinix': 'equinix data center',
            'digital realty': 'digital realty data center',
            'cyxtera': 'cyxtera data center',
            'interxion': 'interxion data center',
            'telehouse': 'telehouse data center',
            'telecity': 'telecity data center',
            'level3': 'level3 communications',
            'cogent': 'cogent communications',
            'he': 'hurricane electric',
            'telia': 'telia carrier',
            'nordunet': 'nordunet carrier',
            'ams-ix': 'amsterdam internet exchange',
            'linx': 'london internet exchange',
            'de-cix': 'deutsche commercial internet exchange',
            'equinix': 'equinix data center',
            'digital realty': 'digital realty data center',
            'cyxtera': 'cyxtera data center',
            'interxion': 'interxion data center',
            'telehouse': 'telehouse data center',
            'telecity': 'telecity data center'
        })
        
        return aliases
    
    def _build_skill_vectors(self):
        """Build TF-IDF vectors for semantic matching"""
        try:
            # Collect all skills from taxonomy
            all_skills = []
            for category, skills in self.skill_taxonomy.items():
                all_skills.extend(skills)
            
            # Add aliases
            all_skills.extend(list(self.skill_aliases.keys()))
            
            # Remove duplicates and normalize
            self.skill_names = list(set([skill.lower().strip() for skill in all_skills]))
            
            if self.skill_names:
                # Create TF-IDF vectorizer
                self.vectorizer = TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.9,
                    stop_words='english'
                )
                
                # Fit vectorizer
                self.skill_vectors = self.vectorizer.fit_transform(self.skill_names)
                
        except Exception as e:
            logger.error(f"Failed to build skill vectors: {e}")
            self.skill_vectors = None
            self.skill_names = []
    
    def find_skill_matches(self, query_skill: str, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Find skill matches using semantic similarity"""
        if not self.skill_vectors or not self.skill_names:
            return []
        
        try:
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
        except Exception as e:
            logger.warning(f"Semantic matching failed for '{query_skill}': {e}")
            return []
    
    def normalize_skill_name(self, skill_name: str) -> str:
        """Normalize skill name using aliases and fuzzy matching"""
        normalized = skill_name.lower().strip()
        
        # Check exact alias match
        if normalized in self.skill_aliases:
            return self.skill_aliases[normalized]
        
        # Check exact match in skill names
        for skill in self.skill_names:
            if skill.lower() == normalized:
                return skill
        
        # Try fuzzy matching
        best_match = process.extractOne(normalized, self.skill_names, scorer=fuzz.token_sort_ratio)
        if best_match and best_match[1] >= self.fuzzy_match_threshold:
            return best_match[0]
        
        # Try semantic matching (only if vectorizer is available)
        try:
            matches = self.find_skill_matches(skill_name, threshold=self.semantic_match_threshold)
            if matches:
                return matches[0][0]
        except Exception as e:
            logger.warning(f"Semantic matching failed for '{skill_name}': {e}")
            # Fall back to original skill name
        
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
        """Calculate skill overlap between required and candidate skills with advanced matching"""
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
                
                # Fuzzy match
                fuzzy_score = fuzz.token_sort_ratio(req_skill.lower(), cand_skill.lower())
                if fuzzy_score >= self.fuzzy_match_threshold:
                    best_match_score = max(best_match_score, fuzzy_score / 100.0)
                
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
        """Validate candidate skills against job requirements with advanced matching"""
        validation_results = {}
        
        for job_skill in job_skills:
            skill_name = job_skill.get('skill', '')
            required_years = job_skill.get('min_experience', 0)
            
            best_match = None
            best_score = 0.0
            
            for candidate_skill in candidate_skills:
                cand_skill_name = candidate_skill.get('skill', '')
                cand_years = candidate_skill.get('years', 0)
                
                # Calculate match score using multiple methods
                match_score = self._calculate_skill_match_score(skill_name, cand_skill_name)
                
                if match_score > best_score:
                    best_score = match_score
                    best_match = {
                        'skill': cand_skill_name,
                        'years': cand_years,
                        'match_score': match_score,
                        'meets_experience': cand_years >= required_years
                    }
            
            validation_results[skill_name] = {
                'required_years': required_years,
                'best_match': best_match,
                'is_met': best_match and best_match['meets_experience'] if best_match else False
            }
        
        return validation_results
    
    def _calculate_skill_match_score(self, required_skill: str, candidate_skill: str) -> float:
        """Calculate comprehensive skill match score"""
        # Exact match
        if required_skill.lower() == candidate_skill.lower():
            return 1.0
        
        # Fuzzy match
        fuzzy_score = fuzz.token_sort_ratio(required_skill.lower(), candidate_skill.lower()) / 100.0
        
        # Semantic match
        semantic_matches = self.find_skill_matches(required_skill, threshold=0.3)
        semantic_score = 0.0
        for matched_skill, similarity in semantic_matches:
            if matched_skill.lower() == candidate_skill.lower():
                semantic_score = similarity
                break
        
        # Context-aware match (check if skills are in same category)
        context_score = 0.0
        req_category = self.get_skill_category(required_skill)
        cand_category = self.get_skill_category(candidate_skill)
        if req_category == cand_category and req_category != "other":
            context_score = 0.3
        
        # Return the highest score
        return max(fuzzy_score, semantic_score, context_score)
    
    def calculate_overall_match_score(self, validation_results: Dict[str, Dict]) -> float:
        """Calculate overall match score from validation results"""
        if not validation_results:
            return 0.0
        
        total_score = 0.0
        total_skills = len(validation_results)
        
        for skill_name, result in validation_results.items():
            if result['is_met']:
                total_score += 1.0
            elif result['best_match']:
                # Partial credit for skills that match but don't meet experience requirements
                total_score += result['best_match']['match_score'] * 0.5
        
        return total_score / total_skills if total_skills > 0 else 0.0

# Global instance
skill_matcher = AdvancedSkillMatcher() 