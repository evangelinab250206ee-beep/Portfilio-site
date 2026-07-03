'use client';

import React, { useEffect, useState } from 'react';
import './PMVikas.css';
import {
  downloadPMVikasChanges,
  isRemoteSyncConfigured,
  uploadPMVikasChanges,
  usePMVikasData,
} from './trackerData.js';

const QUOTES = [
  'Small progress still counts.',
  'Track the work, then trust the work.',
  'A finished draft beats a perfect idea.',
  'Show up today. Future you will notice.',
];

const DEFAULT_PIN = '2468';

const SAMPLE_COURSES = [
  {
    id: 1,
    name: 'Data Structures',
    code: 'CS201',
    faculty: 'Prof. Meera',
    schedule: 'Mon, Wed, Fri',
    room: 'Lab 2',
    startDate: '2026-05-01',
    endDate: '2026-06-30',
    classDays: 3,
    target: 75,
    classes: [
      { id: 101, date: '2026-05-04', topic: 'Trees', attended: true },
      { id: 102, date: '2026-05-06', topic: 'Binary search tree', attended: true },
      { id: 103, date: '2026-05-08', topic: 'AVL basics', attended: false },
    ],
  },
  {
    id: 2,
    name: 'Web Development',
    code: 'WD204',
    faculty: 'Prof. Arun',
    schedule: 'Tue, Thu',
    room: 'Studio 1',
    startDate: '2026-05-01',
    endDate: '2026-06-30',
    classDays: 2,
    target: 75,
    classes: [
      { id: 201, date: '2026-05-05', topic: 'React state', attended: true },
      { id: 202, date: '2026-05-07', topic: 'Routing', attended: true },
    ],
  },
];

const SAMPLE_PROJECTS = [
  {
    id: 1,
    title: 'E-Commerce Platform',
    description: 'Full-stack shopping app with cart, checkout, and admin views.',
    deadline: '2026-06-30',
    status: 'in-progress',
    priority: 'high',
    progress: 65,
    gitLink: 'https://github.com/',
    liveLink: '',
    notes: 'Payment flow and deployment are the next focus.',
    photos: [],
    milestones: [
      { id: 1, title: 'Backend API', completed: true },
      { id: 2, title: 'Product pages', completed: true },
      { id: 3, title: 'Payment integration', completed: false },
    ],
  },
  {
    id: 2,
    title: 'AI Chatbot',
    description: 'NLP assistant for student FAQs.',
    deadline: '2026-07-15',
    status: 'not-started',
    priority: 'medium',
    progress: 0,
    gitLink: '',
    liveLink: '',
    notes: '',
    photos: [],
    milestones: [],
  },
];

const SAMPLE_ASSIGNMENTS = [
  {
    id: 1,
    subject: 'Data Structures',
    title: 'Binary Search Tree Implementation',
    dueDate: '2026-06-15',
    priority: 'high',
    status: 'in-progress',
    notes: 'Include insert, delete, traversal, and screenshots.',
    documents: [],
  },
  {
    id: 2,
    subject: 'Web Development',
    title: 'React Components Project',
    dueDate: '2026-06-20',
    priority: 'medium',
    status: 'pending',
    notes: 'Reusable UI component set.',
    documents: [],
  },
];

const SAMPLE_BLOG_POSTS = [
  {
    id: 1,
    title: 'My Journey Learning React',
    details: 'React changed how I think about user interfaces and reusable design.',
    category: 'Web Development',
    tags: ['React', 'Learning'],
    date: '2026-05-01',
    visibility: 'public',
    comments: [
      { id: 1, text: 'Add screenshots and project links after the next update.', date: '2026-05-02' },
    ],
  },
];

const Card = ({ children, className = '', ...props }) => (
  <div className={`card glass-morphism ${className}`} {...props}>
    {children}
  </div>
);

const StatCard = ({ icon, label, value, color }) => (
  <Card className="stat-card">
    <div className="stat-card-icon" style={{ color }}>{icon}</div>
    <div className="stat-card-content">
      <div className="stat-card-label">{label}</div>
      <div className="stat-card-value">{value}</div>
    </div>
  </Card>
);

const readFiles = (fileList, acceptType = 'any') => {
  const files = Array.from(fileList || []);
  const filtered = files.filter((file) => {
    if (acceptType === 'image') return file.type.startsWith('image/');
    return true;
  });

  return Promise.all(
    filtered.map(
      (file) =>
        new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () =>
            resolve({
              id: Date.now() + Math.random(),
              name: file.name,
              path: file.webkitRelativePath || file.name,
              type: file.type || 'application/octet-stream',
              size: file.size,
              dataUrl: reader.result,
            });
          reader.onerror = reject;
          reader.readAsDataURL(file);
        })
    )
  );
};

const getStored = (key, fallback) => {
  try {
    const saved = localStorage.getItem(key);
    return saved ? JSON.parse(saved) : fallback;
  } catch {
    return fallback;
  }
};

