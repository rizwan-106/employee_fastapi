from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import os
from bson import ObjectId
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/assessment_db")
client = MongoClient(MONGO_URL)
db_name = MONGO_URL.split("/")[-1] if "/" in MONGO_URL else "assessment_db"
db = client[db_name]
collection = db["employees"]

# Add Index on employee_id
collection.create_index([("employee_id", ASCENDING)], unique=True)

# FastAPI App........
app = FastAPI()

# JWT Config......
SECRET_KEY = "rizwan@12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

fake_users_db = {
    "admin": {"username": "admin", "hashed_password": pwd_context.hash("admin123")}
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or not pwd_context.verify(password, user["hashed_password"]):
        return False
    return user

def get_current_user(token: str = Query(..., alias="token")):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

#Pydantic Models..............
class Employee(BaseModel):
    employee_id: str = Field(..., example="E123")
    name: str = Field(..., example="John Doe")
    department: str = Field(..., example="Engineering")
    salary: int = Field(..., example=75000)
    joining_date: str = Field(..., example="2023-01-15")
    skills: List[str] = Field(..., example=["Python", "MongoDB", "APIs"])

class UpdateEmployee(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    salary: Optional[int] = None
    joining_date: Optional[str] = None
    skills: Optional[List[str]] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

#Auth Routes................
@app.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token({"sub": request.username}, token_expires)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/register")
def register_user(username: str, password: str):
    # Hash password and store new user
    # Return success message
    hashed_password = pwd_context.hash(password)
    fake_users_db[username] = {"username": username, "hashed_password": hashed_password}
    return {"message": "User registered successfully"}

#CRUD APIs........

@app.post("/employees")
def create_employee(employee: Employee):
    if collection.find_one({"employee_id": employee.employee_id}):
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    collection.insert_one(employee.dict())
    return {"message": "Employee created successfully"}

@app.get("/employees/{employee_id}")
def get_employee(employee_id: str, user: str = Depends(get_current_user)):
    emp = collection.find_one({"employee_id": employee_id}, {"_id": 0})
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

@app.put("/employees/{employee_id}")
def update_employee(employee_id: str, updates: UpdateEmployee, user: str = Depends(get_current_user)):
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    result = collection.update_one({"employee_id": employee_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee updated successfully"}

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: str, user: str = Depends(get_current_user)):
    result = collection.delete_one({"employee_id": employee_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully"}

#Queries & Aggregations............

@app.get("/employees")
def list_employees(
    department: str,
    skip: int = 0,
    limit: int = 5,
    user: str = Depends(get_current_user)
):
    employees = list(
        collection.find({"department": department}, {"_id": 0})
        .sort("joining_date", -1)
        .skip(skip)
        .limit(limit)
    )
    return employees

@app.get("/employees/avg-salary")
def avg_salary_by_department(department: str, user: str = Depends(get_current_user)):
    pipeline = [
        {"$match": {"department": department}},
        {"$group": {"_id": "$department", "avg_salary": {"$avg": "$salary"}}}
    ]
    result = list(collection.aggregate(pipeline))
    return [{"department": r["_id"], "avg_salary": r["avg_salary"]} for r in result]

@app.get("/employees/search")
def search_employees(skill: str, user: str = Depends(get_current_user)):
    employees = list(collection.find({"skills": skill}, {"_id": 0}))
    return employees

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
