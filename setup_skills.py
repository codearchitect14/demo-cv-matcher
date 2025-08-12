import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import AsyncSessionLocal
from models import Skill, JobSkill, CandidateSkill  # Import all models to ensure they're registered

# Initial skill taxonomy data
SKILLS_DATA = [
    # Programming Languages
    {"name": "Python", "category": "programming", "description": "High-level programming language", "aliases": '["py", "python3"]'},
    {"name": "JavaScript", "category": "programming", "description": "Web programming language", "aliases": '["js", "ecmascript"]'},
    {"name": "Java", "category": "programming", "description": "Object-oriented programming language", "aliases": '["jdk"]'},
    {"name": "C++", "category": "programming", "description": "System programming language", "aliases": '["cpp"]'},
    {"name": "C#", "category": "programming", "description": "Microsoft programming language", "aliases": '["csharp"]'},
    {"name": "Go", "category": "programming", "description": "Google programming language", "aliases": '["golang"]'},
    {"name": "Rust", "category": "programming", "description": "Systems programming language", "aliases": '["rustlang"]'},
    {"name": "TypeScript", "category": "programming", "description": "Typed JavaScript", "aliases": '["ts"]'},
    {"name": "PHP", "category": "programming", "description": "Web development language", "aliases": '["php"]'},
    {"name": "Ruby", "category": "programming", "description": "Dynamic programming language", "aliases": '["ruby"]'},
    
    # Databases
    {"name": "SQL", "category": "database", "description": "Structured Query Language", "aliases": '["sql"]'},
    {"name": "PostgreSQL", "category": "database", "description": "Advanced open source database", "aliases": '["postgres", "psql"]'},
    {"name": "MySQL", "category": "database", "description": "Open source relational database", "aliases": '["mysql"]'},
    {"name": "MongoDB", "category": "database", "description": "NoSQL document database", "aliases": '["mongo"]'},
    {"name": "Redis", "category": "database", "description": "In-memory data structure store", "aliases": '["redis"]'},
    {"name": "Oracle", "category": "database", "description": "Enterprise database system", "aliases": '["oracle"]'},
    {"name": "SQLite", "category": "database", "description": "Lightweight database", "aliases": '["sqlite"]'},
    
    # Frameworks
    {"name": "React", "category": "framework", "description": "JavaScript UI library", "aliases": '["reactjs", "react.js"]'},
    {"name": "Vue.js", "category": "framework", "description": "Progressive JavaScript framework", "aliases": '["vue", "vuejs"]'},
    {"name": "Angular", "category": "framework", "description": "Google's web framework", "aliases": '["angularjs"]'},
    {"name": "Django", "category": "framework", "description": "Python web framework", "aliases": '["django"]'},
    {"name": "Flask", "category": "framework", "description": "Lightweight Python web framework", "aliases": '["flask"]'},
    {"name": "Spring", "category": "framework", "description": "Java application framework", "aliases": '["springboot", "spring-boot"]'},
    {"name": "Express.js", "category": "framework", "description": "Node.js web framework", "aliases": '["express", "expressjs"]'},
    {"name": "Laravel", "category": "framework", "description": "PHP web framework", "aliases": '["laravel"]'},
    {"name": "Ruby on Rails", "category": "framework", "description": "Ruby web framework", "aliases": '["rails", "ror"]'},
    
    # Cloud & DevOps
    {"name": "AWS", "category": "cloud", "description": "Amazon Web Services", "aliases": '["amazon", "amazon-web-services"]'},
    {"name": "Azure", "category": "cloud", "description": "Microsoft Cloud Platform", "aliases": '["microsoft-azure"]'},
    {"name": "Google Cloud", "category": "cloud", "description": "Google Cloud Platform", "aliases": '["gcp", "google-cloud-platform"]'},
    {"name": "Docker", "category": "devops", "description": "Containerization platform", "aliases": '["docker"]'},
    {"name": "Kubernetes", "category": "devops", "description": "Container orchestration", "aliases": '["k8s", "kube"]'},
    {"name": "Jenkins", "category": "devops", "description": "CI/CD automation server", "aliases": '["jenkins"]'},
    {"name": "Git", "category": "devops", "description": "Version control system", "aliases": '["git"]'},
    {"name": "Terraform", "category": "devops", "description": "Infrastructure as Code", "aliases": '["terraform"]'},
    
    # Data Science & ML
    {"name": "TensorFlow", "category": "ml", "description": "Machine learning framework", "aliases": '["tensorflow"]'},
    {"name": "PyTorch", "category": "ml", "description": "Deep learning framework", "aliases": '["pytorch"]'},
    {"name": "Scikit-learn", "category": "ml", "description": "Machine learning library", "aliases": '["sklearn"]'},
    {"name": "Pandas", "category": "data", "description": "Data manipulation library", "aliases": '["pandas"]'},
    {"name": "NumPy", "category": "data", "description": "Numerical computing library", "aliases": '["numpy"]'},
    {"name": "Matplotlib", "category": "data", "description": "Data visualization library", "aliases": '["matplotlib"]'},
    {"name": "Jupyter", "category": "data", "description": "Interactive computing platform", "aliases": '["jupyter-notebook"]'},
    
    # Web Technologies
    {"name": "HTML", "category": "web", "description": "Hypertext Markup Language", "aliases": '["html5"]'},
    {"name": "CSS", "category": "web", "description": "Cascading Style Sheets", "aliases": '["css3"]'},
    {"name": "Node.js", "category": "web", "description": "JavaScript runtime", "aliases": '["node", "nodejs"]'},
    {"name": "REST API", "category": "web", "description": "Representational State Transfer", "aliases": '["rest", "api"]'},
    {"name": "GraphQL", "category": "web", "description": "Query language for APIs", "aliases": '["graphql"]'},
    
    # Soft Skills
    {"name": "Leadership", "category": "soft_skills", "description": "Team leadership and management", "aliases": '["lead", "management"]'},
    {"name": "Communication", "category": "soft_skills", "description": "Effective communication skills", "aliases": '["communication"]'},
    {"name": "Problem Solving", "category": "soft_skills", "description": "Analytical problem solving", "aliases": '["problem-solving", "analytical"]'},
    {"name": "Teamwork", "category": "soft_skills", "description": "Collaboration and team work", "aliases": '["collaboration", "team"]'},
    {"name": "Agile", "category": "soft_skills", "description": "Agile methodology", "aliases": '["scrum", "kanban"]'},
]

async def setup_skills():
    """Populate the skills table with initial data"""
    async with AsyncSessionLocal() as session:
        try:
            print("Setting up skills taxonomy...")
            
            # Check if skills already exist
            from sqlalchemy import select
            result = await session.execute(select(Skill))
            existing_skills = result.scalars().all()
            
            if existing_skills:
                print(f"Found {len(existing_skills)} existing skills. Skipping setup.")
                return
            
            # Create skills
            for skill_data in SKILLS_DATA:
                skill = Skill(**skill_data)
                session.add(skill)
            
            await session.commit()
            print(f"✅ Successfully created {len(SKILLS_DATA)} skills!")
            
            # Verify creation
            result = await session.execute(select(Skill))
            skills = result.scalars().all()
            print(f"Total skills in database: {len(skills)}")
            
        except Exception as e:
            print(f"❌ Error setting up skills: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(setup_skills()) 