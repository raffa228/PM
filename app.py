import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TOKEN = '8155890509:AAFoFKE40Q1fcdldRcnMmI69dkte7LgvTyY'  
CHAT_ID = '1003538269791'        

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        data = request.get_json(force=True)
        audio_url = data.get('reclink')
        caller = data.get('callerNumber', 'Неизвестный')
        duration = data.get('duration', 'Неизвестно')

        if audio_url:
            try:
                audio_response = requests.get(audio_url, timeout=30)
                audio_response.raise_for_status()
                audio_file = audio_response.content

                caption = f"Новый звонок от {caller}\nДлительность: {duration} сек"

                files = {'audio': ('recording.mp3', audio_file, 'audio/mpeg')}
                params = {'chat_id': CHAT_ID, 'caption': caption}

                send_url = f'https://api.telegram.org/bot{TOKEN}/sendAudio'
                requests.post(send_url, data=params, files=files, timeout=30)

            except Exception as e:
                requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                              data={'chat_id': CHAT_ID, 'text': f"Ошибка отправки аудио: {str(e)}\nСсылка: {audio_url}"})

        return jsonify(success=True)
    
    elif request.method == 'GET':
        return 'OK', 200

@app.route('/')
def home():
    return 'Webhook работает! Готов принимать звонки от Calltouch.'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
