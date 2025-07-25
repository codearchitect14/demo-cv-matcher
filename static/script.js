// --- Top Navigation Logic ---
const navLinks = document.querySelectorAll('.nav-link');
const sections = document.querySelectorAll('.section');

navLinks.forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    navLinks.forEach(l => l.classList.remove('active'));
    link.classList.add('active');
    const target = link.getAttribute('data-section');
    sections.forEach(sec => sec.classList.remove('active-section'));
    document.getElementById(target).classList.add('active-section');
    // If Find Jobs, render job list
    if (target === 'find-jobs') renderJobList();
    // If My Applications, render applications
    if (target === 'my-applications') renderApplicationsList();
  });
});

// --- Filter Panel Logic (for Find Jobs) ---
const industryCheckboxes = document.querySelectorAll('.industry-filter');
const distanceSlider = document.getElementById('distance-slider');
const distanceValue = document.getElementById('distance-value');
const salarySlider = document.getElementById('salary-slider');
const salaryValue = document.getElementById('salary-value');

if (distanceSlider) {
  distanceSlider.addEventListener('input', () => {
    distanceValue.textContent = `${distanceSlider.value} km`;
    renderJobList();
  });
}
if (salarySlider) {
  salarySlider.addEventListener('input', () => {
    salaryValue.textContent = `$${salarySlider.value}`;
    renderJobList();
  });
}
industryCheckboxes.forEach(cb => cb.addEventListener('change', renderJobList));

// --- Mock Data for Jobs ---
const jobs = [
  {
    id: 1,
    title: 'Server',
    company: 'Trio Ristorante',
    industry: 'Food & Beverage',
    pay: 13,
    distance: 2.1,
    expiry: '2 days, 8 hours',
    logo: 'TR',
    tags: ['Food & Beverage'],
    details: {
      employment: 'Part-Time',
      hourly: 13,
      start: 'June 5, 2024',
      commute: 10,
      address: '131 Sheppard St, North York, ON M5V 3Q7',
      responsibilities: [
        "Taking customers' food and drink orders in a timely manner",
        'General clean up duties',
        'Delivering food and drink orders to tables'
      ],
      requirements: [
        { label: 'Experience', value: '1 year' },
        { label: 'Languages', value: 'English' },
        { label: 'Certificates', value: 'Smart Serve' }
      ]
    }
  },
  {
    id: 2,
    title: 'Barback',
    company: 'The Spot',
    industry: 'Food & Beverage',
    pay: 14,
    distance: 1.1,
    expiry: '2 days, 21 hours',
    logo: 'Y',
    tags: ['Food & Beverage'],
    details: {
      employment: 'Part-Time',
      hourly: 14,
      start: 'June 5, 2024',
      commute: 10,
      address: '131 Sheppard St, North York, ON M5V 3Q7',
      responsibilities: [
        'Restocking bar supplies',
        'Assisting bartenders',
        'Cleaning bar area'
      ],
      requirements: [
        { label: 'Experience', value: '1 year' },
        { label: 'Languages', value: 'English' },
        { label: 'Certificates', value: 'Smart Serve' }
      ]
    }
  },
  {
    id: 3,
    title: 'Bakery Clerk',
    company: 'Butter Avenue',
    industry: 'Retail',
    pay: 15,
    distance: 2.8,
    expiry: '2 days, 14 hours',
    logo: 'BA',
    tags: ['Retail'],
    details: {
      employment: 'Full-Time',
      hourly: 15,
      start: 'June 10, 2024',
      commute: 15,
      address: '22 Main St, Toronto, ON',
      responsibilities: [
        'Serving customers',
        'Stocking shelves',
        'Maintaining cleanliness'
      ],
      requirements: [
        { label: 'Experience', value: '6 months' },
        { label: 'Languages', value: 'English' }
      ]
    }
  },
  {
    id: 4,
    title: 'Barista',
    company: 'Lit Espresso Bar',
    industry: 'Food & Beverage',
    pay: 15,
    distance: 3.6,
    expiry: '2 days, 1 hour',
    logo: 'LE',
    tags: ['Food & Beverage'],
    details: {
      employment: 'Part-Time',
      hourly: 15,
      start: 'June 7, 2024',
      commute: 12,
      address: '55 Coffee Ave, Toronto, ON',
      responsibilities: [
        'Making coffee drinks',
        'Customer service',
        'Cleaning work area'
      ],
      requirements: [
        { label: 'Experience', value: '1 year' },
        { label: 'Languages', value: 'English' }
      ]
    }
  },
  {
    id: 5,
    title: 'Cashier',
    company: 'Juice Lend',
    industry: 'Retail',
    pay: 15,
    distance: 4.2,
    expiry: '1 day, 6 hours',
    logo: 'GL',
    tags: ['Retail'],
    details: {
      employment: 'Part-Time',
      hourly: 15,
      start: 'June 8, 2024',
      commute: 15,
      address: '99 Market St, Toronto, ON',
      responsibilities: [
        'Operating cash register',
        'Customer service',
        'Balancing cash drawer'
      ],
      requirements: [
        { label: 'Experience', value: '6 months' },
        { label: 'Languages', value: 'English' }
      ]
    }
  }
];

let selectedJobId = null;

