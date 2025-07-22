def update_preferences(user_id, job_id, feedback):
    # Store feedback for ML training (e.g., in DB or flat file)
    print(f"Feedback received: User {user_id} - Job {job_id} - {feedback}")
