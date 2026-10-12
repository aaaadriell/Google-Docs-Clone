from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db

app = FastAPI()

@app.get("/health-check")
def connectivity_check(db: Session = Depends(get_db)):
    try:
        # Perform a simple query to check database connectivity
        return {"status": "Success", "message": "Successfully connected to Neon DB!."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    



