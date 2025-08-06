import React, { useState, useEffect } from 'react';

const TestJobs = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      console.log('🔄 TestJobs: Fetching jobs...');
      const response = await fetch('http://localhost:8000/api/v1/jobs/?skip=0&limit=5');
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ TestJobs: Data received:', data);
        setJobs(data);
      } else {
        console.error('❌ TestJobs: API error:', response.status);
      }
    } catch (err) {
      console.error('💥 TestJobs: Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>Test Jobs Component</h1>
      <p>Loading: {loading ? 'Yes' : 'No'}</p>
      <p>Jobs count: {jobs.length}</p>
      
      {jobs.length > 0 && (
        <div>
          <h2>Jobs Found:</h2>
          {jobs.map((job, index) => (
            <div key={job.id} style={{ 
              border: '1px solid #ccc', 
              padding: '10px', 
              margin: '10px 0',
              borderRadius: '5px'
            }}>
              <h3>{job.title || 'No Title'}</h3>
              <p><strong>Company:</strong> {job.company || 'No Company'}</p>
              <p><strong>Location:</strong> {job.location || 'No Location'}</p>
              <p><strong>Salary:</strong> ${job.salary_min || 0} - ${job.salary_max || 0}</p>
              <p><strong>Experience:</strong> {job.total_years_required || 0} years</p>
            </div>
          ))}
        </div>
      )}
      
      {jobs.length === 0 && !loading && (
        <p>No jobs found</p>
      )}
    </div>
  );
};

export default TestJobs; 