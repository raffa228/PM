import os
import requests
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

TOKEN = os.getenv('TOKEN', '8155890509:AAFoFKE40Q1fcdldRcnMmI69dkte7LgvTyY')
CHAT_ID = os.getenv('CHAT_ID', '-100xxxxxxxxxx')  # ОБЯЗАТЕЛЬНО с минусом для группы!

def send_to_telegram(audio_url, caller, duration):
    if not audio_url:
        return
    try:
        print(f"Скачиваем аудио: {audio_url}")
        audio_response = requests.get(audio_url, timeout=60)
        audio_response.raise_for_status()
        audio_file = audio_response.content
        
        caption = f"Новый звонок от {caller}\nДлительность: {duration} сек"
        files = {'audio': ('recording.mp3', audio_file, 'audio/mpeg')}
        params = {'chat_id': CHAT_ID, 'caption': caption}
        
        send_url = 'https://api.telegram.org/bot{TOKEN}/sendAudio'
        response = requests.post(send_url, data=params, files=files, timeout=60)
        print("Ответ Telegram:", response.json())
        
    except Exception as e:
        print(f"Ошибка отправки: {str(e)}")
        requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                      data={'chat_id': CHAT_ID, 'text': f"Ошибка: {str(e)}\nСсылка: {audio_url}"})

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return 'OK', 200
    
    if request.method == 'POST':
        print("Получен POST-запрос от Calltouch")  # Лог для отладки
        
        # МГНОВЕННО отвечаем успехом — это пройдёт тест!
        threading.Thread(target=lambda: process_data(request.get_json(force=True))).start()
        
        return jsonify({'status': 'ok'}), 200  # Многие сервисы ожидают такой формат!

def process_data(data):
    if not data:
        print("Пустой JSON — это был тест Calltouch")
        return
    
    print("Данные звонка:", data)
    audio_url = data.get('reclink')
    caller = data.get('callerNumber', 'Неизвестный')
    duration = data.get('duration', 'Неизвестно')
    
    send_to_telegram(audio_url, caller, duration)

@app.route('/')
def home():
    return 'Webhook работает! Готов принимать звонки от Calltouch.'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
