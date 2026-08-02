# API Server Guidelines

- **REST Conventions**: Endpoints should use standard HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`).
- **HTTP Status Codes**:
  - `200 OK`: Successful fetch or non-creation update.
  - `201 Created`: Resource successfully created.
  - `400 Bad Request`: Invalid payload, missing fields, or bad input syntax.
  - `404 Not Found`: Requested resource does not exist.
  - `500 Internal Server Error`: Unhandled server exception.
- **JSON Formatting**: All responses must use `Content-Type: application/json`. Error responses must be structured as `{"error": "<message>"}`.
- **Stateless Handler Design**: Keep HTTP handlers clean and delegate domain logic to testable helper modules.
