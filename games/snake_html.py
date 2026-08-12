SNAKE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Snake Game</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { box-sizing: border-box; user-select: none; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #0f172a; color: #f8fafc; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; touch-action: none; }
        .header { margin-bottom: 12px; text-align: center; }
        .title { font-size: 24px; font-weight: 700; color: #38bdf8; }
        .scores { display: flex; gap: 20px; font-size: 16px; margin-top: 6px; }
        .score-box { background: #1e293b; padding: 6px 14px; border-radius: 8px; border: 1px solid #334155; }
        #canvas-container { position: relative; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 2px solid #38bdf8; }
        canvas { background: #1e293b; display: block; }
        .controls { display: grid; grid-template-columns: repeat(3, 60px); grid-template-rows: repeat(3, 60px); gap: 8px; margin-top: 16px; }
        .btn { background: #334155; color: #fff; border: none; border-radius: 12px; font-size: 22px; display: flex; align-items: center; justify-content: center; cursor: pointer; active { background: #38bdf8; } }
        .btn:active { background: #38bdf8; color: #0f172a; }
        .btn-up { grid-column: 2; grid-row: 1; }
        .btn-left { grid-column: 1; grid-row: 2; }
        .btn-right { grid-column: 3; grid-row: 2; }
        .btn-down { grid-column: 2; grid-row: 3; }
        .overlay { position: absolute; inset: 0; background: rgba(15, 23, 42, 0.85); display: flex; flex-direction: column; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
        .overlay h2 { font-size: 28px; color: #f43f5e; margin-bottom: 8px; }
        .overlay p { font-size: 18px; margin-bottom: 16px; color: #cbd5e1; }
        .restart-btn { background: #38bdf8; color: #0f172a; border: none; padding: 10px 24px; border-radius: 20px; font-size: 16px; font-weight: 700; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🐍 Snake Game</div>
        <div class="scores">
            <div class="score-box">Score: <span id="score">0</span></div>
            <div class="score-box">Best: <span id="best">0</span></div>
        </div>
    </div>

    <div id="canvas-container">
        <canvas id="gameCanvas" width="300" height="300"></canvas>
        <div id="gameOverOverlay" class="overlay" style="display: none;">
            <h2>Game Over</h2>
            <p>Score: <span id="finalScore">0</span></p>
            <button class="restart-btn" onclick="resetGame()">Play Again</button>
        </div>
    </div>

    <div class="controls">
        <button class="btn btn-up" onclick="setDirection('UP')">▲</button>
        <button class="btn btn-left" onclick="setDirection('LEFT')">◀</button>
        <button class="btn btn-right" onclick="setDirection('RIGHT')">▶</button>
        <button class="btn btn-down" onclick="setDirection('DOWN')">▼</button>
    </div>

    <script>
        const tg = window.Telegram?.WebApp;
        if (tg) tg.expand();

        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");
        const gridSize = 15;
        const tileCount = canvas.width / gridSize;

        let snake = [{ x: 10, y: 10 }];
        let food = { x: 15, y: 15 };
        let dx = 1, dy = 0;
        let score = 0;
        let best = localStorage.getItem("snake_best") || 0;
        document.getElementById("best").innerText = best;
        let gameInterval = null;
        let isGameOver = false;

        function gameLoop() {
            if (isGameOver) return;
            moveSnake();
            if (checkCollision()) {
                endGame();
                return;
            }
            draw();
        }

        function moveSnake() {
            const head = { x: snake[0].x + dx, y: snake[0].y + dy };
            snake.unshift(head);
            if (head.x === food.x && head.y === food.y) {
                score += 10;
                document.getElementById("score").innerText = score;
                placeFood();
            } else {
                snake.pop();
            }
        }

        function checkCollision() {
            const head = snake[0];
            if (head.x < 0 || head.x >= tileCount || head.y < 0 || head.y >= tileCount) return true;
            for (let i = 1; i < snake.length; i++) {
                if (head.i === snake[i].x && head.y === snake[i].y) return true;
            }
            return false;
        }

        function placeFood() {
            food = {
                x: Math.floor(Math.random() * tileCount),
                y: Math.floor(Math.random() * tileCount)
            };
        }

        function draw() {
            ctx.fillStyle = "#1e293b";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Food
            ctx.fillStyle = "#f43f5e";
            ctx.beginPath();
            ctx.arc(food.x * gridSize + gridSize/2, food.y * gridSize + gridSize/2, gridSize/2 - 1, 0, Math.PI * 2);
            ctx.fill();

            // Snake
            snake.forEach((part, index) => {
                ctx.fillStyle = index === 0 ? "#38bdf8" : "#0284c7";
                ctx.fillRect(part.x * gridSize + 1, part.y * gridSize + 1, gridSize - 2, gridSize - 2);
            });
        }

        function setDirection(dir) {
            if (dir === 'UP' && dy === 0) { dx = 0; dy = -1; }
            if (dir === 'DOWN' && dy === 0) { dx = 0; dy = 1; }
            if (dir === 'LEFT' && dx === 0) { dx = -1; dy = 0; }
            if (dir === 'RIGHT' && dx === 0) { dx = 1; dy = 0; }
        }

        document.addEventListener("keydown", e => {
            if (e.key === "ArrowUp") setDirection('UP');
            if (e.key === "ArrowDown") setDirection('DOWN');
            if (e.key === "ArrowLeft") setDirection('LEFT');
            if (e.key === "ArrowRight") setDirection('RIGHT');
        });

        // Swipe gestures
        let touchStartX = 0, touchStartY = 0;
        document.addEventListener('touchstart', e => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        });
        document.addEventListener('touchend', e => {
            const diffX = e.changedTouches[0].clientX - touchStartX;
            const diffY = e.changedTouches[0].clientY - touchStartY;
            if (Math.abs(diffX) > Math.abs(diffY)) {
                if (diffX > 30) setDirection('RIGHT');
                else if (diffX < -30) setDirection('LEFT');
            } else {
                if (diffY > 30) setDirection('DOWN');
                else if (diffY < -30) setDirection('UP');
            }
        });

        function endGame() {
            isGameOver = true;
            clearInterval(gameInterval);
            if (score > best) {
                best = score;
                localStorage.setItem("snake_best", best);
                document.getElementById("best").innerText = best;
            }
            document.getElementById("finalScore").innerText = score;
            document.getElementById("gameOverOverlay").style.display = "flex";
            
            // Post score to Telegram WebApp backend
            fetch("/api/set-score", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ score: score, game: "snake" })
            }).catch(() => {});
        }

        function resetGame() {
            snake = [{ x: 10, y: 10 }];
            dx = 1; dy = 0;
            score = 0;
            isGameOver = false;
            document.getElementById("score").innerText = score;
            document.getElementById("gameOverOverlay").style.display = "none";
            placeFood();
            gameInterval = setInterval(gameLoop, 120);
        }

        resetGame();
    </script>
</body>
</html>
"""
