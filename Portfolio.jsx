import React, { useState } from 'react'
import './Portfolio.css'

const skills = [
  { name: 'Project Management', level: 95, cat: 'management' },
  { name: 'Agile / Scrum', level: 92, cat: 'management' },
  { name: 'Stakeholder Communication', level: 90, cat: 'management' },
  { name: 'Risk Analysis', level: 85, cat: 'management' },
  { name: 'Python', level: 78, cat: 'tech' },
  { name: 'SQL / Databases', level: 82, cat: 'tech' },
  //{ name: 'Power BI / Tableau', level: 80, cat: 'tech' },
  //{ name: 'MS Project / Jira', level: 88, cat: 'tech' },
]

const projects = [
  {
    id: 1,
    tag: 'Web Development',
    title: 'Book Trip To Planets',
    desc: 'Led a team to build a futuristic space tourism booking website during the NASA Space Apps Challenge hackathon. Won the Best Use Of AI Tools award.',
    metrics: ['Best Use Of AI Tools', 'NASA Space Apps Challenge', '48-Hour Hackathon', 'Team: Exploranauts'],
    year: '2023',
    status: 'completed',
  },

  {
    id: 2,
    tag: 'Science Communication',
    title: 'Earth Magnetic Field Educational Video',
    desc: 'Led a team to create an educational video explaining Earth’s magnetic field for the NASA Space Apps Challenge. Received Best Use Of Science and Top 8 Ideas awards.',
    metrics: ['Best Use Of Science', 'Top 10 Ideas', 'NASA Space Apps Challenge', 'Team: Rise of Phoenix'],
    year: '2024',
    status: 'completed',
  },

  {
    id: 3,
    tag: 'Robotics',
    title: 'Obstacle Avoiding Robot',
    desc: 'Developed an autonomous obstacle avoiding robot using sensors and embedded systems as part of a robotics learning project.',
    metrics: ['Embedded Systems', 'Autonomous Navigation', 'Sensor Integration', 'ESP32 + Motor Driver'],
    year: '2024',
    status: 'active',
  },

  {
    id: 4,
    tag: 'IoT',
    title: 'Smart Plant Monitoring System',
    desc: 'Built an IoT-based plant monitoring system using sensors and ESP32 to monitor soil moisture and environmental conditions in real time.',
    metrics: ['ESP32', 'Sensor Integration', 'Real-Time Monitoring', 'IoT'],
    year: '2025',
    status: 'active',
  },
]

const awards = [
  {
    year: '2023',
    title: 'Best Use Of AI Tools',
    org: 'NASA Space Apps Challenge'
  },
  {
    year: '2024',
    title: 'Best Use Of Science and Top 10 Ideas',
    org: 'NASA Space Apps Challenge'
  },
  {
    year: '2023',
    title: 'South India Karate Championship - Bronze Medal (U18)',
    org: 'South India Karate Championship'
  }
];

