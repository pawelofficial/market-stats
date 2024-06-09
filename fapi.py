

from fastapi import FastAPI, Depends, HTTPException, status

from pydantic import BaseModel

class Agent(BaseModel):
    name: str
    age: int
    
    
app=FastAPI()
agents={}

# spawn agent endpoint 
@app.post("/agents/")
async def create_agent(agent: Agent):
    agents[agent.name] = agent
    return {"agent": agent}

# get agent instance name 
@app.get("/agents/age/")
async def get_agent(name: str):
    age=agents[name].age
    return {"agent": age}

