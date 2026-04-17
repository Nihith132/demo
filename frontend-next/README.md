# AI4 Frontend (Next.js)

## Pages

- `/` Home
- `/patient` Patient dashboard (Firebase Google sign-in)
- `/doctor/login` Doctor login (backend JWT)
- `/doctor` Doctor dashboard

## Env

Copy `.env.local.example` -> `.env.local` and fill:

- `NEXT_PUBLIC_BACKEND_URL` (default http://localhost:8000)
- Firebase client config vars

## Notes

- Patient calls send Firebase ID token as `Authorization: Bearer <token>`
- Doctor calls send backend JWT as `Authorization: Bearer <token>`

