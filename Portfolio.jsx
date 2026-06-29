import React, { useState } from 'react'
import './Portfolio.css'
import { readFiles, usePortfolioData } from './trackerData.js'

const listToText = (items, mapItem) => items.map(mapItem).join('\n')
const splitLines = (value) => value.split('\n').map((item) => item.trim()).filter(Boolean)

export default function Portfolio() {
  const [activeFilter, setActiveFilter] = useState('all')
  const [portfolio, setPortfolio] = usePortfolioData()
  const [cmsOpen, setCmsOpen] = useState(false)
  const [draft, setDraft] = useState(portfolio)

  const filtered = activeFilter === 'all'
    ? portfolio.projects
    : portfolio.projects.filter(p => p.status === activeFilter)

  const savePortfolio = (event) => {
    event.preventDefault()
    setPortfolio(draft)
    setCmsOpen(false)
  }

  const uploadPhotos = async (files) => {
    const photos = await readFiles(files, 'image')
    setPortfolio((current) => ({ ...current, photos: [...current.photos, ...photos] }))
    setDraft((current) => ({ ...current, photos: [...current.photos, ...photos] }))
  }

  const uploadProfilePhoto = async (files) => {
    const photos = await readFiles(files, 'image')
    if (!photos.length) return
    setPortfolio((current) => ({ ...current, photos: [photos[0], ...current.photos] }))
    setDraft((current) => ({ ...current, photos: [photos[0], ...current.photos] }))
  }

  const updateDraftFromText = (field, value, parser) => {
    setDraft((current) => ({ ...current, [field]: parser(value) }))
  }

  return (
    <div className="portfolio-page">
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
            {portfolio.name.split(' ').slice(0, 2).map((part) => <span className="title-line" key={part}>{part}</span>)}
            <span className="title-line italic">{portfolio.name.split(' ').slice(2).join(' ') || portfolio.name}</span>
          </h1>
          <div className="hero-role">
            {portfolio.role.split('|').map((item, index) => (
              <React.Fragment key={item}>
                {index > 0 && <span className="role-sep">|</span>}
                <span>{item.trim()}</span>
              </React.Fragment>
            ))}
          </div>
          <p className="hero-bio">{portfolio.bio}</p>
          <div className="hero-stats">
            <div className="stat"><div className="stat-num">{portfolio.projects.length}</div><div className="stat-label">Projects</div></div>
            <div className="stat-divider" />
            <div className="stat"><div className="stat-num">{portfolio.awards.length}</div><div className="stat-label">Awards</div></div>
            <div className="stat-divider" />
            <div className="stat"><div className="stat-num">{portfolio.photos.length}</div><div className="stat-label">Photos</div></div>
            <div className="stat-divider" />
            <div className="stat"><div className="stat-num">{portfolio.certifications.length}</div><div className="stat-label">Certifications</div></div>
          </div>
          <div className="hero-actions">
            <a href="#projects" className="btn-primary">View Projects</a>
            <button className="btn-ghost" type="button" onClick={() => { setDraft(portfolio); setCmsOpen(true) }}>Manage Portfolio</button>
            <a href="/pm-vikas" className="btn-ghost">View PM Vikas Project</a>
          </div>
        </div>
        <div className="hero-aside">
          <div className="profile-frame">
            <label className="profile-avatar photo-ready profile-upload-box">
              {portfolio.photos[0] ? (
                <img src={portfolio.photos[0].dataUrl} alt={portfolio.name} className="profile-photo" />
              ) : (
                <>
                  <img
                    src="/profile-photo.jpg"
                    alt={portfolio.name}
                    className="profile-photo"
                    onError={(event) => {
                      event.currentTarget.style.display = 'none'
                      event.currentTarget.nextElementSibling.style.display = 'flex'
                    }}
                  />
                  <div className="photo-placeholder">
                    <span className="photo-initial">{portfolio.name.charAt(0)}</span>
                    <span className="photo-hint">Add Photo</span>
                  </div>
                </>
              )}
              <input type="file" accept="image/*" onChange={(event) => uploadProfilePhoto(event.target.files)} />
              <span className="profile-upload-action">Change Photo</span>
            </label>
            <div className="profile-tag"><span className="tag-dot" />Open to Opportunities</div>
          </div>
          <div className="profile-info">
            <div className="info-row"><span className="info-label">Location</span><span>{portfolio.location}</span></div>
            <div className="info-row"><span className="info-label">Field</span><span>{portfolio.field}</span></div>
            <div className="info-row"><span className="info-label">Interests</span><span>{portfolio.interests}</span></div>
            <div className="info-row"><span className="info-label">Achievements</span><span>{portfolio.awards.length} awards</span></div>
          </div>
        </div>
      </section>

      <section className="section" id="skills">
        <div className="section-header">
          <span className="section-tag">Skills & Technology</span>
          <h2 className="section-title">Core Competencies</h2>
        </div>
        <div className="skills-grid">
          {portfolio.skills.map((s, i) => (
            <div key={`${s.name}-${i}`} className="skill-card" style={{ animationDelay: `${i * 0.07}s` }}>
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
                <span className={`project-status ${p.status}`}>{p.status === 'active' ? 'Active' : 'Done'}</span>
              </div>
              <div className="project-year">{p.year}</div>
              <h3 className="project-title">{p.title}</h3>
              <p className="project-desc">{p.desc}</p>
              <div className="project-metrics">
                {p.metrics.map((m, j) => <span key={j} className="metric-chip">{m}</span>)}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="section" id="awards">
        <div className="section-header">
          <span className="section-tag">Recognition</span>
          <h2 className="section-title">Awards & Honors</h2>
        </div>
        <div className="awards-list">
          {portfolio.awards.map((a, i) => (
            <div key={`${a.title}-${i}`} className="award-row" style={{ animationDelay: `${i * 0.08}s` }}>
              <span className="award-year">{a.year}</span>
              <div className="award-bar" />
              <div className="award-body">
                <div className="award-title">{a.title}</div>
                <div className="award-org">{a.org}</div>
              </div>
              <span className="award-icon">*</span>
            </div>
          ))}
        </div>
      </section>

      <section className="section contact-section" id="contact">
        <div className="contact-inner">
          <span className="section-tag">Get In Touch</span>
          <h2 className="contact-title">Let's Build Something <em>Impactful</em></h2>
          <p className="contact-sub">Open to technology projects, innovation collaborations, and opportunities in robotics, AI, and electronics.</p>
          <div className="contact-links">
            {portfolio.socialLinks.map((link, index) => (
              <React.Fragment key={link.url}>
                {index > 0 && <span className="contact-sep">|</span>}
                <a href={link.url} className="contact-link" target={link.url.startsWith('http') ? '_blank' : undefined} rel="noreferrer">{link.label}</a>
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {cmsOpen && (
        <div className="portfolio-modal-backdrop" onClick={() => setCmsOpen(false)}>
          <div className="portfolio-cms-panel" role="dialog" aria-modal="true" aria-labelledby="portfolio-cms-title" onClick={(event) => event.stopPropagation()}>
            <div className="cms-head">
              <div>
                <span className="section-tag">CMS Mode</span>
                <h2 id="portfolio-cms-title">Manage Portfolio</h2>
              </div>
              <button type="button" onClick={() => setCmsOpen(false)}>Close</button>
            </div>
            <form className="cms-form" onSubmit={savePortfolio}>
              <input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} placeholder="Name" />
              <textarea value={draft.bio} onChange={(e) => setDraft({ ...draft, bio: e.target.value })} placeholder="Bio" />
              <input value={draft.role} onChange={(e) => setDraft({ ...draft, role: e.target.value })} placeholder="Role line, separate with |" />
              <input value={draft.location} onChange={(e) => setDraft({ ...draft, location: e.target.value })} placeholder="Location" />
              <input value={draft.field} onChange={(e) => setDraft({ ...draft, field: e.target.value })} placeholder="Field" />
              <input value={draft.interests} onChange={(e) => setDraft({ ...draft, interests: e.target.value })} placeholder="Interests" />
              <label>Skills
                <textarea value={listToText(draft.skills, (s) => `${s.name}|${s.level}|${s.cat}`)} onChange={(e) => updateDraftFromText('skills', e.target.value, (value) => splitLines(value).map((line, index) => {
                  const [name, level = '80', cat = 'tech'] = line.split('|')
                  return { name, level: Number(level) || 80, cat, id: index + 1 }
                }))} />
              </label>
              <label>Projects
                <textarea value={listToText(draft.projects, (p) => `${p.title}|${p.tag}|${p.year}|${p.status}|${p.desc}|${p.metrics.join(', ')}`)} onChange={(e) => updateDraftFromText('projects', e.target.value, (value) => splitLines(value).map((line, index) => {
                  const [title, tag = 'Project', year = '', status = 'active', desc = '', metrics = ''] = line.split('|')
                  return { id: index + 1, title, tag, year, status, desc, metrics: metrics.split(',').map((item) => item.trim()).filter(Boolean) }
                }))} />
              </label>
              <label>Awards
                <textarea value={listToText(draft.awards, (a) => `${a.year}|${a.title}|${a.org}`)} onChange={(e) => updateDraftFromText('awards', e.target.value, (value) => splitLines(value).map((line) => {
                  const [year, title, org = ''] = line.split('|')
                  return { year, title, org }
                }))} />
              </label>
              <label>Social links
                <textarea value={listToText(draft.socialLinks, (s) => `${s.label}|${s.url}`)} onChange={(e) => updateDraftFromText('socialLinks', e.target.value, (value) => splitLines(value).map((line) => {
                  const [label, url = '#'] = line.split('|')
                  return { label, url }
                }))} />
              </label>
              <label>Certifications
                <textarea value={listToText(draft.certifications, (c) => `${c.title}|${c.issuer}|${c.year}`)} onChange={(e) => updateDraftFromText('certifications', e.target.value, (value) => splitLines(value).map((line, index) => {
                  const [title, issuer = '', year = ''] = line.split('|')
                  return { id: index + 1, title, issuer, year }
                }))} />
              </label>
              <label className="gallery-upload cms-upload">
                Add Photos
                <input type="file" accept="image/*" multiple onChange={(event) => uploadPhotos(event.target.files)} />
              </label>
              <button className="btn-primary" type="submit">Save Portfolio</button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
