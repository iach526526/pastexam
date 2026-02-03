import hmac

import httpx
from fastapi import HTTPException

from app.core.config import settings


async def oauth_callback(code: str, state: str = None, stored_state: str = None):
    """
    Verify CSRF token and handle OAuth callback.
    Now supports Google OAuth.
    """
    if (
        not state or not stored_state or
        not hmac.compare_digest(state, stored_state)
    ):
        raise HTTPException(
            status_code=400, detail="Invalid state parameter"
        )
        
    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                settings.OAUTH_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.OAUTH_CLIENT_ID,
                    "client_secret": settings.OAUTH_CLIENT_SECRET,
                    "redirect_uri": settings.OAUTH_REDIRECT_URI,
                },
            )
            token_resp.raise_for_status() # 檢查 4xx/5xx 錯誤
            
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        raise HTTPException(
            status_code=502, detail=f"Failed to connect to OAuth server: {e}"
        )

    token_data = token_resp.json()
    access_token = token_data["access_token"]

    try:
        async with httpx.AsyncClient() as client:
            profile_resp = await client.get(
                settings.OAUTH_USERINFO_URL, # 讀取 .env (https://www.googleapis.com/oauth2/v3/userinfo)
                headers={"Authorization": f"Bearer {access_token}"}
            )
            profile_resp.raise_for_status() # 檢查 4xx/5xx 錯誤
            
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch user info: {e}"
        )

    userinfo = profile_resp.json()
    
    # --- 回傳 Google 格式的字典 ---
    return {
        "provider": "google",               
        "sub": userinfo.get("sub"),         # <-- 從 "username" 改成 "sub" (Google 的 ID)
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),       # <-- 從 "username" 改成 "name"
        "avatar_url": userinfo.get("picture") # <-- Google 會提供頭像
    }
