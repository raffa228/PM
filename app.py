import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# БЕЗОПАСНО: используем environment variables (добавим их в Render)
TOKEN = os.getenv('TOKEN', '8155890509:AAFoFKE40Q1fcdldRcnMmI69dkte7LgvTyY')
CHAT_ID = os.getenv('CHAT_ID', '1003538269791')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        data = request.get_json(force=True)
        print("Получен webhook:", data)  # Для отладки в логах Render
        
        audio_url = data.get('reclink')
        caller = data.get('callerNumber', 'Неизвестный')
        duration = data.get('duration', 'Неизвестно')
        
        if audio_url:
            try:
                print(f"Скачиваем аудио: {audio_url}")
                audio_response = requests.get(audio_url, timeout=30)
                audio_response.raise_for_status()
                audio_file = audio_response.content
                
                caption = f"Новый звонок от {caller}\nДлительность: {duration} сек"
                files = {'audio': ('recording.mp3', audio_file, 'audio/mpeg')}
                params = {'chat_id': CHAT_ID, 'caption': caption}
                
                send_url = f'https://api.telegram.org/bot{TOKEN}/sendAudio'  # БЕЗ СКОБОК!
                requests.post(send_url, data=params, files=files, timeout=30)
                print("Аудио отправлено в Telegram")
                
            except Exception as e:
                print(f"Ошибка: {str(e)}")
                requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                            data={'chat_id': CHAT_ID, 'text': f"Ошибка: {str(e)}\nСсылка: {audio_url}"})
        
        return jsonify({'success': True})
    
    elif request.method == 'GET':
        return 'OK', 200

@app.route('/')
def home():
    return 'Webhook работает! Готов принимать звонки от Calltouch.'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)  # ПРАВИЛЬНЫЙ СИНТАКСИС!
