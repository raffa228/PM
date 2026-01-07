import os
import requests
from flask import Flask, request, jsonify
import threading  # Добавляем для фоновой отправки

app = Flask(__name__)

TOKEN = os.getenv('TOKEN', '8155890509:AAFoFKE40Q1fcdldRcnMmI69dkte7LgvTyY')
CHAT_ID = os.getenv('CHAT_ID', '1003538269791')  # Обратите внимание: для групп ID с минусом, типа -100...

def send_to_telegram(audio_url, caller, duration):
    """Фоновая функция отправки в Telegram"""
    if not audio_url:
        return
    try:
        print(f"Фон: Скачиваем аудио {audio_url}")
        audio_response = requests.get(audio_url, timeout=60)
        audio_response.raise_for_status()
        audio_file = audio_response.content
        
        caption = f"Новый звонок от {caller}\nДлительность: {duration} сек"
        files = {'audio': ('recording.mp3', audio_file, 'audio/mpeg')}
        params = {'chat_id': CHAT_ID, 'caption': caption}
        
        send_url = f'https://api.telegram.org/bot{TOKEN}/sendAudio'
        requests.post(send_url, data=params, files=files, timeout=60)
        print("Фон: Аудио успешно отправлено")
        
    except Exception as e:
        print(f"Фон: Ошибка {str(e)}")
        requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                      data={'chat_id': CHAT_ID, 'text': f"Ошибка отправки аудио: {str(e)}\nСсылка: {audio_url}"})

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return 'OK', 200
    
    if request.method == 'POST':
        data = request.get_json(force=True)
        print("Получен POST от Calltouch:", data)  # Для логов
        
        audio_url = data.get('reclink')
        caller = data.get('callerNumber', 'Неизвестный')
        duration = data.get('duration', 'Неизвестно')
        
        # Запускаем отправку в фоне — не ждём!
        threading.Thread(target=send_to_telegram, args=(audio_url, caller, duration)).start()
        
        # МГНОВЕННО отвечаем Calltouch успехом
        return jsonify({'success': True}), 200

@app.route('/')
def home():
    return 'Webhook работает! Готов принимать звонки от Calltouch.'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
