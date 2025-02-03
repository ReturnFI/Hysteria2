import secrets
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel


class SessionData(BaseModel):
    '''Pydantic model for representing session data.'''
    username: str
    created_at: datetime
    expires_at: datetime


class SessionStorage:
    '''Abstracts session storage (default: in-memory, can be replaced with Redis).'''

    def __init__(self):
        # The sessions are now stored as a dictionary with SessionData as values
        self.sessions: dict[str, SessionData] = {}

    def set(self, session_id: str, data: SessionData):
        '''Store the session data with the session_id.'''
        self.sessions[session_id] = data

    def get(self, session_id: str) -> SessionData | None:
        '''Retrieve session data by session_id.'''
        return self.sessions.get(session_id)

    def delete(self, session_id: str):
        '''Delete a session from storage.'''
        self.sessions.pop(session_id, None)


class SessionManager:
    '''Manages user authentication with session storage.'''

    def __init__(self, storage: SessionStorage, expiration_minutes: int = 60):
        self.storage = storage
        self.expiration = timedelta(minutes=expiration_minutes)

    def set_session(self, username: str) -> str:
        '''Generates a session ID and stores user data in the session.'''
        session_id = secrets.token_hex(32)
        session_data = SessionData(username=username, created_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc) + self.expiration)

        self.storage.set(session_id, session_data)

        return session_id

    def get_session(self, session_id: str) -> SessionData | None:
        '''Retrieves and validates a session. Raises HTTPException if the session is invalid or expired.'''
        return self.storage.get(session_id)

    def revoke_session(self, session_id: str):
        '''Removes session from storage.'''
        self.storage.delete(session_id)
