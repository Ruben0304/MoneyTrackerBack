import asyncio
from typing import Optional
from google import genai

class GeminiProvider:
    def __init__(self):
        # Hardcoded API key - replace with your actual key
        self.api_key = "AIzaSyBYp960eddWNmCrSgUW3zqUy5Hujdj-LhQ"  # Replace this with your actual API key
        self.client = genai.Client(api_key=self.api_key)
    
    async def chat(self, model: str, prompt: str, system_prompt: Optional[str] = None, streaming: bool = False) -> str:
        if streaming:
            return await self._chat_streaming(model, prompt, system_prompt)
        else:
            return await self._chat_sync(model, prompt, system_prompt)
    
    async def _chat_streaming(self, model: str, prompt: str, system_prompt: Optional[str] = None) -> str:
        full_response = ""
        
        def sync_streaming():
            result = ""
            contents = []
            if system_prompt:
                contents.append(system_prompt)
            contents.append(prompt)
            
            for chunk in self.client.models.generate_content_stream(
                model=model,
                contents=contents,
            ):
                chunk_text = ""
                if hasattr(chunk, 'text') and chunk.text:
                    chunk_text = chunk.text
                elif hasattr(chunk, 'candidates') and chunk.candidates:
                    candidate = chunk.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    chunk_text += part.text
                
                if chunk_text:
                    result += chunk_text
            return result
        
        full_response = await asyncio.to_thread(sync_streaming)
        return full_response
    
    async def _chat_sync(self, model: str, prompt: str, system_prompt: Optional[str] = None) -> str:
        def sync_chat():
            contents = []
            if system_prompt:
                contents.append(system_prompt)
            contents.append(prompt)
            
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
            )
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        return candidate.content.parts[0].text
            if hasattr(response, 'text'):
                return response.text
            return str(response)
        
        return await asyncio.to_thread(sync_chat)

# Global instance
gemini_provider = GeminiProvider()

async def conversar(modelo: str, pregunta: str, system_prompt: Optional[str] = None, streaming: bool = False) -> str:
    return await gemini_provider.chat(modelo, pregunta, system_prompt, streaming)