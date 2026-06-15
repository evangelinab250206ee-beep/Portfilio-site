import React from 'react'
import './Insights.css'
import { formatDate, useTrackerSnapshot } from './trackerData.js'

const StatCard = ({ label, value, detail, tone = 'normal' }) => (
  <div className={`insight-card ${tone}`}>
    <span className="insight-label">{label}</span>
    <strong className="insight-value">{value}</strong>
    <span className="insight-detail">{detail}</span>
  </div>
)

export default function Insights() {
  const { stats, portfolio } = useTrackerSnapshot()
  const portfolioUpdates = [
    { type: 'Portfolio', title: `${portfolio.projects.length} portfolio projects`, detail: 'Project showcase' },
    { type: 'Portfolio', title: `${portfolio.photos.length} gallery photos`, detail: 'Gallery' },
    { type: 'Portfolio', title: `${portfolio.certifications.length} certifications`, detail: 'CMS' },
  ]

  return (
    <div className="insights-page">
      <div className="insights-header">
        <span className="insights-eyebrow">PM Vikas Live Insights</span>
        <h1 className="insights-title">Tracker Overview</h1>
        <p className="insights-sub">Attendance, assignments, projects, blog activity, and portfolio changes update from the shared PM Vikas data.</p>
      </div>

      <div className="insight-stats-grid">
        <StatCard label="Attendance Percentage" value={`${stats.attendance}%`} detail={`${stats.attendedClasses}/${stats.totalClasses} classes attended`} tone={stats.attendance < 75 ? 'danger' : 'good'} />
        <StatCard label="Total Attended Classes" value={stats.attendedClasses} detail="Across all PM Vikas courses" />
        <StatCard label="Missed Classes" value={stats.missedClasses} detail="Classes marked missed" tone={stats.missedClasses ? 'danger' : 'good'} />
        <StatCard label="Pending Assignments" value={stats.pendingAssignments} detail={`${stats.overdueAssignments} overdue`} tone={stats.overdueAssignments ? 'danger' : 'normal'} />
        <StatCard label="Completed Projects" value={stats.completedProjects} detail={`${stats.activeProjects} active projects`} tone="good" />
        <StatCard label="Recent Updates" value={stats.recentActivity.length + portfolioUpdates.length} detail="Blog, activity, and portfolio updates" />
      </div>

      <div className="insight-panel-grid">
        <section className="insight-panel">
          <div className="panel-heading">
            <span className="insights-eyebrow">Warnings</span>
            <h2>Needs Attention</h2>
          </div>
          <div className="warning-list">
            {stats.warnings.length ? (
              stats.warnings.map((warning) => <div className="warning-item" key={warning}>{warning}</div>)
            ) : (
              <div className="good-item">No PM Vikas warnings right now.</div>
            )}
          </div>
        </section>

        <section className="insight-panel">
          <div className="panel-heading">
            <span className="insights-eyebrow">Attendance</span>
            <h2>Course Breakdown</h2>
          </div>
          <div className="course-insight-list">
            {stats.courseBreakdown.map((course) => (
              <div className="course-insight-row" key={course.id}>
                <div>
                  <strong>{course.name}</strong>
                  <span>{course.stats.attended} attended / {course.stats.missed} missed</span>
                </div>
                <b className={course.stats.percent < course.target ? 'danger-text' : 'good-text'}>{course.stats.percent}%</b>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="insight-panel activity-panel">
        <div className="panel-heading">
          <span className="insights-eyebrow">Recent Blog / Activity Updates</span>
          <h2>Latest Signals</h2>
        </div>
        <div className="activity-insight-list">
          {[...stats.recentActivity, ...portfolioUpdates].map((item, index) => (
            <div className="activity-insight-item" key={`${item.type}-${item.title}-${index}`}>
              <span>{item.type}</span>
              <strong>{item.title}</strong>
              <em>{item.date ? formatDate(item.date) : item.detail}</em>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
