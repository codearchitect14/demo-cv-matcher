def filter_jobs_by_criteria(jobs, candidate):
    return [
        job for job in jobs
        if job["location"] == candidate["location"] and
           job["domain"] == candidate["domain"]
    ]
