from flask import Flask, render_template, request, session, redirect, url_for
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 在实际应用中请使用更安全的密钥

@app.route('/', methods=['GET', 'POST'])
def index():
    # 初始化游戏
    if 'number' not in session or request.form.get('new_game'):
        session['number'] = random.randint(1, 100)
        session['attempts'] = 0
        session['message'] = '我已经想好了一个1-100之间的数字，猜猜看是多少？'
    
    # 处理用户猜测
    if request.method == 'POST' and 'guess' in request.form:
        try:
            guess = int(request.form['guess'])
            session['attempts'] += 1
            
            if guess < session['number']:
                session['message'] = f'你猜的 {guess} 太小了！再试试看。'
            elif guess > session['number']:
                session['message'] = f'你猜的 {guess} 太大了！再试试看。'
            else:
                session['message'] = f'恭喜你！你猜对了！数字就是 {session["number"]}。你用了 {session["attempts"]} 次尝试。'
        except ValueError:
            session['message'] = '请输入一个有效的数字！'
    
    return render_template('index.html', 
                         message=session.get('message', ''),
                         attempts=session.get('attempts', 0))

if __name__ == '__main__':
    app.run(debug=True)
