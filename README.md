1. Requirements: 
  Python 3.8+
  MongoDB running (local)

2. Recommended packages: 
  fastapi
  uvicorn
  pymongo
  python-dotenv
  passlib[bcrypt]
  python-jose

3. created .venv file and put mongoDB details:
  pip install fastapi uvicorn pymongo python-dotenv passlib[bcrypt] python-jose

4. created file main.py and wrote code and run this:
  uvicorn main:app --reload

5. Here endpoint summary:

  A. POST /register — register user (username, password as query params)
  B. POST /login — login (JSON body: {"username": "...", "password": "..."}) → returns access_token
  C. POST /employees — create employee (JSON body)
  D. GET /employees/{employee_id} — get employee (requires token query param)
  E. PUT /employees/{employee_id} — update employee (JSON body, requires token)
  F. DELETE /employees/{employee_id} — delete employee (requires token)
  G. GET /employees — list employees (query: department, optional skip, limit, requires token)
  H. GET /employees/avg-salary — avg salary by department (query: department, requires token)
  I. GET /employees/search — search by skill (query: skill, requires token)
