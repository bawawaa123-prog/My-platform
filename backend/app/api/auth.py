'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-05-30 16:03:31
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-03 15:58:38
FilePath: \My-platform\backend\app\api\auth.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import create_access_token, parse_token_subject
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.user_service import UserService


router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    # 所有需要登录态的接口都复用这一个依赖：
    # 负责从 Bearer Token 解析用户，再把数据库里的真实用户对象注入给业务层。
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    subject = parse_token_subject(credentials.credentials)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_service = UserService(db)
    user = user_service.get_user_by_id(int(subject))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    # 登录接口只做两件事：校验账号密码、签发 JWT。
    user_service = UserService(db)
    user = user_service.authenticate_user(payload.email, payload.password)
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


def require_reviewer(
    current_user: User = Depends(get_current_user),
) -> User:
    # 这个依赖用于需要审核员权限的接口。
    if current_user.role not in {"admin", "agent"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer role required",
        )
    return current_user