// --- Render Job List (for Find Jobs) ---
function renderJobList() {
  const selectedIndustries = Array.from(document.querySelectorAll('.industry-filter:checked')).map(cb => cb.value);
  const maxDistance = Number(distanceSlider.value);
  const minSalary = Number(salarySlider.value);
  const filtered = jobs.filter(job =>
    selectedIndustries.includes(job.industry) &&
    job.distance <= maxDistance &&
    job.pay >= minSalary
  );
  const jobList = document.getElementById('job-list');
  jobList.innerHTML = '';
  document.getElementById('job-count').textContent = `${filtered.length} Jobs`;
  if (!filtered.length) {
    jobList.innerHTML = '<div class="job-list-empty">No jobs match your filters.</div>';
    renderJobDetails(null);
    return;
  }
  filtered.forEach(job => {
    const card = document.createElement('div');
    card.className = 'job-card' + (job.id === selectedJobId ? ' selected' : '');
    card.innerHTML = `
      <div class="job-logo">${job.logo}</div>
      <div class="job-info">
        <div class="job-title">${job.title}</div>
        <div class="job-company">${job.company}</div>
        <div class="job-tags">${job.tags.map(tag => `<span class='job-tag'>${tag}</span>`).join('')}</div>
        <div class="job-meta">
          <span class="job-pay">$${job.pay}/hr</span>
          <span>${job.distance} km from you</span>
          <span class="job-expiry">Job expires in ${job.expiry}</span>
        </div>
      </div>
    `;
    card.addEventListener('click', () => {
      selectedJobId = job.id;
      renderJobList();
      renderJobDetails(job);
    });
    jobList.appendChild(card);
  });
  const selectedJob = filtered.find(j => j.id === selectedJobId) || filtered[0];
  if (selectedJob) {
    selectedJobId = selectedJob.id;
    renderJobDetails(selectedJob);
  } else {
    renderJobDetails(null);
  }
}

// --- Render Job Details (for Find Jobs) ---
function renderJobDetails(job) {
  const panel = document.getElementById('job-details-panel');
  if (!job) {
    panel.innerHTML = `<div class="job-details-placeholder">
      <i class="fa fa-briefcase fa-3x"></i>
      <p>Select a job to see details</p>
    </div>`;
    return;
  }
  panel.innerHTML = `
    <div class="job-details">
      <div class="job-details-header">
        <div class="job-details-logo">${job.logo}</div>
        <div>
          <div class="job-details-title">${job.title}</div>
          <div class="job-details-company">${job.company}</div>
          <div class="job-details-tags">${job.tags.map(tag => `<span class='job-details-tag'>${tag}</span>`).join('')}</div>
        </div>
      </div>
      <div class="job-details-meta">
        <span><i class="fa fa-clock"></i> ${job.details.employment}</span> |
        <span><i class="fa fa-dollar-sign"></i> $${job.details.hourly}/hr</span> |
        <span><i class="fa fa-calendar"></i> Start: ${job.details.start}</span>
      </div>
      <div class="job-details-meta">
        <span><i class="fa fa-map-marker-alt"></i> ${job.details.address}</span>
      </div>
      <div class="job-details-section">
        <div class="job-details-section-title">Responsibilities</div>
        <ul class="job-details-list">
          ${job.details.responsibilities.map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>
      <div class="job-details-section">
        <div class="job-details-section-title">Requirements</div>
        <div class="job-details-req">
          ${job.details.requirements.map(req => `<span>${req.label}: ${req.value}</span>`).join('')}
        </div>
      </div>
    </div>
  `;
}

// --- Mock Data for My Applications ---
const applications = [
  {
    id: 1,
    title: 'Interior & Graphic Designer',
    company: 'Alissat - Amman, Jordan',
    date: 'July 22, 2014',
    viewed: true,
    viewedCount: 167,
    cvRelevancy: 3,
    rank: 374,
    total: 936
  },
  {
    id: 2,
    title: 'Interior & Graphic Designer',
    company: 'Alissat - Amman, Jordan',
    date: 'July 22, 2014',
    viewed: true,
    viewedCount: 167,
    cvRelevancy: 3,
    rank: 605,
    total: 936
  },
  {
    id: 3,
    title: 'Interior & Graphic Designer',
    company: 'Alissat - Amman, Jordan',
    date: 'July 22, 2014',
    viewed: false,
    viewedCount: 167,
    cvRelevancy: 3,
    rank: 842,
    total: 936
  }
];

// --- Render Applications List (for My Applications) ---
function renderApplicationsList() {
  const container = document.getElementById('applications-list');
  container.innerHTML = '';
  applications.forEach(app => {
    const card = document.createElement('div');
    card.className = 'application-card';
    card.innerHTML = `
      <div class="app-main">
        <div class="app-title"><a href="#">${app.title}</a></div>
        <div class="app-company">${app.company}</div>
        <div class="app-meta">Date Applied: ${app.date} | Viewed Applications: ${app.viewedCount} | CV Relevancy: ${'★'.repeat(app.cvRelevancy)}</div>
        <div class="app-compare"><a href="#">Compare to Other Applicants.</a></div>
      </div>
      <div class="app-status">
        <div class="app-viewed">${app.viewed ? '<span class="viewed"><i class="fa fa-check-circle"></i> Application Viewed</span>' : '<span class="not-viewed"><i class="fa fa-times-circle"></i> Not Yet Viewed</span>'}</div>
        <div class="app-rank">${app.rank} / ${app.total}<br><span class="app-rank-label">My Rank</span></div>
        <button class="app-promote">Promote to Top</button>
      </div>
    `;
    container.appendChild(card);
  });
}

// --- Initial Render ---
document.addEventListener('DOMContentLoaded', () => {
  // Show Home section by default
  document.querySelectorAll('.section').forEach(sec => sec.classList.remove('active-section'));
  document.getElementById('home').classList.add('active-section');
  document.querySelector('.nav-link[data-section="home"]').classList.add('active');
}); 