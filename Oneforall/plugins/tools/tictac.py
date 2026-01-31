# tictactoe.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from collections import defaultdict

# =======================
# Game and leaderboard storage
# =======================
games = {}  # {chat_id: {game_id: game_data}}
leaderboard = defaultdict(lambda: defaultdict(int))  # {chat_id: {user_id: wins}}

# =======================
# Helper functions
# =======================
def render_board(board):
    """Render the board as emoji"""
    symbols = {"X": "❌", "O": "⭕", "": "⬜"}
    return "\n".join("".join(symbols[cell] for cell in row) for row in board)

def check_winner(board):
    """Check if there's a winner"""
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != "":
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] != "":
            return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] != "":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != "":
        return board[0][2]
    return None

def build_keyboard(board, game_id):
    """Build inline keyboard for the board"""
    buttons = []
    for i in range(3):
        row = []
        for j in range(3):
            cell = board[i][j]
            text = " " if cell == "" else cell
            row.append(InlineKeyboardButton(text=text, callback_data=f"{game_id}:{i}:{j}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

# =======================
# Commands
# =======================
@Client.on_message(filters.command("tictactoe") & filters.group)
async def start_game(client: Client, message: Message):
    """Start a new game by replying to a user's message"""
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user's message to challenge them! Example: /tictactoe")

    player1 = message.from_user
    player2 = message.reply_to_message.from_user
    game_id = message.message_id  # unique per game

    board = [["" for _ in range(3)] for _ in range(3)]
    chat_games = games.setdefault(message.chat.id, {})
    chat_games[game_id] = {
        "board": board,
        "players": [player1, player2],
        "turn": 0
    }

    await message.reply_text(
        f"Tic Tac Toe started!\n{player1.mention} vs {player2.mention}\n"
        f"Turn: {player1.mention} (❌)\n\n{render_board(board)}",
        reply_markup=build_keyboard(board, game_id)
    )

@Client.on_callback_query()
async def button_click(client: Client, callback_query: CallbackQuery):
    """Handle button presses"""
    data = callback_query.data.split(":")
    if len(data) != 3:
        return
    game_id, i, j = data
    i, j = int(i), int(j)
    chat_id = callback_query.message.chat.id

    chat_games = games.get(chat_id)
    if not chat_games or int(game_id) not in chat_games:
        return await callback_query.answer("This game no longer exists.", show_alert=True)

    game = chat_games[int(game_id)]
    board = game["board"]
    players = game["players"]
    turn = game["turn"]
    current_player = players[turn]

    if callback_query.from_user.id != current_player.id:
        return await callback_query.answer("Not your turn!", show_alert=True)

    if board[i][j] != "":
        return await callback_query.answer("Cell already taken!", show_alert=True)

    board[i][j] = "X" if turn == 0 else "O"

    winner_symbol = check_winner(board)
    if winner_symbol:
        winner = current_player
        leaderboard[chat_id][winner.id] += 1

        await callback_query.message.edit_text(
            f"🏆 Game Over! {winner.mention} ({winner_symbol}) won!\n\n{render_board(board)}",
            reply_markup=None
        )
        del chat_games[int(game_id)]
        return

    if all(cell != "" for row in board for cell in row):
        await callback_query.message.edit_text(
            f"🤝 Game Over! It's a draw!\n\n{render_board(board)}",
            reply_markup=None
        )
        del chat_games[int(game_id)]
        return

    # Switch turn
    game["turn"] = 1 - turn
    next_player = players[game["turn"]]

    await callback_query.message.edit_text(
        f"Turn: {next_player.mention} ({'❌' if game['turn']==0 else '⭕'})\n\n{render_board(board)}",
        reply_markup=build_keyboard(board, game_id)
    )
    await callback_query.answer()

@Client.on_message(filters.command("ticlead") & filters.group)
async def show_leaderboard(client: Client, message: Message):
    """Show leaderboard of wins in this group"""
    chat_id = message.chat.id
    if chat_id not in leaderboard or not leaderboard[chat_id]:
        return await message.reply_text("No games played yet!")

    sorted_board = sorted(leaderboard[chat_id].items(), key=lambda x: x[1], reverse=True)
    text = "🏆 Tic Tac Toe Leaderboard 🏆\n\n"
    for idx, (user_id, wins) in enumerate(sorted_board[:10], 1):  # top 10
        text += f"{idx}. [User](tg://user?id={user_id}) - {wins} wins\n"

    await message.reply_text(text, disable_web_page_preview=True)
