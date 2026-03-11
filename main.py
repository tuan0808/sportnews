"""
main.py — FastAPI backend
Serves cached ESPN news data scraped by scraper_news.py
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional

from scraper_news import (
    scrape_league_news,
    scrape_team_news,
    MAJOR_LEAGUES,
    ESPN_TEAM_IDS,
)

app = FastAPI(title="Sports News API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/news")
def get_league_news(
    league: str = Query(..., description="nfl | nba | mlb | nhl"),
    limit: int  = Query(50, ge=1, le=100),
):
    league = league.lower()
    if league not in MAJOR_LEAGUES:
        raise HTTPException(400, detail=f"League must be one of: {MAJOR_LEAGUES}")
    data = scrape_league_news(league, limit=limit)
    if not data:
        raise HTTPException(503, detail="Could not fetch news")
    return data


@app.get("/api/news/team")
def get_team_news(
    league: str = Query(..., description="nfl | nba | mlb | nhl"),
    team: str   = Query(..., description="Team abbreviation e.g. LAL, KC"),
    limit: int  = Query(25, ge=1, le=50),
):
    league = league.lower()
    if league not in MAJOR_LEAGUES:
        raise HTTPException(400, detail=f"League must be one of: {MAJOR_LEAGUES}")
    data = scrape_team_news(league, team.upper(), limit=limit)
    if not data:
        raise HTTPException(404, detail=f"No news found for {team.upper()}")
    return data


@app.get("/api/teams")
def get_teams(league: str = Query(..., description="nfl | nba | mlb | nhl")):
    league = league.lower()
    teams  = ESPN_TEAM_IDS.get(league)
    if not teams:
        raise HTTPException(400, detail=f"Unknown league: {league}")
    return {"league": league, "teams": sorted(teams.keys())}


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve frontend — put index.html in ./static/
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")
