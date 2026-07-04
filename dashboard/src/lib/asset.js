// Resolve a root-absolute asset path (e.g. "/book/ch02.pdf") against Vite's
// configured base, so the build works both at "/" (dev) and under a project
// subpath like "/Modern-Robotics/" (GitHub Pages).
const base = import.meta.env.BASE_URL.replace(/\/$/, '');
export const asset = (u) => (typeof u === 'string' && u.startsWith('/') ? base + u : u);
