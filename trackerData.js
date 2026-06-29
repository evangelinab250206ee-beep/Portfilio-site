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
    const saved = localStorage.getItem(key);
    return saved ? JSON.parse(saved) : fallback;
  } catch {
    return fallback;
  }
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

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value));
    broadcast();
  }, [key, value]);

  return [value, setValue];
}

export function usePMVikasData() {
  const [courses, setCourses] = useStoredState('pmVikas_courses', SAMPLE_COURSES, (items) => items.map(normalizeCourse));
  const [projects, setProjects] = useStoredState('pmVikas_projects_v2', SAMPLE_PROJECTS);
  const [assignments, setAssignments] = useStoredState('pmVikas_assignments_v2', SAMPLE_ASSIGNMENTS);
  const [blogPosts, setBlogPosts] = useStoredState('pmVikas_blog_v2', SAMPLE_BLOG_POSTS, (items) => items.map(normalizeBlogPost));

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
    const refresh = () => {
      setSnapshot({
        courses: getStored('pmVikas_courses', SAMPLE_COURSES).map(normalizeCourse),
        projects: getStored('pmVikas_projects_v2', SAMPLE_PROJECTS),
        assignments: getStored('pmVikas_assignments_v2', SAMPLE_ASSIGNMENTS),
        blogPosts: getStored('pmVikas_blog_v2', SAMPLE_BLOG_POSTS).map(normalizeBlogPost),
        portfolio: getStored('portfolio_cms_v1', DEFAULT_PORTFOLIO),
      });
    };
    window.addEventListener('storage', refresh);
    window.addEventListener('pm-vikas-data-change', refresh);
    window.addEventListener('portfolio-data-change', refresh);
    return () => {
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

  useEffect(() => {
    localStorage.setItem('portfolio_cms_v1', JSON.stringify(portfolio));
    window.dispatchEvent(new Event('portfolio-data-change'));
  }, [portfolio]);

  return [portfolio, setPortfolio];
}
