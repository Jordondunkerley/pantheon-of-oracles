# Pantheon API to GPT Router

This service exposes a minimal set of endpoints that allow ChatGPT to send authenticated commands to the Pantheon game backend.

## Endpoints

| Method | Path       | Description                            |
| ------ | ---------- | -------------------------------------- |
| POST   | `/register`| Create a new account                   |
| POST   | `/login`   | Obtain a JWT for subsequent requests   |
| POST   | `/chart`   | Upload or update a natal chart         |
| POST   | `/oracle`  | Create or modify an oracle             |
| POST   | `/battle`  | Trigger a battle action                |
| POST   | `/raids`   | Start a raid                           |
| POST   | `/ritual`  | Perform a ritual                       |
| POST   | `/codex`   | Append to the Codex                    |

All endpoints except `/register` and `/login` require a bearer token in the `Authorization` header.

```
Authorization: Bearer <JWT>
```

## Authentication

Use the `/login` endpoint to obtain a token. The token is signed with `HS256` using the `PANTHEON_GPT_SECRET` environment variable. Tokens expire after one hour.

## Deployment

The router is a standard FastAPI application and can be deployed to services such as Render:

```
# example render start command
uvicorn "router:app" --host 0.0.0.0 --port $PORT
```

Ensure the `PANTHEON_GPT_SECRET` environment variable is configured in your deployment.
