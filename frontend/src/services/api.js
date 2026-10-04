import axios from "axios";

const API_BASE = "https://adaptive-ai-tutor-backend-6i4r.onrender.com/api/v1";
const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const register = (data) => api.post("/auth/register", data);
export const login = (email, password) => {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  return api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
};
export const getMe = () => api.get("/auth/me");

// Student model
export const getStudentModel = () => api.get("/student-model");
export const submitAssessment = (data) => api.post("/student-model/assessment", data);
// Fast recommendation for Dashboard (no LLM)
export const getRecommendation = () => api.get("/student-model/recommendation");

// Course & Lessons
export const getCourse = () => api.get("/course");
export const generateLesson = (lessonId) => api.get(`/lesson/${lessonId}/generate`);

// Quiz
export const getQuiz = (lessonId) => api.get(`/quiz/lesson/${lessonId}`);
export const submitQuiz = (data) => api.post("/quiz/submit", data);

// Progress
export const getProgressHistory = () => api.get("/progress/history");
export const getQuizResults = () => api.get("/progress/quiz-results");

// Admin
export const getStudents = () => api.get("/admin/students");

// Evaluation
export const getTestQuestions = () => api.get("/evaluation/test-questions");
export const submitTest = (data) => api.post("/evaluation/submit-test", data);
export const getMyTests = () => api.get("/evaluation/my-tests");
export const exportCsv = () =>
  api.get("/evaluation/export/csv", { responseType: "blob" });

// Chat
export const chatWithTutor = (data) => api.post("/chat", data);

// Exercises
export const getDetectionExercises = () => api.get("/exercises/detection");
export const evaluateClaim = (data) => api.post("/exercises/evaluate-claim", data);

// Goals & Spaced Repetition
export const getDailyGoal = () => api.get("/goals/daily");
export const getReviewItems = () => api.get("/goals/review");

export default api;

export const createTeacher = (data) =>
  api.post("/admin/create-teacher", data);