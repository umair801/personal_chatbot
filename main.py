from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import os


load_dotenv()

openapi = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


app = FastAPI()
templates = Jinja2Templates(directory='templates')

chat_log = [{
    'role': 'system',
    'content': 'You are a professional data science assistant. Provide clear, concise, and practical advice. Use minimal formatting and no emojis unless specifically requested. Focus on actionable guidance.',
}]

chat_responses = []


# Chat page -------------------------------------------------
@app.get('/', response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse('home.html', {'request': request, 'chat_responses': chat_responses})


@app.websocket('/ws')
async def websocket_chat(websocket: WebSocket):
    
    await websocket.accept()
    try:
        while True:
            user_input = await websocket.receive_text()
            
            # Add user input to chat log
            chat_log.append({'role': 'user', 'content': user_input})
            chat_responses.append(user_input)
            
            # Get OpenAI response
            response = openapi.chat.completions.create(
                model='chatgpt-4o-latest',
                messages=chat_log,
                temperature=0.6,
                stream=True
            )
            
            bot_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    bot_response += chunk_content
                    # Send each chunk via WebSocket for real-time effect
                    await websocket.send_text(chunk_content)
        
            # Add complete response to chat log
            chat_log.append({'role': 'assistant', 'content': bot_response})
            chat_responses.append(bot_response)
            
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

@app.post('/', response_class=HTMLResponse)
async def chat_form(request: Request, user_input: Annotated[str, Form()]):
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)
    
    response = openapi.chat.completions.create(
        model='chatgpt-4o-latest',
        messages=chat_log,
        temperature=0.6,
    )

    bot_response = response.choices[0].message.content
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return templates.TemplateResponse('home.html', {'request': request, 'chat_responses': chat_responses})


# Image generate page ------------------------------------------
@app.get('/image', response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse('image.html', {'request': request})

@app.post('/image', response_class=HTMLResponse)
async def create_image(request: Request, user_input: Annotated[str, Form()]):
    
    response = openapi.images.generate(
    prompt=user_input,
    n=1,
    size="512x512"
    )

    image_url = response.data[0].url

    return templates.TemplateResponse('image.html', {'request': request, 'image_url': image_url})
