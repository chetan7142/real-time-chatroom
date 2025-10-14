# Import models to register with SQLAlchemy metadata
from app.models.user import User
from app.models.room import Room
from app.models.message import Message
from app.models.file import File
from app.models.notification import Notification
from app.models.room_member import RoomMember, RoomRole
from app.models.mention import Mention
