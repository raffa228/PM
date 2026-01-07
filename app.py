import os
import requests
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')  # Обязательно с -100... для группы!

def send_to_telegram(audio_url, caller, duration):
    if not audio_url or not TOKEN or not CHAT_ID:
        print("Нет аудио или неверные TOKEN/CHAT_ID")
        return
    
    try:
        print(f"Скачиваем запись: {audio_url}")
        audio_response = requests.get(audio_url, timeout=90)
        audio_response.raise_for_status()
        audio_file = audio_response.content
        
        caption = f"Новый звонок от {caller}\nДлительность: {duration} сек"
        
        files = {'audio': ('recording.mp3', audio_file, 'audio/mpeg')}
        params = {'chat_id': CHAT_ID, 'caption': caption}
        send_url = f'https://api.telegram.org/bot{TOKEN}/sendAudio'
        
        resp = requests.post(send_url, data=params, files=files, timeout=90)
        if resp.ok:
            print("Аудио успешно отправлено в Telegram")
        else:
            print("Ошибка Telegram API:", resp.json())
            
    except Exception as e:
        print(f"Ошибка при отправке: {str(e)}")
        # Fallback — отправляем ссылку текстом
        try:
            requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                          data={'chat_id': CHAT_ID, 'text': f"Ошибка отправки аудио: {str(e)}\nСсылка: {audio_url}"})
        except:
            pass

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return 'OK', 200
    
    if request.method == 'POST':
        print("Получен POST от Calltouch")
        
        # Извлекаем JSON сразу в основной функции (пока контекст жив)
        try:
            data = request.get_json(force=True) or {}
        except:
            data = {}
        
        print("Данные звонка:", data)
        
        audio_url = data.get('reclink')
        caller = data.get('callerNumber', 'Неизвестный')
        duration = data.get('duration', 'Неизвестно')
        
        # Запускаем отправку в фоне, передавая данные явно (не через request!)
        if audio_url:
            threading.Thread(target=send_to_telegram, args=(audio_url, caller, duration), daemon=True).start()
        else:
            print("Нет reclink — возможно, тестовый запрос или запись отключена")
        
        # Мгновенный ответ Calltouch
        return jsonify({'status': 'ok'}), 200

@app.route('/')
def home():
    return 'Webhook работает! Готов принимать звонки от Calltouch.'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