const formatDate = (date) =>
  new Date(`${date}T00:00:00`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

const localDateKey = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const isImageUpload = (file) =>
  file?.type?.startsWith('image/') || /\.(png|jpe?g|webp|gif|avif)$/i.test(file?.name || '');

const fileExtension = (fileName) => {
  const extension = fileName?.split('.').pop();
  return extension && extension !== fileName ? extension.toUpperCase() : 'FILE';
};

const PREVIEWABLE_EXTENSIONS = new Set([
  'TXT', 'MD', 'CSV', 'JSON', 'JS', 'JSX', 'TS', 'TSX', 'HTML', 'CSS', 'SCSS',
  'PY', 'JAVA', 'C', 'CPP', 'CS', 'PHP', 'RB', 'GO', 'RS', 'SQL', 'XML', 'YAML',
  'YML', 'ENV', 'SH', 'BAT', 'PS1', 'LOG',
]);

const canPreviewFile = (file) =>
  file?.type?.startsWith('text/') ||
  file?.type === 'application/json' ||
  PREVIEWABLE_EXTENSIONS.has(fileExtension(file?.name));

const readDataUrlText = (dataUrl) => {
  const [, payload = ''] = dataUrl.split(',');
  try {
    return decodeURIComponent(
      atob(payload)
        .split('')
        .map((char) => `%${char.charCodeAt(0).toString(16).padStart(2, '0')}`)
        .join('')
    );
  } catch {
    try {
      return atob(payload);
    } catch {
      return 'Preview is not available for this file.';
    }
  }
};

const startOfMonth = (date) => new Date(date.getFullYear(), date.getMonth(), 1);
const endOfMonth = (date) => new Date(date.getFullYear(), date.getMonth() + 1, 0);

const buildCalendarDays = (monthDate) => {
  const first = startOfMonth(monthDate);
  const last = endOfMonth(monthDate);
  const days = [];

  for (let i = 0; i < first.getDay(); i += 1) {
    days.push(null);
  }

  for (let day = 1; day <= last.getDate(); day += 1) {
    days.push(new Date(monthDate.getFullYear(), monthDate.getMonth(), day));
  }

  return days;
};

const courseStats = (course) => {
  const total = course.classes.length;
  const attended = course.classes.filter((item) => item.attended).length;
  const missed = total - attended;
  return {
    total,
    attended,
    missed,
    percent: total ? Math.round((attended / total) * 100) : 0,
  };
};

const normalizeCourse = (course) => ({
  startDate: '',
  endDate: '',
  classDays: '',
  ...course,
  classes: Array.isArray(course.classes) ? course.classes : [],
});

const normalizeBlogPost = (post) => ({
  category: 'General',
  details: post.details || post.content || '',
  tags: [],
  visibility: 'private',
  ...post,
  comments: Array.isArray(post.comments) ? post.comments : [],
});

function SecurityPanel({ canEdit, onUnlock, onLock, onChangePin }) {
  const [pin, setPin] = useState('');
  const [newPin, setNewPin] = useState('');

  return (
    <Card className="security-panel">
      <div>
        <span className={`lock-badge ${canEdit ? 'open' : ''}`}>{canEdit ? 'Edit mode on' : 'Locked'}</span>
        <p className="security-copy">
          Owner editing is protected on this browser. Default PIN is 2468 until you change it.
        </p>
      </div>
      <div className="security-actions">
        {!canEdit ? (
          <>
            <input
              className="mini-input"
              type="password"
              placeholder="Owner PIN"
              value={pin}
              onChange={(event) => setPin(event.target.value)}
            />
            <button
              className="primary-btn"
              type="button"
              onClick={() => {
                if (onUnlock(pin)) {
                  setPin('');
                }
              }}
            >
              Unlock
            </button>
          </>
        ) : (
          <>
            <input
              className="mini-input"
              type="password"
              placeholder="New PIN"
              value={newPin}
              onChange={(event) => setNewPin(event.target.value)}
            />
            <button
              className="action-btn"
              type="button"
              onClick={() => {
                if (onChangePin(newPin)) {
                  setPin('');
                  setNewPin('');
                }
              }}
            >
              Change PIN
            </button>
            <button
              className="delete-btn"
              type="button"
              onClick={() => {
                setNewPin('');
                onLock();
              }}
            >
              Lock
            </button>
          </>
        )}
      </div>
    </Card>
  );
}

function CloudSyncPanel({ enabled, syncing, onUpload, onDownload }) {
  return (
    <Card className="cloud-sync-panel">
      <div>
        <span className={`lock-badge ${enabled ? 'open' : ''}`}>{enabled ? 'Cloud sync on' : 'Cloud sync off'}</span>
        <p className="security-copy">
          {enabled
            ? 'Upload this device after edits, or get latest changes made on another device.'
            : 'Add Supabase environment variables in Vercel to sync changes across devices.'}
        </p>
      </div>
      <div className="security-actions">
        <button className="action-btn" type="button" onClick={onDownload} disabled={!enabled || syncing}>
          Get Latest
        </button>
        <button className="primary-btn" type="button" onClick={onUpload} disabled={!enabled || syncing}>
          {syncing ? 'Syncing' : 'Upload This Device'}
        </button>
      </div>
    </Card>
  );
}

function AttendanceTracker({ courses, setCourses, canEdit, notify }) {
  const [selectedCourseId, setSelectedCourseId] = useState(courses[0]?.id || null);
  const [monthDate, setMonthDate] = useState(new Date());
  const [courseForm, setCourseForm] = useState(null);
  const [classForm, setClassForm] = useState({ date: '', topic: '', attended: true });
  const [editingClass, setEditingClass] = useState(null);
  const [attendanceSearch, setAttendanceSearch] = useState('');
  const [showAllRecords, setShowAllRecords] = useState(false);

  const selectedCourse = courses.find((course) => course.id === selectedCourseId) || courses[0];
  const stats = selectedCourse ? courseStats(selectedCourse) : { total: 0, attended: 0, percent: 0 };
  const days = buildCalendarDays(monthDate);
  const monthLabel = monthDate.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
  const monthKey = `${monthDate.getFullYear()}-${String(monthDate.getMonth() + 1).padStart(2, '0')}`;
  const monthRecords = selectedCourse?.classes.filter((item) => item.date.startsWith(monthKey)) || [];
  const monthAttended = monthRecords.filter((item) => item.attended).length;
  const monthMissed = monthRecords.length - monthAttended;
  const monthPercent = monthRecords.length ? Math.round((monthAttended / monthRecords.length) * 100) : 0;
  const filteredRecords = (selectedCourse?.classes || [])
    .filter((item) => item.date.startsWith(monthKey))
    .filter((item) => item.topic.toLowerCase().includes(attendanceSearch.toLowerCase()))
    .slice()
    .sort((a, b) => b.date.localeCompare(a.date));
  const visibleRecords = showAllRecords ? filteredRecords : filteredRecords.slice(0, 5);

  useEffect(() => {
    if (!selectedCourseId && courses[0]) setSelectedCourseId(courses[0].id);
  }, [courses, selectedCourseId]);

  const updateSelectedCourse = (patch) => {
    if (!selectedCourse) return;
    setCourses((currentCourses) =>
      currentCourses.map((course) => (course.id === selectedCourse.id ? { ...course, ...patch } : course))
    );
  };

  const saveCourse = (event) => {
    event.preventDefault();
    if (!canEdit || !courseForm?.name?.trim()) return;

    const savedCourse = normalizeCourse({
      ...courseForm,
      name: courseForm.name.trim(),
      code: courseForm.code.trim(),
      faculty: courseForm.faculty.trim(),
      schedule: courseForm.schedule.trim(),
      room: courseForm.room.trim(),
      target: Number(courseForm.target) || 75,
    });

    if (courseForm.id) {
      setCourses((currentCourses) =>
        currentCourses.map((course) => (course.id === courseForm.id ? { ...course, ...savedCourse } : course))
      );
      setSelectedCourseId(courseForm.id);
      notify('Course details updated.');
    } else {
      const newCourse = { ...savedCourse, id: Date.now(), classes: [] };
      setCourses((currentCourses) => [...currentCourses, newCourse]);
      setSelectedCourseId(newCourse.id);
      notify('Course added.');
    }
    setCourseForm(null);
  };

  const addClass = (event) => {
    event.preventDefault();
    if (!selectedCourse || !classForm.date) return;

    updateSelectedCourse({
      classes: [
        ...selectedCourse.classes,
        { id: Date.now(), date: classForm.date, topic: classForm.topic || 'Class attended', attended: classForm.attended },
      ],
    });
    setClassForm({ date: '', topic: '', attended: true });
    notify('Class added to calendar.');
  };

  const saveEditedClass = (event) => {
    event.preventDefault();
    if (!selectedCourse || !editingClass?.date) return;

    updateSelectedCourse({
      classes: selectedCourse.classes.map((item) =>
        item.id === editingClass.id
          ? {
              ...item,
              date: editingClass.date,
              topic: editingClass.topic || 'Class attended',
              attended: editingClass.attended,
            }
          : item
      ),
    });
    setEditingClass(null);
    notify('Attendance entry updated.');
  };

  const toggleClass = (classId) => {
    updateSelectedCourse({
      classes: selectedCourse.classes.map((item) =>
        item.id === classId ? { ...item, attended: !item.attended } : item
      ),
    });
  };

  const deleteClass = (classId) => {
    updateSelectedCourse({
      classes: selectedCourse.classes.filter((item) => item.id !== classId),
    });
    notify('Class removed.');
  };

  const deleteCourse = () => {
    if (!selectedCourse) return;
    const remainingCourses = courses.filter((course) => course.id !== selectedCourse.id);
    setCourses(remainingCourses);
    setSelectedCourseId(remainingCourses[0]?.id || null);
    setCourseForm(null);
    notify('Course deleted.');
  };

  return (
    <section className="tab-section">
      <div className="section-heading-row">
        <h2 className="section-title">Attendance Tracker</h2>
        {canEdit && (
          <div className="section-button-group">
            <button
              className="primary-btn"
              type="button"
              onClick={() =>
                setCourseForm({
                  id: null,
                  name: '',
                  code: '',
                  faculty: '',
                  schedule: '',
                  room: '',
                  startDate: '',
                  endDate: '',
                  classDays: '',
                  target: 75,
                  classes: [],
                })
              }
            >
              Add Course
            </button>
            <button
              className="action-btn"
              type="button"
              onClick={() => setClassForm({ date: localDateKey(new Date()), topic: '', attended: true })}
            >
              Add Attendance
            </button>
          </div>
        )}
      </div>

      {courseForm && (
        <Card className="editor-card">
          <form className="editor-grid" onSubmit={saveCourse}>
            <input value={courseForm.name} onChange={(e) => setCourseForm({ ...courseForm, name: e.target.value })} placeholder="Course name" />
            <input value={courseForm.code} onChange={(e) => setCourseForm({ ...courseForm, code: e.target.value })} placeholder="Course code" />
            <input value={courseForm.faculty} onChange={(e) => setCourseForm({ ...courseForm, faculty: e.target.value })} placeholder="Faculty" />
            <input value={courseForm.schedule} onChange={(e) => setCourseForm({ ...courseForm, schedule: e.target.value })} placeholder="Schedule" />
            <input value={courseForm.room} onChange={(e) => setCourseForm({ ...courseForm, room: e.target.value })} placeholder="Room" />
            <label className="field-with-label">
              No. of class days
              <input type="number" min="0" value={courseForm.classDays || ''} onChange={(e) => setCourseForm({ ...courseForm, classDays: e.target.value ? Number(e.target.value) : '' })} placeholder="Example: 3" />
            </label>
            <label className="field-with-label">
              From
              <input type="date" value={courseForm.startDate || ''} onChange={(e) => setCourseForm({ ...courseForm, startDate: e.target.value })} />
            </label>
            <label className="field-with-label">
              To
              <input type="date" value={courseForm.endDate || ''} onChange={(e) => setCourseForm({ ...courseForm, endDate: e.target.value })} />
            </label>
            <input type="number" value={courseForm.target} onChange={(e) => setCourseForm({ ...courseForm, target: Number(e.target.value) })} placeholder="Target %" />
            <div className="form-actions">
              <button className="primary-btn" type="submit">Save Course</button>
              <button className="action-btn" type="button" onClick={() => setCourseForm(null)}>Cancel</button>
            </div>
          </form>
        </Card>
      )}

      {selectedCourse && (
        <>
          <div className="course-topbar">
            <div className="course-tabs">
              {courses.map((course) => (
                <button
                  key={course.id}
                  className={`course-tab ${selectedCourse.id === course.id ? 'active' : ''}`}
                  type="button"
                  onClick={() => setSelectedCourseId(course.id)}
                >
                  {course.name}
                </button>
              ))}
            </div>
            <div className="course-summary">
              <strong>{selectedCourse.code || 'Course'}</strong>
              <span>{selectedCourse.faculty || 'Faculty not set'}</span>
              <span>{selectedCourse.schedule || 'Schedule not set'}</span>
              <span>{selectedCourse.room || 'Room not set'}</span>
              <span>{selectedCourse.classDays || 'Class days not set'} class days</span>
              <span>
                {selectedCourse.startDate ? formatDate(selectedCourse.startDate) : 'Start not set'} to{' '}
                {selectedCourse.endDate ? formatDate(selectedCourse.endDate) : 'End not set'}
              </span>
              <span>{stats.attended}/{stats.total} attended</span>
              <span className={stats.percent < selectedCourse.target ? 'risk-text' : 'good-text'}>
                {stats.percent}% / {selectedCourse.target}% target
              </span>
              {canEdit && (
                <div className="record-actions">
                  <button className="action-btn" type="button" onClick={() => setCourseForm(selectedCourse)}>
                    Edit Details
                  </button>
                  <button className="delete-btn" type="button" onClick={deleteCourse}>
                    Delete Course
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="attendance-layout">
            <Card className="calendar-card">
              <div className="calendar-toolbar">
                <button className="action-btn" type="button" onClick={() => setMonthDate(new Date(monthDate.getFullYear(), monthDate.getMonth() - 1, 1))}>Prev</button>
                <h3>{monthLabel}</h3>
                <button className="action-btn" type="button" onClick={() => setMonthDate(new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 1))}>Next</button>
              </div>
              <div className="calendar-weekdays">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => <span key={day}>{day}</span>)}
              </div>
              <div className="calendar-grid">
                {days.map((day, index) => {
                  const dateKey = day ? localDateKey(day) : '';
                  const classes = selectedCourse.classes.filter((item) => item.date === dateKey);
                  return (
                    <div key={`${dateKey}-${index}`} className={`calendar-day ${!day ? 'empty' : ''}`}>
                      {day && <span className="day-number">{day.getDate()}</span>}
                      {classes.map((item) => (
                        <button
                          key={item.id}
                          type="button"
                          className={`class-chip ${item.attended ? 'attended' : 'missed'}`}
                          onClick={() => canEdit && toggleClass(item.id)}
                          title={canEdit ? 'Click to toggle attended/missed' : item.topic}
                        >
                          {item.topic}
                        </button>
                      ))}
                    </div>
                  );
                })}
              </div>
            </Card>

            <Card className="side-editor-card">
              <h3 className="card-title">Monthly Summary</h3>
              <div className="attendance-month-controls">
                <label className="field-with-label">
                  Filter by month
                  <input
                    type="month"
                    value={monthKey}
                    onChange={(e) => {
                      const [year, month] = e.target.value.split('-').map(Number);
                      if (year && month) setMonthDate(new Date(year, month - 1, 1));
                    }}
                  />
                </label>
                <input
                  value={attendanceSearch}
                  onChange={(e) => setAttendanceSearch(e.target.value)}
                  placeholder="Search by subject or title"
                />
              </div>
              <div className="attendance-summary-cards">
                <div><strong>{monthPercent}%</strong><span>Attendance</span></div>
                <div><strong>{monthAttended}</strong><span>Attended</span></div>
                <div><strong>{monthMissed}</strong><span>Missed</span></div>
              </div>
              {canEdit && (
                <form className="stack-form" onSubmit={addClass}>
                  <input type="date" value={classForm.date} onChange={(e) => setClassForm({ ...classForm, date: e.target.value })} />
                  <input value={classForm.topic} onChange={(e) => setClassForm({ ...classForm, topic: e.target.value })} placeholder="Title / subject name" />
                  <select value={classForm.attended ? 'attended' : 'missed'} onChange={(e) => setClassForm({ ...classForm, attended: e.target.value === 'attended' })}>
                    <option value="attended">Attended</option>
                    <option value="missed">Missed</option>
                  </select>
                  <button className="primary-btn" type="submit">Add Attendance</button>
                </form>
              )}
              <div className="log-list">
                {visibleRecords
                  .map((item) => (
                    <div className="log-item" key={item.id}>
                      <div>
                        <strong>{formatDate(item.date)}</strong>
                        <span>{item.topic}</span>
                      </div>
                      <span className={item.attended ? 'good-text' : 'risk-text'}>{item.attended ? 'Attended' : 'Missed'}</span>
                      {canEdit && (
                        <div className="record-actions">
                          <button className="action-btn" type="button" onClick={() => setEditingClass(item)}>Edit</button>
                          <button className="delete-btn" type="button" onClick={() => deleteClass(item.id)}>Delete</button>
                        </div>
                      )}
                    </div>
                  ))}
                {!visibleRecords.length && <p className="empty-state">No attendance records for this month.</p>}
              </div>
              {filteredRecords.length > 5 && (
                <button className="action-btn view-all-btn" type="button" onClick={() => setShowAllRecords(!showAllRecords)}>
                  {showAllRecords ? 'Show Recent 5' : 'View All'}
                </button>
              )}
            </Card>
          </div>
        </>
      )}

      {editingClass && (
        <div className="edit-modal-backdrop" onClick={() => setEditingClass(null)}>
          <Card className="edit-modal-card" role="dialog" aria-modal="true" aria-labelledby="edit-attendance-title" onClick={(event) => event.stopPropagation()}>
            <h3 id="edit-attendance-title" className="card-title">Edit Attendance</h3>
            <form className="stack-form" onSubmit={saveEditedClass}>
              <input type="date" value={editingClass.date} onChange={(e) => setEditingClass({ ...editingClass, date: e.target.value })} />
              <input value={editingClass.topic} onChange={(e) => setEditingClass({ ...editingClass, topic: e.target.value })} placeholder="Title / subject name" />
              <select value={editingClass.attended ? 'attended' : 'missed'} onChange={(e) => setEditingClass({ ...editingClass, attended: e.target.value === 'attended' })}>
                <option value="attended">Attended</option>
                <option value="missed">Missed</option>
              </select>
              <div className="form-actions">
                <button className="primary-btn" type="submit">Save</button>
                <button className="action-btn" type="button" onClick={() => setEditingClass(null)}>Cancel</button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </section>
  );
}

function ProjectTracker({ projects, setProjects, canEdit, notify }) {
  const [selectedId, setSelectedId] = useState(projects[0]?.id || null);
  const [draft, setDraft] = useState(null);
  const selectedProject = projects.find((project) => project.id === selectedId) || projects[0];

  useEffect(() => {
    if (!selectedId && projects[0]) setSelectedId(projects[0].id);
  }, [projects, selectedId]);

  const saveProject = (event) => {
    event.preventDefault();
    if (!draft.title.trim()) return;

    if (draft.id) {
      setProjects(projects.map((project) => (project.id === draft.id ? draft : project)));
      setSelectedId(draft.id);
      notify('Project updated.');
    } else {
      const newProject = { ...draft, id: Date.now(), photos: [], milestones: [] };
      setProjects([...projects, newProject]);
      setSelectedId(newProject.id);
      notify('Project added.');
    }
    setDraft(null);
  };

  const deleteProject = (id) => {
    setProjects(projects.filter((project) => project.id !== id));
    setSelectedId(projects.find((project) => project.id !== id)?.id || null);
    notify('Project deleted.');
  };

  const uploadPhotos = async (files, input) => {
    if (!selectedProject) return;
    const uploads = await readFiles(files, 'image');
    if (!uploads.length) return;
    setProjects(
      projects.map((project) =>
        project.id === selectedProject.id ? { ...project, photos: [...project.photos, ...uploads] } : project
      )
    );
    if (input) input.value = '';
    notify(`${uploads.length} photo${uploads.length === 1 ? '' : 's'} uploaded.`);
  };

  const removePhoto = (photoId) => {
    setProjects(
      projects.map((project) =>
        project.id === selectedProject.id
          ? { ...project, photos: project.photos.filter((photo) => photo.id !== photoId) }
          : project
      )
    );
  };

  return (
    <section className="tab-section">
      <div className="section-heading-row">
        <h2 className="section-title">Projects Tracker</h2>
        {canEdit && (
          <button
            className="primary-btn"
            type="button"
            onClick={() =>
              setDraft({
                id: null,
                title: '',
                description: '',
                deadline: '',
                status: 'not-started',
                priority: 'medium',
                progress: 0,
                gitLink: '',
                liveLink: '',
                notes: '',
                photos: [],
                milestones: [],
              })
            }
          >
            New Project
          </button>
        )}
      </div>

      {draft && (
        <Card className="editor-card">
          <form className="editor-grid" onSubmit={saveProject}>
            <input value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} placeholder="Project title" />
            <input value={draft.deadline} onChange={(e) => setDraft({ ...draft, deadline: e.target.value })} type="date" />
            <select value={draft.status} onChange={(e) => setDraft({ ...draft, status: e.target.value })}>
              <option value="not-started">Not started</option>
              <option value="in-progress">In progress</option>
              <option value="completed">Completed</option>
            </select>
            <select value={draft.priority} onChange={(e) => setDraft({ ...draft, priority: e.target.value })}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
            <input type="number" min="0" max="100" value={draft.progress} onChange={(e) => setDraft({ ...draft, progress: Number(e.target.value) })} placeholder="Progress" />
            <input value={draft.gitLink} onChange={(e) => setDraft({ ...draft, gitLink: e.target.value })} placeholder="GitHub or project link" />
            <input value={draft.liveLink} onChange={(e) => setDraft({ ...draft, liveLink: e.target.value })} placeholder="Live demo link" />
            <textarea value={draft.description} onChange={(e) => setDraft({ ...draft, description: e.target.value })} placeholder="Description" />
            <textarea value={draft.notes} onChange={(e) => setDraft({ ...draft, notes: e.target.value })} placeholder="Notes" />
            <div className="form-actions">
              <button className="primary-btn" type="submit">Save Project</button>
              <button className="action-btn" type="button" onClick={() => setDraft(null)}>Cancel</button>
            </div>
          </form>
        </Card>
      )}

      <div className="project-workspace">
        <div className="kanban-board compact">
          {['not-started', 'in-progress', 'completed'].map((status) => (
            <div className="kanban-column" key={status}>
              <h3 className="kanban-title">{status.replace('-', ' ')}</h3>
              <div className="kanban-cards">
                {projects
                  .filter((project) => project.status === status)
                  .map((project) => (
                    <Card
                      key={project.id}
                      className={`project-card ${selectedProject?.id === project.id ? 'selected' : ''}`}
                      onClick={() => setSelectedId(project.id)}
                    >
                      <div className="project-thumb-row">
                        {project.photos[0] ? <img src={project.photos[0].dataUrl} alt="" /> : <div className="photo-placeholder">No photo</div>}
                        <div>
                          <h3 className="project-title">{project.title}</h3>
                          <p className="project-description">{project.description}</p>
                        </div>
                      </div>
                      <div className="progress-label">
                        <span>{project.priority}</span>
                        <span>{project.progress}%</span>
                      </div>
                      <div className="progress-bar"><div className="progress-fill" style={{ width: `${project.progress}%` }} /></div>
                    </Card>
                  ))}
              </div>
            </div>
          ))}
        </div>

        {selectedProject && (
          <Card className="project-detail-panel">
            <div className="detail-header">
              <div>
                <span className="lock-badge open">{selectedProject.status}</span>
                <h3>{selectedProject.title}</h3>
              </div>
              {canEdit && (
                <div className="record-actions">
                  <button className="action-btn" type="button" onClick={() => setDraft(selectedProject)}>Edit</button>
                  <button className="delete-btn" type="button" onClick={() => deleteProject(selectedProject.id)}>Delete</button>
                </div>
              )}
            </div>
            <p>{selectedProject.description}</p>
            <div className="detail-meta">
              <span>Deadline: {selectedProject.deadline ? formatDate(selectedProject.deadline) : 'Not set'}</span>
              <span>Priority: {selectedProject.priority}</span>
              <span>Progress: {selectedProject.progress}%</span>
            </div>
            <div className="link-row">
              {selectedProject.gitLink && <a href={selectedProject.gitLink} target="_blank" rel="noreferrer">Open Git/Project Link</a>}
              {selectedProject.liveLink && <a href={selectedProject.liveLink} target="_blank" rel="noreferrer">Open Live Demo</a>}
            </div>
            {selectedProject.notes && <p className="detail-notes">{selectedProject.notes}</p>}
            {canEdit && (
              <label className="upload-box">
                Upload project photos
                <input type="file" accept="image/*" multiple onChange={(e) => uploadPhotos(e.target.files, e.target)} />
              </label>
            )}
            <div className="photo-grid">
              {selectedProject.photos.map((photo) => (
                <div className="photo-item" key={photo.id}>
                  <div className="post-topline">
                    <span>{selectedProject.title}</span>
                    <a href={photo.dataUrl} download={photo.name}>Download</a>
                  </div>
                  <img src={photo.dataUrl} alt={photo.name} />
                  <div className="post-caption">
                    <strong>{photo.name}</strong>
                    <span>{Math.round((photo.size || 0) / 1024)} KB</span>
                  </div>
                  {canEdit && <button className="delete-btn" type="button" onClick={() => removePhoto(photo.id)}>Remove</button>}
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </section>
  );
}

function AssignmentTracker({ assignments, setAssignments, canEdit, notify, searchQuery }) {
  const [draft, setDraft] = useState(null);
  const [previewFile, setPreviewFile] = useState(null);

  const saveAssignment = (event) => {
    event.preventDefault();
    if (!draft.title.trim()) return;

    if (draft.id) {
      setAssignments(assignments.map((assignment) => (assignment.id === draft.id ? draft : assignment)));
      notify('Assignment updated.');
    } else {
      setAssignments([...assignments, { ...draft, id: Date.now(), documents: [] }]);
      notify('Assignment added.');
    }
    setDraft(null);
  };

  const uploadDocuments = async (assignmentId, files, input) => {
    const uploads = await readFiles(files);
    if (!uploads.length) return;
    setAssignments(
      assignments.map((assignment) =>
        assignment.id === assignmentId
          ? { ...assignment, documents: [...assignment.documents, ...uploads] }
          : assignment
      )
    );
    if (input) input.value = '';
    notify(`${uploads.length} file${uploads.length === 1 ? '' : 's'} uploaded.`);
  };

  const removeDocument = (assignmentId, docId) => {
    setAssignments(
      assignments.map((assignment) =>
        assignment.id === assignmentId
          ? { ...assignment, documents: assignment.documents.filter((doc) => doc.id !== docId) }
          : assignment
      )
    );
  };

  const filteredAssignments = assignments.filter(
    (assignment) =>
      !searchQuery ||
      assignment.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      assignment.subject.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <section className="tab-section">
      <div className="section-heading-row">
        <h2 className="section-title">Assignments Tracker</h2>
        {canEdit && (
          <button
            className="primary-btn"
            type="button"
            onClick={() =>
              setDraft({
                id: null,
                subject: '',
                title: '',
                dueDate: '',
                priority: 'medium',
                status: 'pending',
                notes: '',
                documents: [],
              })
            }
          >
            Add Assignment
          </button>
        )}
      </div>

      {draft && (
        <Card className="editor-card">
          <form className="editor-grid" onSubmit={saveAssignment}>
            <input value={draft.subject} onChange={(e) => setDraft({ ...draft, subject: e.target.value })} placeholder="Subject" />
            <input value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} placeholder="Assignment title" />
            <input type="date" value={draft.dueDate} onChange={(e) => setDraft({ ...draft, dueDate: e.target.value })} />
            <select value={draft.priority} onChange={(e) => setDraft({ ...draft, priority: e.target.value })}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
            <select value={draft.status} onChange={(e) => setDraft({ ...draft, status: e.target.value })}>
              <option value="pending">Pending</option>
              <option value="in-progress">In progress</option>
              <option value="submitted">Submitted</option>
            </select>
            <textarea value={draft.notes} onChange={(e) => setDraft({ ...draft, notes: e.target.value })} placeholder="Notes" />
            <div className="form-actions">
              <button className="primary-btn" type="submit">Save Assignment</button>
              <button className="action-btn" type="button" onClick={() => setDraft(null)}>Cancel</button>
            </div>
          </form>
        </Card>
      )}

      <div className="assignments-grid">
        {filteredAssignments.map((assignment) => {
          const overdue = assignment.dueDate && new Date(`${assignment.dueDate}T00:00:00`) < new Date() && assignment.status !== 'submitted';
          return (
            <Card className={`assignment-card ${overdue ? 'overdue' : ''}`} key={assignment.id}>
              <div className="assignment-header">
                <div>
                  <h4 className="assignment-title">{assignment.title}</h4>
                  <p className="assignment-subject">{assignment.subject}</p>
                </div>
                <span className="priority-badge">{assignment.priority}</span>
              </div>
              <p className="assignment-notes">{assignment.notes}</p>
              <div className="assignment-footer">
                <span>Due: {assignment.dueDate ? formatDate(assignment.dueDate) : 'Not set'}</span>
                <span className={assignment.status === 'submitted' ? 'good-text' : 'risk-text'}>{assignment.status}</span>
              </div>
              {canEdit && (
                <div className="record-actions assignment-actions">
                  <button className="action-btn" type="button" onClick={() => setDraft(assignment)}>Edit</button>
                  <label className="action-btn upload-inline">
                    Upload Files
                    <input type="file" multiple onChange={(e) => uploadDocuments(assignment.id, e.target.files, e.target)} />
                  </label>
                  <label className="action-btn upload-inline">
                    Upload Folder
                    <input type="file" multiple webkitdirectory="" directory="" onChange={(e) => uploadDocuments(assignment.id, e.target.files, e.target)} />
                  </label>
                  <button className="delete-btn" type="button" onClick={() => setAssignments(assignments.filter((item) => item.id !== assignment.id))}>Delete</button>
                </div>
              )}
              <div className="document-list">
                {assignment.documents.map((doc) => {
                  const image = isImageUpload(doc);
                  const previewable = canPreviewFile(doc);

                  return (
                    <div className={`document-item ${image ? 'image-post' : 'file-post'}`} key={doc.id}>
                      <div className="post-topline">
                        <span>{assignment.subject || 'Assignment'}</span>
                        <a href={doc.dataUrl} download={doc.name}>Download</a>
                      </div>
                      {image ? (
                        <img src={doc.dataUrl} alt={doc.name} />
                      ) : (
                        <div className="file-preview">
                          <span>{fileExtension(doc.name)}</span>
                        </div>
                      )}
                      <div className="post-caption">
                        <strong>{doc.name}</strong>
                        <span>{Math.round((doc.size || 0) / 1024)} KB</span>
                      </div>
                      {doc.path && doc.path !== doc.name && <p className="folder-path">{doc.path}</p>}
                      {previewable && (
                        <button className="action-btn" type="button" onClick={() => setPreviewFile(doc)}>
                          Preview
                        </button>
                      )}
                      {canEdit && <button className="delete-btn" type="button" onClick={() => removeDocument(assignment.id, doc.id)}>Remove</button>}
                    </div>
                  );
                })}
              </div>
            </Card>
          );
        })}
      </div>

      {previewFile && (
        <div className="edit-modal-backdrop" onClick={() => setPreviewFile(null)}>
          <Card className="file-preview-modal" role="dialog" aria-modal="true" aria-labelledby="file-preview-title" onClick={(event) => event.stopPropagation()}>
            <div className="file-preview-head">
              <div>
                <h3 id="file-preview-title" className="card-title">{previewFile.name}</h3>
                {previewFile.path && <p>{previewFile.path}</p>}
              </div>
              <div className="record-actions">
                <a className="action-btn" href={previewFile.dataUrl} download={previewFile.name}>Download</a>
                <button className="delete-btn" type="button" onClick={() => setPreviewFile(null)}>Close</button>
              </div>
            </div>
            <pre className="code-preview"><code>{readDataUrlText(previewFile.dataUrl)}</code></pre>
          </Card>
        </div>
      )}
    </section>
  );
}

function BlogTracker({ posts, setPosts, canEdit, notify, searchQuery }) {
  const [draft, setDraft] = useState(null);
  const [commentDrafts, setCommentDrafts] = useState({});

  const savePost = (event) => {
    event.preventDefault();
    if (!draft.title.trim()) return;

    const cleanDraft = {
      ...draft,
      tags: typeof draft.tags === 'string'
        ? draft.tags.split(',').map((tag) => tag.trim()).filter(Boolean)
        : draft.tags,
    };

    if (cleanDraft.id) {
      setPosts(posts.map((post) => (post.id === cleanDraft.id ? cleanDraft : post)));
      notify('Blog or note updated.');
    } else {
      setPosts([...posts, { ...cleanDraft, id: Date.now(), comments: [] }]);
      notify('Blog or note added.');
    }
    setDraft(null);
  };

  const deletePost = (id) => {
    setPosts(posts.filter((post) => post.id !== id));
    notify('Blog or note deleted.');
  };

  const addComment = (postId) => {
    const text = (commentDrafts[postId] || '').trim();
    if (!text) return;
    setPosts(
      posts.map((post) =>
        post.id === postId
          ? {
              ...post,
              comments: [
                ...post.comments,
                { id: Date.now(), text, date: localDateKey(new Date()) },
              ],
            }
          : post
      )
    );
    setCommentDrafts({ ...commentDrafts, [postId]: '' });
    notify('Comment added.');
  };

  const deleteComment = (postId, commentId) => {
    setPosts(
      posts.map((post) =>
        post.id === postId
          ? { ...post, comments: post.comments.filter((comment) => comment.id !== commentId) }
          : post
      )
    );
  };

  const filteredPosts = posts.filter(
    (post) =>
      !searchQuery ||
      post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <section className="tab-section">
      <div className="section-heading-row">
        <h2 className="section-title">Blog & Notes</h2>
        {canEdit && (
          <button
            className="primary-btn"
            type="button"
            onClick={() =>
              setDraft({
                id: null,
                title: '',
                date: localDateKey(new Date()),
                category: 'General',
                details: '',
                tags: '',
                visibility: 'private',
                comments: [],
              })
            }
          >
            Add Blog or Note
          </button>
        )}
      </div>

      {draft && (
        <Card className="editor-card">
          <form className="editor-grid" onSubmit={savePost}>
            <input value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} placeholder="Title" />
            <input type="date" value={draft.date || ''} onChange={(e) => setDraft({ ...draft, date: e.target.value })} />
            <input value={draft.category} onChange={(e) => setDraft({ ...draft, category: e.target.value })} placeholder="Category" />
            <select value={draft.visibility} onChange={(e) => setDraft({ ...draft, visibility: e.target.value })}>
              <option value="private">Private</option>
              <option value="public">Public</option>
            </select>
            <input
              value={Array.isArray(draft.tags) ? draft.tags.join(', ') : draft.tags}
              onChange={(e) => setDraft({ ...draft, tags: e.target.value })}
              placeholder="Tags, separated by commas"
            />
            <textarea value={draft.details} onChange={(e) => setDraft({ ...draft, details: e.target.value })} placeholder="Details / notes" />
            <div className="form-actions">
              <button className="primary-btn" type="submit">Save Blog or Note</button>
              <button className="action-btn" type="button" onClick={() => setDraft(null)}>Cancel</button>
            </div>
          </form>
        </Card>
      )}

      <div className="blog-grid">
        {filteredPosts.map((post) => (
          <Card className="blog-card note-card" key={post.id}>
            <div className="blog-header">
              <div>
                <h3 className="blog-title">{post.title}</h3>
                <p className="blog-category">{post.category} - {post.date ? formatDate(post.date) : 'No date'}</p>
              </div>
              <span className="visibility-badge">{post.visibility}</span>
            </div>
            <p className="blog-content">{post.details}</p>
            <div className="blog-tags">
              {post.tags.map((tag) => <span className="tag" key={tag}>#{tag}</span>)}
            </div>
            {canEdit && (
              <div className="record-actions">
                <button className="action-btn" type="button" onClick={() => setDraft(post)}>Edit</button>
                <button className="delete-btn" type="button" onClick={() => deletePost(post.id)}>Delete</button>
              </div>
            )}
            <div className="comments-box">
              <h4>Comments</h4>
              {post.comments.map((comment) => (
                <div className="comment-item" key={comment.id}>
                  <div>
                    <span>{comment.date ? formatDate(comment.date) : 'No date'}</span>
                    <p>{comment.text}</p>
                  </div>
                  {canEdit && <button className="delete-btn" type="button" onClick={() => deleteComment(post.id, comment.id)}>Remove</button>}
                </div>
              ))}
              {canEdit && (
                <div className="comment-form">
                  <input
                    value={commentDrafts[post.id] || ''}
                    onChange={(e) => setCommentDrafts({ ...commentDrafts, [post.id]: e.target.value })}
                    placeholder="Write a comment"
                  />
                  <button className="action-btn" type="button" onClick={() => addComment(post.id)}>Add Comment</button>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}

export default function PMVikasTracker({ darkMode, setDarkMode }) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [notification, setNotification] = useState(null);
  const [canEdit, setCanEdit] = useState(false);
  const [quote, setQuote] = useState(QUOTES[0]);
  const [syncing, setSyncing] = useState(false);
  const {
    courses,
    setCourses,
    projects,
    setProjects,
    assignments,
    setAssignments,
    blogPosts,
    setBlogPosts,
    stats: allStats,
  } = usePMVikasData();

  const notify = (message, type = 'success') => {
    setNotification({ message, type });
    window.setTimeout(() => setNotification(null), 2800);
  };

  const cloudSyncEnabled = isRemoteSyncConfigured();

  const uploadDeviceChanges = async () => {
    setSyncing(true);
    try {
      await uploadPMVikasChanges({ courses, projects, assignments, blogPosts });
      notify('This device uploaded tracker changes.');
    } catch {
      notify('Cloud sync is not ready. Check Supabase and Vercel env vars.', 'error');
    } finally {
      setSyncing(false);
    }
  };

  const downloadLatestChanges = async () => {
    setSyncing(true);
    try {
      const latest = await downloadPMVikasChanges();
      setCourses(latest.courses);
      setProjects(latest.projects);
      setAssignments(latest.assignments);
      setBlogPosts(latest.blogPosts);
      notify('Latest tracker changes loaded.');
    } catch {
      notify('Could not load cloud changes. Check Supabase and Vercel env vars.', 'error');
    } finally {
      setSyncing(false);
    }
  };

  const unlock = (pin) => {
    const storedPin = localStorage.getItem('pmVikas_ownerPin') || DEFAULT_PIN;
    if (pin === storedPin) {
      setCanEdit(true);
      notify('Edit mode unlocked.');
      return true;
    } else {
      notify('Wrong PIN. Editing stays locked.', 'error');
      return false;
    }
  };

  const changePin = (newPin) => {
    if (newPin.trim().length < 4) {
      notify('Use at least 4 digits or characters.', 'error');
      return false;
    }
    localStorage.setItem('pmVikas_ownerPin', newPin.trim());
    notify('Owner PIN changed.');
    return true;
  };

  return (
    <div className={`pm-vikas-container ${darkMode ? 'dark-mode' : 'light-mode'}`}>
      <header className="pm-header">
        <div className="header-left">
          <h1 className="logo">PM Vikas Tracker</h1>
          <p className="tagline">Academic progress, attendance, files, and project proof</p>
        </div>
        <div className="header-right">
          <input className="search-bar" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search..." />
          <button className="theme-toggle" type="button" onClick={() => setDarkMode(!darkMode)}>{darkMode ? 'Light' : 'Dark'}</button>
          <div className="profile-avatar">EV</div>
        </div>
      </header>

      <nav className="sidebar">
        <div className="nav-section">
          {[
            ['dashboard', 'Dashboard'],
            ['attendance', 'Attendance'],
            ['projects', 'Projects'],
            ['assignments', 'Assignments'],
            ['blog', 'Blog'],
          ].map(([id, label]) => (
            <button key={id} className={`nav-item ${activeTab === id ? 'active' : ''}`} type="button" onClick={() => setActiveTab(id)}>
              {label}
            </button>
          ))}
        </div>
      </nav>

      <main className="main-content">
        <SecurityPanel
          canEdit={canEdit}
          onUnlock={unlock}
          onLock={() => {
            setCanEdit(false);
            notify('Edit mode locked.');
          }}
          onChangePin={changePin}
        />
        <CloudSyncPanel
          enabled={cloudSyncEnabled}
          syncing={syncing}
          onUpload={uploadDeviceChanges}
          onDownload={downloadLatestChanges}
        />

        {activeTab === 'dashboard' && (
          <section className="tab-section">
            <h2 className="section-title">Dashboard</h2>
            <div className="stats-grid">
              <StatCard icon="AT" label="Average Attendance" value={`${allStats.attendance}%`} color="#3b82f6" />
              <StatCard icon="AS" label="Open Assignments" value={allStats.pendingAssignments} color="#f59e0b" />
              <StatCard icon="PR" label="Active Projects" value={allStats.activeProjects} color="#10b981" />
              <StatCard icon="UP" label="Uploaded Docs" value={allStats.uploadedDocs} color="#8b5cf6" />
            </div>
            <Card className="course-attendance-panel">
              <h3 className="card-title">Course Attendance</h3>
              <div className="course-attendance-grid">
                {allStats.courseBreakdown.map((course) => (
                  <div className="course-attendance-card" key={course.id}>
                    <div className="course-attendance-head">
                      <div>
                        <strong>{course.name}</strong>
                        <span>{course.code || 'No code'} · {course.classDays || 'No'} class days</span>
                      </div>
                      <b className={course.stats.percent < course.target ? 'risk-text' : 'good-text'}>
                        {course.stats.percent}%
                      </b>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{ width: `${course.stats.percent}%` }}
                      />
                    </div>
                    <div className="course-attendance-foot">
                      <span>{course.stats.attended} attended</span>
                      <span>{course.stats.missed} missed</span>
                      <span>{course.stats.total} total</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
            <div className="widgets-row">
              <Card className="quote-widget">
                <h4 className="widget-title">Daily Motivation</h4>
                <p className="quote-text">"{quote}"</p>
                <button className="refresh-btn" type="button" onClick={() => setQuote(QUOTES[Math.floor(Math.random() * QUOTES.length)])}>New Quote</button>
              </Card>
              <Card className="recent-activity">
                <h3 className="card-title">Tracker Snapshot</h3>
                <div className="activity-list">
                  <div className="activity-item"><span>Courses</span><strong>{courses.length}</strong></div>
                  <div className="activity-item"><span>Projects</span><strong>{projects.length}</strong></div>
                  <div className="activity-item"><span>Assignments</span><strong>{assignments.length}</strong></div>
                </div>
              </Card>
            </div>
          </section>
        )}

        {activeTab === 'attendance' && <AttendanceTracker courses={courses} setCourses={setCourses} canEdit={canEdit} notify={notify} />}
        {activeTab === 'projects' && <ProjectTracker projects={projects} setProjects={setProjects} canEdit={canEdit} notify={notify} />}
        {activeTab === 'assignments' && <AssignmentTracker assignments={assignments} setAssignments={setAssignments} canEdit={canEdit} notify={notify} searchQuery={searchQuery} />}
        {activeTab === 'blog' && <BlogTracker posts={blogPosts} setPosts={setBlogPosts} canEdit={canEdit} notify={notify} searchQuery={searchQuery} />}
      </main>

      {notification && <div className={`notification-toast ${notification.type}`}>{notification.message}</div>}
    </div>
  );
}
