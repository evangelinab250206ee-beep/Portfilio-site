import React, { useState } from 'react'
import './Insights.css'

const TRACKER_MODULES = [
  { name: 'Attendance Tracker', domain: 'Academics', launched: 'Core Module', goal: 'Track attended and total classes', metric: 'Low warning below 75%', coverage: 'Monthly and semester views' },
  { name: 'Projects Tracker', domain: 'Engineering Builds', launched: 'Kanban Module', goal: 'Manage demos, robotics builds, and web projects', metric: 'Progress, priority, deadline', coverage: 'Milestones and team members' },
  { name: 'Assignments Tracker', domain: 'Deadlines', launched: 'Task Module', goal: 'Sort work by subject, due date, and status', metric: 'Overdue alerts', coverage: 'Filters and calendar view' },
  { name: 'Blog Section', domain: 'Reflection', launched: 'Writing Module', goal: 'Publish project notes and learning logs', metric: 'Tags, likes, comments', coverage: 'Public and private posts' },
  { name: 'Dashboard', domain: 'Student OS', launched: 'Overview Module', goal: 'Show what needs attention now', metric: 'Charts and weekly stats', coverage: 'Activity, quotes, streaks' },
  { name: 'Focus Tools', domain: 'Productivity', launched: 'Study Module', goal: 'Use Pomodoro, reminders, and AI planning', metric: 'Streak and focus sessions', coverage: 'Daily engineering workflow' },
]

const TOOLS = [
  { name: 'React', cat: 'Frontend', rating: 4 },
  { name: 'Next.js', cat: 'Full Stack', rating: 4 },
  { name: 'TypeScript', cat: 'Code Quality', rating: 4 },
  { name: 'Tailwind CSS', cat: 'UI Design', rating: 5 },
  { name: 'Prisma', cat: 'Database', rating: 4 },
  { name: 'Supabase', cat: 'Backend', rating: 4 },
  { name: 'Python', cat: 'Automation', rating: 4 },
  { name: 'SQL', cat: 'Data', rating: 4 },
  { name: 'GitHub', cat: 'Version Control', rating: 5 },
  { name: 'Figma', cat: 'Design', rating: 3 },
  { name: 'Arduino / ESP32', cat: 'Electronics', rating: 4 },
  { name: 'Notion', cat: 'Planning', rating: 5 },
]

export default function Insights() {
  const [tab, setTab] = useState('schemes')

  return (
    <div className="insights-page">
      <div className="insights-header">
        <span className="insights-eyebrow">Interactive Hub</span>
        <h1 className="insights-title">Engineering Student Insights</h1>
        <p className="insights-sub">Explore the study habits, tracker modules, and tools behind the PM Vikas productivity system.</p>
      </div>

      <div className="tab-bar">
        {['schemes', 'tools'].map(t => (
          <button key={t} className={tab === t ? 'tab active' : 'tab'} onClick={() => setTab(t)}>
            {t === 'schemes' ? 'PM Vikas Modules' : 'Engineering Tools'}
          </button>
        ))}
      </div>

      {tab === 'schemes' && (
        <div className="schemes-grid">
          {TRACKER_MODULES.map((s, i) => (
            <div key={i} className="scheme-card" style={{ animationDelay: `${i * 0.07}s` }}>
              <div className="scheme-domain">{s.domain}</div>
              <h3 className="scheme-name">{s.name}</h3>
              <div className="scheme-year">{s.launched}</div>
              <div className="scheme-rows">
                <div className="scheme-row"><span className="sr-label">Goal</span><span>{s.goal}</span></div>
                <div className="scheme-row"><span className="sr-label">Signal</span><span className="sr-val-accent">{s.metric}</span></div>
                <div className="scheme-row"><span className="sr-label">Coverage</span><span>{s.coverage}</span></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'tools' && (
        <div className="tools-section">
          <p className="tools-intro">A practical engineering-student stack for building the portfolio, PM Vikas Tracker, robotics projects, and learning logs.</p>
          <div className="tools-grid">
            {TOOLS.map((t, i) => (
              <div key={i} className="tool-card" style={{ animationDelay: `${i * 0.04}s` }}>
                <div className="tool-head">
                  <span className="tool-name">{t.name}</span>
                  <span className="tool-cat">{t.cat}</span>
                </div>
                <div className="tool-stars">
                  {[...Array(5)].map((_, j) => (
                    <span key={j} className={j < t.rating ? 'star on' : 'star'}>*</span>
                  ))}
                </div>
                <div className="tool-bar">
                  <div style={{ width: `${(t.rating / 5) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
