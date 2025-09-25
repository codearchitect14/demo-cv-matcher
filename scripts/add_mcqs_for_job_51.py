#!/usr/bin/env python3
"""
Add MCQs for job 51
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection_pool import global_pool

async def add_mcqs_for_job_51():
    """Add MCQs for job 51"""
    
    test_mcqs = [
        {
            "question": "What is React?",
            "options": {
                "A": "A JavaScript library for building user interfaces",
                "B": "A database management system", 
                "C": "A programming language",
                "D": "A web server"
            },
            "correct": "A"
        },
        {
            "question": "What is the purpose of useState in React?",
            "options": {
                "A": "To fetch data from APIs",
                "B": "To manage component state",
                "C": "To style components",
                "D": "To handle routing"
            },
            "correct": "B"
        },
        {
            "question": "What does JSX stand for?",
            "options": {
                "A": "JavaScript XML",
                "B": "Java Script Extension",
                "C": "JSON Syntax Extension",
                "D": "JavaScript Extension"
            },
            "correct": "A"
        },
        {
            "question": "What is the virtual DOM?",
            "options": {
                "A": "A real DOM element",
                "B": "A JavaScript representation of the DOM",
                "C": "A CSS framework",
                "D": "A database table"
            },
            "correct": "B"
        },
        {
            "question": "What is a React component?",
            "options": {
                "A": "A CSS file",
                "B": "A reusable piece of UI",
                "C": "A database query",
                "D": "A server endpoint"
            },
            "correct": "B"
        }
    ]
    
    try:
        job_id = 51
        
        # Clear existing MCQs for this job
        await global_pool.execute("DELETE FROM job_mcqs WHERE job_id = $1", job_id)
        
        # Insert new MCQs
        for i, mcq in enumerate(test_mcqs):
            await global_pool.execute("""
                INSERT INTO job_mcqs (job_id, question_number, question, option_a, option_b, option_c, option_d, correct_answer)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
                job_id, i + 1, mcq["question"], 
                mcq["options"]["A"], mcq["options"]["B"], mcq["options"]["C"], mcq["options"]["D"],
                mcq["correct"]
            )
        print(f"✅ Saved {len(test_mcqs)} MCQs to database for job {job_id}")
        
        # Verify
        mcqs_count = await global_pool.fetchval("SELECT COUNT(*) FROM job_mcqs WHERE job_id = $1", job_id)
        print(f"📊 MCQs for job {job_id}: {mcqs_count}")
        
        total_mcqs = await global_pool.fetchval("SELECT COUNT(*) FROM job_mcqs")
        print(f"📊 Total MCQs in database: {total_mcqs}")
        
    except Exception as e:
        print(f"❌ Error saving MCQs: {e}")

if __name__ == "__main__":
    asyncio.run(add_mcqs_for_job_51())
