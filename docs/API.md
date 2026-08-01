# API Documentation

Base path: `/api/v1`

Interactive OpenAPI: `http://localhost:8000/docs`

## Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create user account |
| POST | `/auth/login` | Login (sets HTTP-only cookie) |
| POST | `/auth/logout` | Clear session cookie |
| GET | `/auth/me` | Current user |

## Households & members

| Method | Path | Description |
|--------|------|-------------|
| POST | `/households` | Onboard household + members |
| GET | `/households` | List my households |
| GET | `/households/{id}` | Household detail |
| PATCH | `/households/{id}` | Update settings |
| POST | `/households/{id}/members` | Add member |
| PATCH | `/households/{id}/members/{member_id}` | Rename / deactivate |
| DELETE | `/households/{id}` | Delete household (export-first recommended) |

## Accounts, categories, imports, events, analytics

See generated OpenAPI for full schemas. Major groups:

- `/institutions`, `/accounts`
- `/categories`, `/category-proposals`, `/rules`
- `/files`, `/imports`, `/imports/{id}/interpretation`, `/imports/{id}/confirm`
- `/raw-rows`, `/source-records`, `/events`
- `/splitwise`, `/recurring`, `/planned`, `/assets`, `/debts`, `/budgets`
- `/dashboard`, `/analytics`, `/forecasts`, `/data-quality`, `/exports`, `/audit`
