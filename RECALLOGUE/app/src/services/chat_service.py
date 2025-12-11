from time import sleep

from app.src.schema.message_schemas import SystemResponse, UserMessageRequest

class ChatService:
    """
    Service that is responcible for accepting user messages and prividing responses.
    """
    def message_request(self, message : UserMessageRequest):
        yield SystemResponse(
            content="message 1", 
            sources=None,
            attachments=None,
            other=None
        )
        sleep(0.5)
        yield SystemResponse(
            content="message 2", 
            sources=None,
            attachments=None,
            other=None
        )
    
chat_service = ChatService()