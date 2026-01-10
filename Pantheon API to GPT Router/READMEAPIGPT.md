# Pantheon API to GPT Router

This document describes the HTTP endpoints provided by the FastAPI service used by both the Discord bot and the planned ChatGPT integration. All requests expect JSON bodies and return JSON responses.

## API Endpoints

### `POST /gpt/update-oracle`
Records an oracle action coming from ChatGPT or the Discord bot.
- **Headers**: `Authorization: <API_KEY>`
- **Body**: object containing `command`, `oracle_name`, `action`, and a `metadata` object.
- **Response**: confirmation of the update timestamp.

### `POST /auth/signup`
Creates a new player account.
- **Body**: `{ "email": "user@example.com", "password": "secret" }`
- **Response**: success message and Supabase signup result.

### `POST /auth/login`
Logs a user in and returns an authentication session.
- **Body**: `{ "email": "user@example.com", "password": "secret" }`
- **Response**: success message with session details.

## JWT Authentication
The signup and login endpoints use Supabase authentication. The resulting session token can be supplied as a Bearer token in the `Authorization` header when calling protected endpoints.

## Deployment Notes
The FastAPI app is configured for deployment on [Render](https://render.com). Define the following environment variables when running the service:

- `API_KEY` – shared secret for `/gpt/update-oracle`
- `SUPABASE_URL` – your Supabase instance URL
- `SUPABASE_SERVICE_KEY` – Supabase service role key
- `RELEASED_PATCHES` – comma-separated list of content patches available to players

This router keeps progress synchronized between Discord and GPT clients.
