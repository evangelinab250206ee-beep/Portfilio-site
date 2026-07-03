import { useEffect, useMemo, useState } from 'react';

export const DEFAULT_PIN = '2468';

export const SAMPLE_COURSES = [
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

export const SAMPLE_PROJECTS = [
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

export const SAMPLE_ASSIGNMENTS = [
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

export const SAMPLE_BLOG_POSTS = [
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

export const DEFAULT_PORTFOLIO = {
  name: 'Evangelina Maria Jais',
  bio: 'Passionate student and aspiring technology professional with interests in robotics, electronics, and software development. Experienced in teamwork, leadership, and innovation through NASA Space Apps Challenge participation and competitive achievements in karate.',
  role: "Chavarite 25' | NIT Calicut 29' | Sports Captain of Higher Secondary",
  location: 'Pala, Kerala',
  field: 'EEE & Technology',
  interests: 'Robotics, AI & Nanotechnology',
  skills: [
    { name: 'Project Management', level: 95, cat: 'management' },
    { name: 'Agile / Scrum', level: 92, cat: 'management' },
    { name: 'Stakeholder Communication', level: 90, cat: 'management' },
    { name: 'Risk Analysis', level: 85, cat: 'management' },
    { name: 'Python', level: 78, cat: 'tech' },
    { name: 'SQL / Databases', level: 82, cat: 'tech' },
  ],
  projects: [
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
      desc: "Led a team to create an educational video explaining Earth's magnetic field for the NASA Space Apps Challenge. Received Best Use Of Science and Top 8 Ideas awards.",
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
  ],
  awards: [
    { year: '2023', title: 'Best Use Of AI Tools', org: 'NASA Space Apps Challenge' },
    { year: '2024', title: 'Best Use Of Science and Top 10 Ideas', org: 'NASA Space Apps Challenge' },
    { year: '2023', title: 'South India Karate Championship - Bronze Medal (U18)', org: 'South India Karate Championship' },
  ],
  socialLinks: [
    { label: 'Email', url: 'mailto:evangelinatjais@gmail.com' },
    { label: 'Phone', url: 'tel:+917907152494' },
    { label: 'LinkedIn', url: 'https://www.linkedin.com/in/evangelina-jais-440487355' },
  ],
  photos: [],
  certifications: [
    { id: 1, title: 'NASA Space Apps Challenge Participant', issuer: 'NASA Space Apps', year: '2023' },
  ],
};

export const formatDate = (date) =>
  new Date(`${date}T00:00:00`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

export const localDateKey = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const readFiles = (fileList, acceptType = 'any') => {
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

export const getStored = (key, fallback) => {
  try {
    if (typeof localStorage === 'undefined') return fallback;
    const saved = localStorage.getItem(key);
    return saved ? JSON.parse(saved) : fallback;
  } catch {
    return fallback;
  }
};

const DB_NAME = 'pm-vikas-durable-storage';
const DB_VERSION = 1;
const DB_STORE = 'records';
const META_SUFFIX = '__updatedAt';

const canUseBrowserStorage = () => typeof window !== 'undefined';
const remoteTable = import.meta.env.VITE_SUPABASE_TABLE || 'tracker_records';
const PM_SYNC_KEYS = {
  courses: 'pmVikas_courses',
  projects: 'pmVikas_projects_v2',
  assignments: 'pmVikas_assignments_v2',
  blogPosts: 'pmVikas_blog_v2',
};

const getRemoteConfig = () => {
  const url = import.meta.env.VITE_SUPABASE_URL;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

  if (!url || !anonKey) return null;
  return { url: url.replace(/\/$/, ''), anonKey };
};

export const isRemoteSyncConfigured = () => Boolean(getRemoteConfig());

const remoteHeaders = (anonKey) => ({
  apikey: anonKey,
  Authorization: `Bearer ${anonKey}`,
  'Content-Type': 'application/json',
});

const readFromRemote = async (key) => {
  const config = getRemoteConfig();
  if (!config || typeof fetch === 'undefined') return undefined;

  const response = await fetch(
    `${config.url}/rest/v1/${remoteTable}?id=eq.${encodeURIComponent(key)}&select=value,updated_at`,
    {
      headers: remoteHeaders(config.anonKey),
    }
  );

  if (!response.ok) throw new Error('Remote read failed');
  const rows = await response.json();
  return rows[0];
};

const writeToRemote = async (key, value, updatedAt = new Date().toISOString()) => {
  const config = getRemoteConfig();
  if (!config || typeof fetch === 'undefined') return;

  const response = await fetch(`${config.url}/rest/v1/${remoteTable}`, {
    method: 'POST',
    headers: {
      ...remoteHeaders(config.anonKey),
      Prefer: 'resolution=merge-duplicates',
    },
    body: JSON.stringify({
      id: key,
      value,
      updated_at: updatedAt,
    }),
  });

  if (!response.ok) throw new Error('Remote write failed');
};

export const uploadPMVikasChanges = async ({ courses, projects, assignments, blogPosts }) => {
  if (!isRemoteSyncConfigured()) {
    throw new Error('Cloud sync is not configured');
  }

  await Promise.all([
    setStoredDurable(PM_SYNC_KEYS.courses, courses),
    setStoredDurable(PM_SYNC_KEYS.projects, projects),
    setStoredDurable(PM_SYNC_KEYS.assignments, assignments),
    setStoredDurable(PM_SYNC_KEYS.blogPosts, blogPosts),
  ]);
};

export const downloadPMVikasChanges = async () => {
  if (!isRemoteSyncConfigured()) {
    throw new Error('Cloud sync is not configured');
  }

  const [courses, projects, assignments, blogPosts] = await Promise.all([
    getStoredFromRemote(PM_SYNC_KEYS.courses, SAMPLE_COURSES),
    getStoredFromRemote(PM_SYNC_KEYS.projects, SAMPLE_PROJECTS),
    getStoredFromRemote(PM_SYNC_KEYS.assignments, SAMPLE_ASSIGNMENTS),
    getStoredFromRemote(PM_SYNC_KEYS.blogPosts, SAMPLE_BLOG_POSTS),
  ]);

  return {
    courses: courses.map(normalizeCourse),
    projects,
    assignments,
    blogPosts: blogPosts.map(normalizeBlogPost),
  };
};

export const requestPMVikasRefresh = () => {
  if (!canUseBrowserStorage()) return;
  window.dispatchEvent(new Event('pm-vikas-remote-refresh'));
};

const openStorageDatabase = () =>
  new Promise((resolve, reject) => {
    if (!canUseBrowserStorage() || !window.indexedDB) {
      resolve(null);
      return;
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(DB_STORE)) {
        db.createObjectStore(DB_STORE);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });

const readFromIndexedDB = async (key) => {
  const db = await openStorageDatabase();
  if (!db) return undefined;

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(DB_STORE, 'readonly');
    const request = transaction.objectStore(DB_STORE).get(key);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    transaction.oncomplete = () => db.close();
    transaction.onerror = () => db.close();
  });
};

const writeToIndexedDB = async (key, value) => {
  const db = await openStorageDatabase();
  if (!db) return;

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(DB_STORE, 'readwrite');
    transaction.objectStore(DB_STORE).put(value, key);
    transaction.oncomplete = () => {
      db.close();
      resolve();
    };
    transaction.onerror = () => {
      db.close();
      reject(transaction.error);
    };
  });
};

const getLocalUpdatedAt = (key) => {
  try {
    return localStorage.getItem(`${key}${META_SUFFIX}`);
  } catch {
    return null;
  }
};

const setLocalUpdatedAt = (key, updatedAt) => {
  try {
    localStorage.setItem(`${key}${META_SUFFIX}`, updatedAt);
  } catch {
    // Metadata is only for sync conflict checks; storage can still work without it.
  }
};

const hasLocalStorageValue = (key) => {
  try {
    return localStorage.getItem(key) !== null;
  } catch {
    return false;
  }
};

const newerThan = (first, second) => {
  if (!first) return false;
  if (!second) return true;
  return Date.parse(first) > Date.parse(second);
};

const getStoredDurable = async (key, fallback) => {
  try {
    const localSaved = await readFromIndexedDB(key);
    const hasLocalValue = localSaved !== undefined || hasLocalStorageValue(key);
    const localValue = localSaved === undefined ? getStored(key, fallback) : localSaved;
    let localUpdatedAt = getLocalUpdatedAt(key);

    if (hasLocalValue && !localUpdatedAt) {
      localUpdatedAt = new Date().toISOString();
      setLocalUpdatedAt(key, localUpdatedAt);
    }

    const remoteRecord = await readFromRemote(key);

    if (remoteRecord?.value !== undefined) {
      const remoteUpdatedAt = remoteRecord.updated_at;

      if (!hasLocalValue || newerThan(remoteUpdatedAt, localUpdatedAt)) {
        await setStoredLocal(key, remoteRecord.value, remoteUpdatedAt);
        return remoteRecord.value;
      }

      if (newerThan(localUpdatedAt, remoteUpdatedAt)) {
        writeToRemote(key, localValue, localUpdatedAt).catch(() => {
          // The next manual upload or automatic save can retry the cloud update.
        });
      }
    }

    return localValue;
  } catch {
    try {
      const saved = await readFromIndexedDB(key);
      return saved === undefined ? getStored(key, fallback) : saved;
    } catch {
      return getStored(key, fallback);
    }
  }
};

const getStoredFromRemote = async (key, fallback) => {
  const remoteRecord = await readFromRemote(key);

  if (remoteRecord?.value !== undefined) {
    await setStoredLocal(key, remoteRecord.value, remoteRecord.updated_at);
    return remoteRecord.value;
  }

  return getStoredDurable(key, fallback);
};

const setStoredLocal = async (key, value, updatedAt = new Date().toISOString()) => {
  const serialized = JSON.stringify(value);

  try {
    localStorage.setItem(key, serialized);
  } catch {
    try {
      localStorage.removeItem(key);
    } catch {
      // IndexedDB below is the durable source when localStorage is full.
    }
  }

  await writeToIndexedDB(key, value);
  setLocalUpdatedAt(key, updatedAt);
};

const setStoredDurable = async (key, value) => {
  const updatedAt = new Date().toISOString();
  await setStoredLocal(key, value, updatedAt);
  await writeToRemote(key, value, updatedAt);
};

export const normalizeCourse = (course) => ({
  startDate: '',
  endDate: '',
  classDays: '',
  ...course,
  classes: Array.isArray(course.classes) ? course.classes : [],
});

export const normalizeBlogPost = (post) => ({
  category: 'General',
  details: post.details || post.content || '',
  tags: [],
  visibility: 'private',
  ...post,
  comments: Array.isArray(post.comments) ? post.comments : [],
});

export const courseStats = (course) => {
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

const broadcast = () => window.dispatchEvent(new Event('pm-vikas-data-change'));

function useStoredState(key, fallback, normalize = (value) => value) {
  const [value, setValue] = useState(() => normalize(getStored(key, fallback)));
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;

    const refresh = () =>
      getStoredDurable(key, fallback)
        .then((saved) => {
          if (active) setValue(normalize(saved));
        })
        .catch(() => {
          // Keep the current browser state when cloud sync is unavailable.
        });

    refresh()
      .finally(() => {
        if (active) setReady(true);
      });
    const refreshTimer = window.setInterval(refresh, 15000);
    window.addEventListener('focus', refresh);
    window.addEventListener('pm-vikas-remote-refresh', refresh);

    return () => {
      active = false;
      window.clearInterval(refreshTimer);
      window.removeEventListener('focus', refresh);
      window.removeEventListener('pm-vikas-remote-refresh', refresh);
    };
  }, [key]);

  useEffect(() => {
    if (!ready) return;

    setStoredDurable(key, value)
      .catch(() => {
        try {
          localStorage.setItem(key, JSON.stringify(value));
        } catch {
          // The UI should keep working even if browser storage is unavailable.
        }
      })
      .finally(broadcast);
  }, [key, ready, value]);

  return [value, setValue];
}

export function usePMVikasData() {
  const [courses, setCourses] = useStoredState(PM_SYNC_KEYS.courses, SAMPLE_COURSES, (items) => items.map(normalizeCourse));
  const [projects, setProjects] = useStoredState(PM_SYNC_KEYS.projects, SAMPLE_PROJECTS);
  const [assignments, setAssignments] = useStoredState(PM_SYNC_KEYS.assignments, SAMPLE_ASSIGNMENTS);
  const [blogPosts, setBlogPosts] = useStoredState(PM_SYNC_KEYS.blogPosts, SAMPLE_BLOG_POSTS, (items) => items.map(normalizeBlogPost));

  const stats = useMemo(() => buildPMVikasStats({ courses, projects, assignments, blogPosts }), [courses, projects, assignments, blogPosts]);

  return { courses, setCourses, projects, setProjects, assignments, setAssignments, blogPosts, setBlogPosts, stats };
}

export function buildPMVikasStats({ courses, projects, assignments, blogPosts }) {
  const courseBreakdown = courses.map((course) => ({ ...course, stats: courseStats(course) }));
  const totalClasses = courseBreakdown.reduce((sum, course) => sum + course.stats.total, 0);
  const attendedClasses = courseBreakdown.reduce((sum, course) => sum + course.stats.attended, 0);
  const missedClasses = totalClasses - attendedClasses;
  const today = localDateKey(new Date());
  const pendingAssignments = assignments.filter((item) => item.status !== 'submitted');
  const overdueAssignments = pendingAssignments.filter((item) => item.dueDate && item.dueDate < today);
  const completedProjects = projects.filter((item) => item.status === 'completed' || item.progress >= 100);
  const recentActivity = [
    ...blogPosts.map((post) => ({ type: 'Blog', title: post.title, date: post.date, detail: post.category })),
    ...assignments.map((item) => ({ type: 'Assignment', title: item.title, date: item.dueDate, detail: item.status })),
    ...projects.map((item) => ({ type: 'Project', title: item.title, date: item.deadline, detail: item.status })),
  ]
    .filter((item) => item.date)
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 5);

  return {
    attendance: totalClasses ? Math.round((attendedClasses / totalClasses) * 100) : 0,
    attendedClasses,
    missedClasses,
    totalClasses,
    courseBreakdown,
    pendingAssignments: pendingAssignments.length,
    overdueAssignments: overdueAssignments.length,
    activeProjects: projects.filter((item) => item.status === 'in-progress').length,
    completedProjects: completedProjects.length,
    uploadedDocs: assignments.reduce((sum, item) => sum + (item.documents?.length || 0), 0),
    recentActivity,
    warnings: [
      ...(totalClasses && Math.round((attendedClasses / totalClasses) * 100) < 75 ? ['Attendance below 75%'] : []),
      ...(overdueAssignments.length ? [`${overdueAssignments.length} assignment overdue`] : []),
    ],
  };
}

export function useTrackerSnapshot() {
  const [snapshot, setSnapshot] = useState(() => ({
    courses: getStored('pmVikas_courses', SAMPLE_COURSES).map(normalizeCourse),
    projects: getStored('pmVikas_projects_v2', SAMPLE_PROJECTS),
    assignments: getStored('pmVikas_assignments_v2', SAMPLE_ASSIGNMENTS),
    blogPosts: getStored('pmVikas_blog_v2', SAMPLE_BLOG_POSTS).map(normalizeBlogPost),
    portfolio: getStored('portfolio_cms_v1', DEFAULT_PORTFOLIO),
  }));

  useEffect(() => {
    let active = true;

    const refresh = async () => {
      const nextSnapshot = {
        courses: (await getStoredDurable('pmVikas_courses', SAMPLE_COURSES)).map(normalizeCourse),
        projects: await getStoredDurable('pmVikas_projects_v2', SAMPLE_PROJECTS),
        assignments: await getStoredDurable('pmVikas_assignments_v2', SAMPLE_ASSIGNMENTS),
        blogPosts: (await getStoredDurable('pmVikas_blog_v2', SAMPLE_BLOG_POSTS)).map(normalizeBlogPost),
        portfolio: await getStoredDurable('portfolio_cms_v1', DEFAULT_PORTFOLIO),
      };

      if (!active) return;
      setSnapshot({
        ...nextSnapshot,
      });
    };

    refresh();
    window.addEventListener('storage', refresh);
    window.addEventListener('pm-vikas-data-change', refresh);
    window.addEventListener('portfolio-data-change', refresh);
    return () => {
      active = false;
      window.removeEventListener('storage', refresh);
      window.removeEventListener('pm-vikas-data-change', refresh);
      window.removeEventListener('portfolio-data-change', refresh);
    };
  }, []);

  return {
    ...snapshot,
    stats: buildPMVikasStats(snapshot),
  };
}

export function usePortfolioData() {
  const [portfolio, setPortfolio] = useState(() => getStored('portfolio_cms_v1', DEFAULT_PORTFOLIO));
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;

    const refresh = () =>
      getStoredDurable('portfolio_cms_v1', DEFAULT_PORTFOLIO)
        .then((saved) => {
          if (active) setPortfolio(saved);
        })
        .catch(() => {
          // Keep the current browser state when cloud sync is unavailable.
        });

    refresh()
      .finally(() => {
        if (active) setReady(true);
      });
    const refreshTimer = window.setInterval(refresh, 15000);
    window.addEventListener('focus', refresh);
    window.addEventListener('portfolio-remote-refresh', refresh);

    return () => {
      active = false;
      window.clearInterval(refreshTimer);
      window.removeEventListener('focus', refresh);
      window.removeEventListener('portfolio-remote-refresh', refresh);
    };
  }, []);

  useEffect(() => {
    if (!ready) return;

    setStoredDurable('portfolio_cms_v1', portfolio)
      .catch(() => {
        try {
          localStorage.setItem('portfolio_cms_v1', JSON.stringify(portfolio));
        } catch {
          // Keep the in-memory edit visible for this session.
        }
      })
      .finally(() => window.dispatchEvent(new Event('portfolio-data-change')));
  }, [portfolio, ready]);

  return [portfolio, setPortfolio];
}
