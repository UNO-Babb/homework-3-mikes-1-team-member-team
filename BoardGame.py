#Name:Michael Walton
#Homework 3
#Cist 1600001.1248
#Date: 01/19/2024


from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def createBoardMap(boardSize):
    return [[None for _ in range(boardSize)] for _ in range(boardSize)]

def updateBoardMap(boardMap, row, col, playerColor):
    boardMap[row][col] = playerColor

def claimEnclosedArea(boardMap, playerColor):
    boardSize = len(boardMap)
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    visited = set()

    def floodFill(x, y):
        #fill bonus tiles
        queue = [(x, y)]
        area = []
        isEnclosed = True

        while queue:
            cx, cy = queue.pop(0)
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            area.append((cx, cy))

            if cx == 0 or cy == 0 or cx == boardSize - 1 or cy == boardSize - 1:
                isEnclosed = False

            #check tile borders
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < boardSize and 0 <= ny < boardSize:
                    if boardMap[nx][ny] is None and (nx, ny) not in visited:
                        queue.append((nx, ny))
                    elif boardMap[nx][ny] != playerColor and boardMap[nx][ny] is not None:
                        isEnclosed = False

        return area if isEnclosed else []

    tileCounts = session.get('tileCounts', {})

    #check for bonus claim
    for x in range(boardSize):
        for y in range(boardSize):
            if boardMap[x][y] is None and (x, y) not in visited:
                enclosedArea = floodFill(x, y)
                if enclosedArea:
                    for ex, ey in enclosedArea:
                        boardMap[ex][ey] = playerColor
                        currentPlayer = session.get('currentPlayer')
                        tileCounts[str(currentPlayer)] += 1

    #update count
    session['tileCounts'] = tileCounts

    return boardMap

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            boardSize = int(request.form.get('boardSize', 5))  #5x5 default
            numPlayers = int(request.form.get('numPlayers', 2))  #2 player default
        except (ValueError, TypeError):
            return render_template('index.html', error='Invalid input. Please enter valid integers.')

        if not (1 <= boardSize <= 20 and 1 <= numPlayers <= 4):
            return render_template('index.html', error='Invalid input. Board size must be between 1 and 20, and players between 1 and 4.')

        #pick colors
        playerColors = []
        for i in range(1, numPlayers + 1):
            color = request.form.get(f'playerColor_{i}', 'red')
            playerColors.append(color)

        #initial status
        session['boardSize'] = boardSize
        session['numPlayers'] = numPlayers
        session['currentPlayer'] = 1
        session['playerColors'] = playerColors
        session['boardMap'] = createBoardMap(boardSize)
        session['tileCounts'] = {str(player): 0 for player in range(1, numPlayers + 1)}

        return redirect(url_for('game'))

    return render_template('index.html')

@app.route('/game', methods=['GET', 'POST'])
def game():
    if 'boardSize' not in session:
        return redirect(url_for('index'))

    boardSize = session.get('boardSize')
    boardMap = session.get('boardMap', [])
    currentPlayer = session.get('currentPlayer', 1)
    playerColors = session.get('playerColors', [])
    tileCounts = session.get('tileCounts', {})

    if request.method == 'POST':
        row = int(request.form.get('row'))
        col = int(request.args.get('col'))
        if boardMap[row][col] is None:
            updateBoardMap(boardMap, row, col, playerColors[currentPlayer - 1])
            session['boardMap'] = boardMap
            tileCounts[str(currentPlayer)] += 1
            session['tileCounts'] = tileCounts

            #claim bonus tiles
            boardMap = claimEnclosedArea(boardMap, playerColors[currentPlayer - 1])
            session['boardMap'] = boardMap

            #next player
            session['currentPlayer'] = (currentPlayer % session['numPlayers']) + 1

        #check for board full
        if all(cell is not None for row in boardMap for cell in row):
            return redirect(url_for('winner'))

        return redirect(url_for('game'))

    return render_template('game.html', boardSize=boardSize, board=boardMap, currentPlayer=currentPlayer, color=playerColors[currentPlayer - 1])

@app.route('/winner')
def winner():
    tileCounts = session.get('tileCounts', {})
    maxTiles = max(tileCounts.values())
    winners = [player for player, count in tileCounts.items() if count == maxTiles]

    # Create a list of tile counts formatted as strings
    tileCountMessages = [f"Player {player}: {count} tiles" for player, count in tileCounts.items()]

    # Determine the winner message
    if len(winners) > 1:
        winnerMessage = f"It's a tie between players {', '.join(winners)}!"
    else:
        winnerMessage = f"Player {winners[0]} wins!"

    return render_template('winner.html', winnerMessage=winnerMessage, tileCountMessages=tileCountMessages)

@app.route('/handle_choice', methods=['POST'])
def handle_choice():
    choice = request.form.get('choice', '').strip().upper()
    if choice == 'Y':
        #index page
        session.clear()
        return redirect(url_for('index'))
    elif choice == 'N':
        #closing message
        session.clear()
        return "Thank you for playing! You can close the browser window.", 200
    else:
        return "Invalid input. Please enter 'Y' or 'N'.", 400

@app.route('/restart', methods=['POST'])
def restart():
    #clear session
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)