GAME2048_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>2048 Game</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { box-sizing: border-box; user-select: none; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #0f172a; color: #f8fafc; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; touch-action: none; }
        .header { margin-bottom: 16px; text-align: center; }
        .title { font-size: 32px; font-weight: 800; color: #f59e0b; }
        .scores { display: flex; gap: 16px; font-size: 16px; margin-top: 8px; }
        .score-box { background: #1e293b; padding: 6px 16px; border-radius: 8px; border: 1px solid #334155; }
        .grid { width: 300px; height: 300px; background: #334155; border-radius: 12px; padding: 8px; display: grid; grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(4, 1fr); gap: 8px; position: relative; }
        .cell { background: rgba(255, 255, 255, 0.05); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 700; color: #fff; transition: all 0.1s ease; }
        .tile-2 { background: #eee4da; color: #776e65; }
        .tile-4 { background: #ede0c8; color: #776e65; }
        .tile-8 { background: #f2b179; color: #f9f6f2; }
        .tile-16 { background: #f59563; color: #f9f6f2; }
        .tile-32 { background: #f67c5f; color: #f9f6f2; }
        .tile-64 { background: #f65e3b; color: #f9f6f2; }
        .tile-128 { background: #edcf72; color: #f9f6f2; font-size: 18px; }
        .tile-256 { background: #edcc61; color: #f9f6f2; font-size: 18px; }
        .tile-512 { background: #edc850; color: #f9f6f2; font-size: 18px; }
        .tile-1024 { background: #edc53f; color: #f9f6f2; font-size: 16px; }
        .tile-2048 { background: #edc22e; color: #f9f6f2; font-size: 16px; }
        .overlay { position: absolute; inset: 0; background: rgba(15, 23, 42, 0.9); display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 12px; }
        .overlay h2 { font-size: 28px; color: #f59e0b; margin-bottom: 8px; }
        .overlay p { font-size: 18px; margin-bottom: 16px; color: #cbd5e1; }
        .restart-btn { background: #f59e0b; color: #0f172a; border: none; padding: 10px 24px; border-radius: 20px; font-size: 16px; font-weight: 700; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🎮 2048</div>
        <div class="scores">
            <div class="score-box">Score: <span id="score">0</span></div>
            <div class="score-box">Best: <span id="best">0</span></div>
        </div>
    </div>

    <div class="grid" id="grid">
        <div id="gameOverOverlay" class="overlay" style="display: none;">
            <h2>Game Over</h2>
            <p>Score: <span id="finalScore">0</span></p>
            <button class="restart-btn" onclick="initGame()">Play Again</button>
        </div>
    </div>

    <script>
        const tg = window.Telegram?.WebApp;
        if (tg) tg.expand();

        let board = Array(4).fill(0).map(() => Array(4).fill(0));
        let score = 0;
        let best = localStorage.getItem("2048_best") || 0;
        document.getElementById("best").innerText = best;

        function initGame() {
            board = Array(4).fill(0).map(() => Array(4).fill(0));
            score = 0;
            document.getElementById("score").innerText = score;
            document.getElementById("gameOverOverlay").style.display = "none";
            addRandomTile();
            addRandomTile();
            render();
        }

        function addRandomTile() {
            let emptyCells = [];
            for (let r = 0; r < 4; r++) {
                for (let c = 0; c < 4; c++) {
                    if (board[r][c] === 0) emptyCells.push({ r, c });
                }
            }
            if (emptyCells.length > 0) {
                let cell = emptyCells[Math.floor(Math.random() * emptyCells.length)];
                board[cell.r][cell.c] = Math.random() < 0.9 ? 2 : 4;
            }
        }

        function render() {
            const grid = document.getElementById("grid");
            const overlay = document.getElementById("gameOverOverlay");
            grid.innerHTML = "";
            grid.appendChild(overlay);

            for (let r = 0; r < 4; r++) {
                for (let c = 0; c < 4; c++) {
                    let val = board[r][c];
                    let cell = document.createElement("div");
                    cell.className = "cell" + (val ? " tile-" + val : "");
                    cell.innerText = val ? val : "";
                    grid.appendChild(cell);
                }
            }
        }

        function slide(row) {
            let arr = row.filter(val => val !== 0);
            for (let i = 0; i < arr.length - 1; i++) {
                if (arr[i] === arr[i + 1]) {
                    arr[i] *= 2;
                    score += arr[i];
                    arr[i + 1] = 0;
                }
            }
            arr = arr.filter(val => val !== 0);
            while (arr.length < 4) arr.push(0);
            return arr;
        }

        function move(direction) {
            let oldBoard = JSON.stringify(board);
            if (direction === "LEFT") {
                for (let r = 0; r < 4; r++) board[r] = slide(board[r]);
            } else if (direction === "RIGHT") {
                for (let r = 0; r < 4; r++) board[r] = slide(board[r].reverse()).reverse();
            } else if (direction === "UP") {
                for (let c = 0; c < 4; c++) {
                    let col = [board[0][c], board[1][c], board[2][c], board[3][c]];
                    col = slide(col);
                    for (let r = 0; r < 4; r++) board[r][c] = col[r];
                }
            } else if (direction === "DOWN") {
                for (let c = 0; c < 4; c++) {
                    let col = [board[0][c], board[1][c], board[2][c], board[3][c]];
                    col = slide(col.reverse()).reverse();
                    for (let r = 0; r < 4; r++) board[r][c] = col[r];
                }
            }

            if (oldBoard !== JSON.stringify(board)) {
                document.getElementById("score").innerText = score;
                addRandomTile();
                render();
                if (checkGameOver()) endGame();
            }
        }

        function checkGameOver() {
            for (let r = 0; r < 4; r++) {
                for (let c = 0; c < 4; c++) {
                    if (board[r][c] === 0) return false;
                    if (r < 3 && board[r][c] === board[r + 1][c]) return false;
                    if (c < 3 && board[r][c] === board[r][c + 1]) return false;
                }
            }
            return true;
        }

        function endGame() {
            if (score > best) {
                best = score;
                localStorage.setItem("2048_best", best);
                document.getElementById("best").innerText = best;
            }
            document.getElementById("finalScore").innerText = score;
            document.getElementById("gameOverOverlay").style.display = "flex";

            fetch("/api/set-score", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ score: score, game: "2048" })
            }).catch(() => {});
        }

        document.addEventListener("keydown", e => {
            if (e.key === "ArrowLeft") move("LEFT");
            if (e.key === "ArrowRight") move("RIGHT");
            if (e.key === "ArrowUp") move("UP");
            if (e.key === "ArrowDown") move("DOWN");
        });

        let touchStartX = 0, touchStartY = 0;
        document.addEventListener('touchstart', e => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        });
        document.addEventListener('touchend', e => {
            const diffX = e.changedTouches[0].clientX - touchStartX;
            const diffY = e.changedTouches[0].clientY - touchStartY;
            if (Math.abs(diffX) > Math.abs(diffY)) {
                if (diffX > 30) move("RIGHT");
                else if (diffX < -30) move("LEFT");
            } else {
                if (diffY > 30) move("DOWN");
                else if (diffY < -30) move("UP");
            }
        });

        initGame();
    </script>
</body>
</html>
"""
