# galdr/interceptor/backend/modules/portal/engine.py
# --- FINAL LIVE VERSION ---
# This engine now makes live API calls to a locally running Ollama server.

import logging
import aiohttp
import json
from models.database import DatabaseManager
from .models import PortalConversation, PortalMessage

# The default location of the Ollama API.
# In the future, this will be loaded from Galdr's configuration.
OLLAMA_API_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3" # The model we downloaded

class PortalEngine:
    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        # We'll create one aiohttp session and reuse it for performance.
        self.http_session = aiohttp.ClientSession()

    async def _call_llm(self, messages: list[dict], model: str = DEFAULT_MODEL) -> str:
        """
        Calls the Ollama REST API to get a chat completion.
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": False  # We want the full response at once for now.
        }
        
        self.logger.info(f"Sending prompt to Ollama model '{model}' at {OLLAMA_API_URL}...")
        try:
            async with self.http_session.post(OLLAMA_API_URL, json=payload) as response:
                if response.status == 200:
                    response_data = await response.json()
                    assistant_content = response_data.get('message', {}).get('content', '')
                    self.logger.info("Successfully received response from Ollama.")
                    return assistant_content
                else:
                    error_text = await response.text()
                    self.logger.error(f"Ollama API error ({response.status}): {error_text}")
                    return f"Error: The AI backend returned status {response.status}. Please ensure Ollama is running and the model '{model}' is available."
        except aiohttp.ClientConnectorError as e:
            self.logger.error(f"Could not connect to Ollama server at {OLLAMA_API_URL}. Is it running? Error: {e}")
            return "Error: Could not connect to the local AI server. Please ensure Ollama is running."
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during the LLM call: {e}", exc_info=True)
            return "An unexpected error occurred while communicating with the AI."

    # --- Database methods remain the same ---

    def get_all_conversations(self) -> list[dict]:
        """Fetches a list of all conversations, ordered by most recent."""
        session = self.db.get_session()
        try:
            convos = session.query(PortalConversation).order_by(PortalConversation.created_at.desc()).all()
            return [{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()} for c in convos]
        finally:
            session.close()

    def get_conversation_messages(self, conversation_id: str) -> list[dict]:
        """Fetches all messages for a specific conversation."""
        session = self.db.get_session()
        try:
            messages = session.query(PortalMessage).filter(PortalMessage.conversation_id == conversation_id).all()
            return [{"id": m.id, "role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()} for m in messages]
        finally:
            session.close()

    def start_conversation(self, title: str = "New Conversation") -> dict:
        """Starts a new conversation and returns its data."""
        session = self.db.get_session()
        try:
            new_convo = PortalConversation(title=title)
            session.add(new_convo)
            session.flush() # Ensure new_convo.id is generated
            
            system_message = PortalMessage(
                conversation_id=new_convo.id,
                role="system",
                content="You are Portal, a helpful cybersecurity assistant integrated into the Galdr testing suite. You are an expert in web application security, penetration testing, and secure coding practices. Provide concise, accurate, and actionable advice. Format code snippets and payloads using Markdown."
            )
            session.add(system_message)
            session.commit()
            self.logger.info(f"Started new Portal conversation: {new_convo.id}")
            return {"id": new_convo.id, "title": new_convo.title, "created_at": new_convo.created_at.isoformat()}
        finally:
            session.close()


    async def submit_message(self, conversation_id: str, user_message_content: str, context: dict = None) -> dict:
        """The main interaction logic, now with a live LLM call."""
        session = self.db.get_session()
        try:
            # 1. Save user message.
            user_message = PortalMessage(conversation_id=conversation_id, role="user", content=user_message_content)
            session.add(user_message)
            session.commit()
            
            # 2. Fetch history.
            messages = session.query(PortalMessage).filter_by(conversation_id=conversation_id).order_by(PortalMessage.timestamp).all()
            
            # 3. CONTEXT INTEGRATION (The crucial part we'll build on)
            # Create the list of messages for the LLM prompt.
            prompt_messages = []
            
            # Add context first if it exists
            if context:
                # We'll create a more robust formatter later.
                context_str = json.dumps(context, indent=2)
                system_context_message = f"You have the following context from the Galdr tool. Use it to inform your answer.\n\nCONTEXT:\n```json\n{context_str}\n```"
                prompt_messages.append({"role": "system", "content": system_context_message})

            # Add the rest of the message history
            prompt_messages.extend([{"role": msg.role, "content": msg.content} for msg in messages])
            
            # 4. Call the live LLM.
            assistant_response_content = await self._call_llm(prompt_messages)
            
            # 5. Save assistant's response.
            assistant_message = PortalMessage(conversation_id=conversation_id, role="assistant", content=assistant_response_content)
            session.add(assistant_message)
            
            # Update conversation title based on the first real user message
            if len(messages) <= 2: # System, User
                convo = session.query(PortalConversation).filter_by(id=conversation_id).first()
                if convo:
                    convo.title = user_message_content[:50] # Set title to first 50 chars of message
                    
            session.commit()

            return {"id": assistant_message.id, "role": "assistant", "content": assistant_message.content, "timestamp": assistant_message.timestamp.isoformat()}
            
        except Exception as e:
            self.logger.error(f"Portal engine error: {e}", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()
