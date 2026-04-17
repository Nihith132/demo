export default function ApiDocsPage() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
      <h1 className="text-xl font-semibold">Backend API Docs</h1>
      <p className="mt-2 text-sm text-white/70">
        Run the FastAPI server and open <code>/docs</code>.
      </p>
      <div className="mt-4 text-sm text-white/70">
        <p>
          Default backend URL in this frontend is <code>http://localhost:8000</code>. You can change it in
          <code> NEXT_PUBLIC_BACKEND_URL</code>.
        </p>
      </div>
    </div>
  );
}
