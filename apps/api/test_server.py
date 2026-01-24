"""
Simple FastAPI test server
Compatible with Python 3.14
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="X Tweet Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "x-tweet-generator-api"}

@app.get("/")
async def root():
    return {
        "name": "X Tweet Generator API",
        "version": "2.0.0-test",
        "message": "API is running!"
    }

# Simple tweet analysis (no external deps for now)
@app.post("/api/v1/tweets/analyze")
async def analyze_tweet(data: dict):
    content = data.get("content", "")

    # Simple analysis
    score = 50
    strengths = []
    weaknesses = []
    suggestions = []

    if len(content) > 0:
        if "?" in content:
            score += 10
            strengths.append("Soru içeriyor - reply'leri artırır")
        else:
            suggestions.append("Soru ekleyerek etkileşimi artırın")

        if len(content) > 280:
            weaknesses.append("280 karakter limitini aşıyor")
        elif len(content) < 50:
            suggestions.append("Daha fazla detay ekleyin")
        else:
            strengths.append("İyi uzunluk")

        hashtags = content.count("#")
        if hashtags > 3:
            weaknesses.append("Çok fazla hashtag")
        elif hashtags > 0:
            strengths.append("Hashtag kullanıyor")

    return {
        "score": min(100, score),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "engagement_prediction": {
            "favorite": min(0.05, score / 100),
            "reply": min(0.03, score / 100),
            "repost": min(0.02, score / 100),
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001)
