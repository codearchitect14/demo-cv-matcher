# File: manual_test.py
"""
Manual testing script to interact with your implementation
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import AsyncSessionLocal
from services.candidate_service import CandidateService
from schemas.candidate import CandidateCreate, CandidateExperienceCreate, CandidateUpdate
from schemas.search import CandidateSearchFilter


async def interactive_test():
    """Interactive testing menu"""
    print("🔧 Manual Testing Interface")
    print("=" * 40)
    
    service = CandidateService()
    
    while True:
        print("\nChoose an option:")
        print("1. Create a candidate")
        print("2. Search candidates")
        print("3. Get candidate by ID")
        print("4. Add experience to candidate")
        print("5. Get candidate statistics")
        print("6. List all candidates")
        print("0. Exit")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            await create_candidate_interactive(service)
        elif choice == "2":
            await search_candidates_interactive(service)
        elif choice == "3":
            await get_candidate_interactive(service)
        elif choice == "4":
            await add_experience_interactive(service)
        elif choice == "5":
            await get_stats_interactive(service)
        elif choice == "6":
            await list_candidates_interactive(service)
        else:
            print("Invalid choice!")


async def create_candidate_interactive(service):
    """Interactive candidate creation"""
    async with AsyncSessionLocal() as session:
        try:
            print("\n--- Create New Candidate ---")
            name = input("Name: ")
            location = input("Location: ")
            domain = input("Domain: ")
            salary_min = input("Expected Salary Min (optional): ")
            salary_max = input("Expected Salary Max (optional): ")
            
            experiences = []
            while True:
                add_exp = input("Add experience? (y/n): ").lower()
                if add_exp != 'y':
                    break
                
                skill = input("Skill: ")
                years = int(input("Years of experience: "))
                description = input("Description (optional): ")
                
                experiences.append(CandidateExperienceCreate(
                    skill=skill,
                    years=years,
                    description=description if description else None
                ))
            
            candidate_data = CandidateCreate(
                name=name,
                location=location,
                domain=domain,
                expected_salary_min=int(salary_min) if salary_min else None,
                expected_salary_max=int(salary_max) if salary_max else None,
                experiences=experiences
            )
            
            candidate = await service.create_candidate(session, candidate_data)
            print(f"✅ Created candidate: {candidate.name} (ID: {candidate.id})")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def search_candidates_interactive(service):
    """Interactive candidate search"""
    async with AsyncSessionLocal() as session:
        try:
            print("\n--- Search Candidates ---")
            domain = input("Domain (optional): ")
            location = input("Location (optional): ")
            skills = input("Skills (comma-separated, optional): ")
            
            search_filter = CandidateSearchFilter(
                domain=domain if domain else None,
                location=location if location else None,
                skills=skills.split(",") if skills else []
            )
            
            results = await service.search_candidates(session, search_filter)
            print(f"\nFound {len(results)} candidates:")
            for candidate in results:
                print(f"- {candidate.name} ({candidate.domain}) - {candidate.location}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def get_candidate_interactive(service):
    """Get candidate by ID"""
    async with AsyncSessionLocal() as session:
        try:
            candidate_id = int(input("Enter candidate ID: "))
            candidate = await service.get_candidate(session, candidate_id)
            
            print(f"\n--- Candidate Details ---")
            print(f"Name: {candidate.name}")
            print(f"Location: {candidate.location}")
            print(f"Domain: {candidate.domain}")
            print(f"Salary Range: {candidate.expected_salary_min} - {candidate.expected_salary_max}")
            print("Experiences:")
            for exp in candidate.experiences:
                print(f"  - {exp.skill}: {exp.years} years")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def add_experience_interactive(service):
    """Add experience to candidate"""
    async with AsyncSessionLocal() as session:
        try:
            candidate_id = int(input("Enter candidate ID: "))
            skill = input("Skill: ")
            years = int(input("Years of experience: "))
            description = input("Description (optional): ")
            
            updated = await service.add_experience(
                session, candidate_id, skill, years, 
                description if description else None
            )
            print(f"✅ Added {skill} experience to {updated.name}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def get_stats_interactive(service):
    """Get candidate statistics"""
    async with AsyncSessionLocal() as session:
        try:
            candidate_id = int(input("Enter candidate ID: "))
            stats = await service.get_candidate_stats(session, candidate_id)
            
            print(f"\n--- Candidate Statistics ---")
            print(f"Total Skills: {stats['total_skills']}")
            print(f"Max Experience: {stats['max_experience_years']} years")
            print(f"Skills: {', '.join(stats['skills_list'])}")
            print(f"Total Applications: {stats['total_applications']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def list_candidates_interactive(service):
    """List all candidates"""
    async with AsyncSessionLocal() as session:
        try:
            candidates = await service.get_candidates(session, limit=20)
            print(f"\n--- All Candidates ({len(candidates)}) ---")
            for candidate in candidates:
                print(f"{candidate.id}. {candidate.name} ({candidate.domain}) - {candidate.location}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(interactive_test())