export default function Portfolio() {
  const [activeFilter, setActiveFilter] = useState('all')

  const filtered = activeFilter === 'all'
    ? projects
    : projects.filter(p => p.status === activeFilter)

  return (
    <div className="portfolio-page">
      {/* Hero */}
      <section className="hero">
        <div className="hero-grid-bg" aria-hidden="true">
          {[...Array(120)].map((_, i) => <span key={i} className="grid-dot" />)}
        </div>
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-dot" />
            Available for New Projects
          </div>
          <h1 className="hero-title">
            <span className="title-line">Evangelina</span>
            <span className="title-line italic">Maria Jais</span>
          </h1>
          <div className="hero-role">
            <span>Chavarite 25'</span>
            <span className="role-sep">·</span>
            <span>NIT Calicut 29'</span>
            <span className="role-sep">·</span>
            <span>Sports Captian of Higher Secondary</span>
          </div>
          <p className="hero-bio">
           Passionate student and aspiring technology professional with interests in robotics, electronics,
           and software development.Experienced in teamwork, leadership, and innovation through NASA Space Apps
           Challenge participation and competitive achievements in karate.
          </p>
          <div className="hero-stats">
            <div className="stat"><div className="stat-num">2x</div><div className="stat-label">NASA Space Apps Finalist</div></div>
            <div className="stat-divider" />

            <div className="stat"><div className="stat-num">U18</div><div className="stat-label">Karate Bronze Medalist</div></div>
            <div className="stat-divider" />

            <div className="stat"><div className="stat-num">Robotics</div><div className="stat-label">Core Area of Interest</div></div>
            <div className="stat-divider" />

            <div className="stat"><div className="stat-num">EEE</div><div className="stat-label">Engineering & Innovation</div></div>
          </div>
          <div className="hero-actions">
            <a href="#projects" className="btn-primary">View Projects</a>
            <a href="/pm-vikas" className="btn-ghost">View PM Vikas Project</a>
            <a href="#contact" className="btn-ghost">Get in Touch</a>
          </div>
        </div>
        <div className="hero-aside">
          <div className="profile-frame">
            <div className="profile-avatar photo-ready">
              <img
                src="/profile-photo.jpg"
                alt="Evangelina Maria Jais"
                className="profile-photo"
                onError={(event) => {
                  event.currentTarget.style.display = 'none'
                  event.currentTarget.nextElementSibling.style.display = 'flex'
                }}
              />
              <div className="photo-placeholder">
                <span className="photo-initial">E</span>
                <span className="photo-hint">Add Photo</span>
              </div>
            </div>
            <div className="profile-tag"><span className="tag-dot" />Open to Opportunities</div>
          </div>
          <div className="profile-info">
            <div className="info-row"><span className="info-label">Location</span><span>Pala, Kerala</span></div>
            <div className="info-row"><span className="info-label">Field</span><span>EEE & Technology</span></div>
            <div className="info-row"><span className="info-label">Interests</span><span>Robotics, AI & Nanotechnology</span></div>
            <div className="info-row"><span className="info-label">Achievements</span><span>NASA Space Apps & Karate</span></div>
          </div>
        </div>
      </section>

      {/* Skills */}
      <section className="section" id="skills">
        <div className="section-header">
          <span className="section-tag">Skills & Technology</span>
          <h2 className="section-title">Core Competencies</h2>
        </div>
        <div className="skills-grid">
          {skills.map((s, i) => (
            <div key={i} className="skill-card" style={{ animationDelay: `${i * 0.07}s` }}>
              <div className="skill-top">
                <span className="skill-name">{s.name}</span>
                <span className="skill-pct">{s.level}%</span>
              </div>
              <div className="skill-bar">
                <div className="skill-fill" style={{ '--w': `${s.level}%`, '--color': s.cat === 'tech' ? 'var(--accent2)' : 'var(--accent)' }} />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Projects */}
      <section className="section" id="projects">
        <div className="section-header">
          <span className="section-tag">Work Portfolio</span>
          <h2 className="section-title">Featured Projects</h2>
        </div>
        <div className="filter-bar">
          {['all', 'active', 'completed'].map(f => (
            <button key={f} className={activeFilter === f ? 'filter-btn active' : 'filter-btn'} onClick={() => setActiveFilter(f)}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        <div className="projects-grid">
          {filtered.map((p, i) => (
            <div key={p.id} className={`project-card ${p.status}`} style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="project-head">
                <span className="project-tag">{p.tag}</span>
                <span className={`project-status ${p.status}`}>{p.status === 'active' ? '● Active' : '✓ Done'}</span>
              </div>
              <div className="project-year">{p.year}</div>
              <h3 className="project-title">{p.title}</h3>
              <p className="project-desc">{p.desc}</p>
              <div className="project-metrics">
                {p.metrics.map((m, j) => (
                  <span key={j} className="metric-chip">{m}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Awards */}
      <section className="section" id="awards">
        <div className="section-header">
          <span className="section-tag">Recognition</span>
          <h2 className="section-title">Awards & Honors</h2>
        </div>
        <div className="awards-list">
          {awards.map((a, i) => (
            <div key={i} className="award-row" style={{ animationDelay: `${i * 0.08}s` }}>
              <span className="award-year">{a.year}</span>
              <div className="award-bar" />
              <div className="award-body">
                <div className="award-title">{a.title}</div>
                <div className="award-org">{a.org}</div>
              </div>
              <span className="award-icon">★</span>
            </div>
          ))}
        </div>
      </section>

      {/* Contact */}
      <section className="section contact-section" id="contact">
        <div className="contact-inner">
          <span className="section-tag">Get In Touch</span>
          <h2 className="contact-title">Let's Build Something <em>Impactful</em></h2>
          <p className="contact-sub">Open to technology projects, innovation collaborations, and opportunities in robotics, AI, and electronics.</p>
          <div className="contact-links">
            <a href="mailto:evangelinatjais@gmail.com" className="contact-link">evangelinatjais@gmail.com</a>
            <span className="contact-sep">·</span>
            <a href="tel:+917907152494" className="contact-link">+91 7907152494</a>
            <span className="contact-sep">·</span>
            <a href="https://www.linkedin.com/in/evangelina-jais-440487355" className="contact-link" target="_blank" rel="noreferrer">LinkedIn</a>
          </div>
        </div>
      </section>
    </div>
  )
}
