import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import AsyncSessionLocal
from services.enhanced_recommendation_service import EnhancedRecommendationService
from services.enhanced_cv_parser import EnhancedCVParser
from services.skill_matcher import skill_matcher
from db.crud import candidate, job, skill, job_skill, candidate_skill

async def test_enhanced_recommendation_system():
    """Test the enhanced recommendation system"""
    print("🧪 Testing Enhanced Recommendation System")
    print("=" * 50)
    
    # Initialize services
    recommendation_service = EnhancedRecommendationService()
    cv_parser = EnhancedCVParser()
    # skill_matcher is already imported as a global instance
    
    async with AsyncSessionLocal() as session:
        try:
            # Test 1: Skill Matching
            print("\n1️⃣ Testing Skill Matching...")
            test_skills = ["Python", "JavaScript", "React", "AWS", "Docker"]
            for skill_name in test_skills:
                matches = skill_matcher.find_skill_matches(skill_name, threshold=0.3)
                print(f"   {skill_name}: {len(matches)} matches found")
                if matches:
                    print(f"      Top match: {matches[0][0]} (score: {matches[0][1]:.2f})")
            
            # Test 2: Skill Normalization
            print("\n2️⃣ Testing Skill Normalization...")
            test_aliases = ["py", "js", "reactjs", "amazon", "docker"]
            for alias in test_aliases:
                normalized = skill_matcher.normalize_skill_name(alias)
                print(f"   '{alias}' → '{normalized}'")
            
            # Test 3: Create Test Data
            print("\n3️⃣ Creating Test Data...")
            
            # Create test skills
            test_skill_data = [
                {"name": "Python", "category": "programming", "description": "High-level programming language"},
                {"name": "React", "category": "framework", "description": "JavaScript UI library"},
                {"name": "AWS", "category": "cloud", "description": "Amazon Web Services"},
                {"name": "Docker", "category": "devops", "description": "Containerization platform"},
                {"name": "PostgreSQL", "category": "database", "description": "Advanced open source database"}
            ]
            
            created_skills = []
            for skill_data in test_skill_data:
                db_skill = await skill.get_by_name(session, skill_data['name'])
                if not db_skill:
                    db_skill = await skill.create(session, obj_in=skill_data)
                created_skills.append(db_skill)
                print(f"   ✅ Created skill: {db_skill.name}")
            
            # Create test candidate
            candidate_data = {
                "name": "John Doe",
                "email": "john.doe@test.com",
                "phone": "+1234567890",
                "location": "New York, NY",
                "total_years_experience": 5.0
            }
            
            test_candidate = await candidate.create(session, obj_in=candidate_data)
            print(f"   ✅ Created candidate: {test_candidate.name}")
            
            # Create candidate skills
            candidate_skill_data = [
                {"skill_id": created_skills[0].id, "years_experience": 3.0, "proficiency_level": "advanced"},
                {"skill_id": created_skills[1].id, "years_experience": 2.5, "proficiency_level": "intermediate"},
                {"skill_id": created_skills[2].id, "years_experience": 1.5, "proficiency_level": "intermediate"},
                {"skill_id": created_skills[3].id, "years_experience": 1.0, "proficiency_level": "beginner"}
            ]
            
            for skill_data in candidate_skill_data:
                skill_data["candidate_id"] = test_candidate.id
                await candidate_skill.create(session, obj_in=skill_data)
            
            print(f"   ✅ Created {len(candidate_skill_data)} candidate skills")
            
            # Create test job
            job_data = {
                "title": "Senior Python Developer",
                "company": "Tech Corp",
                "location": "New York, NY",
                "salary_min": 80000,
                "salary_max": 120000,
                "domain": "IT",
                "total_years_required": 3,
                "job_description": "We are looking for a senior Python developer with React experience."
            }
            
            test_job = await job.create(session, obj_in=job_data)
            print(f"   ✅ Created job: {test_job.title}")
            
            # Create job skill requirements
            job_skill_data = [
                {"skill_id": created_skills[0].id, "min_years_experience": 3.0, "priority": "required"},
                {"skill_id": created_skills[1].id, "min_years_experience": 2.0, "priority": "required"},
                {"skill_id": created_skills[2].id, "min_years_experience": 1.0, "priority": "preferred"},
                {"skill_id": created_skills[4].id, "min_years_experience": 1.0, "priority": "nice_to_have"}
            ]
            
            for skill_data in job_skill_data:
                skill_data["job_id"] = test_job.id
                await job_skill.create(session, obj_in=skill_data)
            
            print(f"   ✅ Created {len(job_skill_data)} job skill requirements")
            
            # Test 4: Enhanced Recommendations
            print("\n4️⃣ Testing Enhanced Recommendations...")
            
            # Get candidate recommendations
            candidate_recommendations = await recommendation_service.get_candidate_job_recommendations(
                db=session,
                candidate_id=test_candidate.id,
                limit=5,
                include_explanation=True
            )
            
            print(f"   📊 Found {len(candidate_recommendations)} candidate recommendations")
            for rec in candidate_recommendations:
                print(f"      Job {rec.job_id}: {rec.overall_match_score:.2f} match score")
                print(f"         Explanation: {rec.explanation}")
                print(f"         Skill matches: {len([sm for sm in rec.skill_matches if sm.meets_requirement])}")
                print(f"         Missing skills: {len(rec.missing_skills)}")
                print(f"         Experience gaps: {len(rec.experience_gaps)}")
                print(f"         Strengths: {len(rec.strengths)}")
            
            # Get recruiter recommendations
            recruiter_recommendations = await recommendation_service.get_recruiter_candidate_recommendations(
                db=session,
                job_id=test_job.id,
                limit=5,
                include_explanation=True
            )
            
            print(f"   📊 Found {len(recruiter_recommendations)} recruiter recommendations")
            for rec in recruiter_recommendations:
                print(f"      Candidate {rec.candidate_id}: {rec.overall_match_score:.2f} match score")
                print(f"         Explanation: {rec.explanation}")
                print(f"         Skill matches: {len([sm for sm in rec.skill_matches if sm.meets_requirement])}")
                print(f"         Missing skills: {len(rec.missing_skills)}")
                print(f"         Experience gaps: {len(rec.experience_gaps)}")
                print(f"         Strengths: {len(rec.strengths)}")
            
            # Test 5: Skill Validation
            print("\n5️⃣ Testing Skill Validation...")
            
            # Get candidate and job with skills
            candidate_with_skills = await candidate.get_with_skills(session, test_candidate.id)
            job_with_skills = await job.get_with_skills(session, test_job.id)
            
            if candidate_with_skills and job_with_skills:
                validation_results = skill_matcher.validate_skill_requirements(
                    job_with_skills['skills'],
                    candidate_with_skills['skills']
                )
                
                print(f"   📋 Skill validation results:")
                for skill_name, result in validation_results.items():
                    status = "✅" if result['meets_requirement'] else "❌"
                    print(f"      {status} {skill_name}: {result['candidate_years']}/{result['required_years']} years")
                
                overall_score = skill_matcher.calculate_overall_match_score(validation_results)
                print(f"   📊 Overall match score: {overall_score:.2f}")
            
            print("\n✅ Enhanced Recommendation System Test Completed Successfully!")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(test_enhanced_recommendation_system()) 