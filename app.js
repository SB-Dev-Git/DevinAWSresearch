const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hello World - Node.js ウェブアプリ</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                text-align: center;
                padding: 2rem;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }
            h1 {
                font-size: 3rem;
                margin-bottom: 1rem;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            p {
                font-size: 1.2rem;
                margin-bottom: 0.5rem;
            }
            .info {
                font-size: 0.9rem;
                opacity: 0.8;
                margin-top: 2rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Hello World!</h1>
            <p>Node.jsで作成されたウェブアプリケーション</p>
            <p>Express.jsを使用してサーバーを構築</p>
            <div class="info">
                <p>ポート: ${port}</p>
                <p>作成者: oshima.yoshie@ditgroup.jp</p>
            </div>
        </div>
    </body>
    </html>
  `);
});

app.listen(port, () => {
  console.log(`🚀 Hello Worldウェブアプリが起動しました！`);
  console.log(`📱 ブラウザでアクセス: http://localhost:${port}`);
  console.log(`⏰ 起動時刻: ${new Date().toLocaleString('ja-JP')}`);
});
