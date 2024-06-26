import random
from data import Data
from leveling_system import Leveling_System
import discord
from random import choice, randint
import asyncio

from discord import colour


class TicTacToe:
    def __init__(self, player_1, plaeyr_2, ctx, all_running_ttt, client):
        self.player_1 = player_1 
        self.player_2 = plaeyr_2
        self.ctx = ctx # Context
        self.all_running_ttt = all_running_ttt # This is a list of all running tictactoe games
        self.current_game = None # This class object
        self.client = client # The bot
        self.turn = choice([self.player_1, self.player_2]) # This will randomly pick between player 1 and 2 to start first

        self.count = 0 # This will count how many moves has been given
        self.o = ':o2:'     # This is O emoji
        self.x = ':regional_indicator_x:'   # This is the X emoji
        self.empty = ':white_large_square:' # This is just white emoji 
        self.gameBoard = [self.empty, self.empty, self.empty, self.empty, self.empty, self.empty, self.empty, self.empty, self.empty]
        self.game_msg = None    # This is the game message 
        self.whos_turn_msg = None   # This is the 'who's turn is it' message
        self.reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'] # All the reactions, that the players can react to
        self.move_choice = {
            '1️⃣': '0',
            '2️⃣': '1',
            '3️⃣': '2',
            '4️⃣': '3',
            '5️⃣': '4',
            '6️⃣': '5',
            '7️⃣': '6',
            '8️⃣': '7',
            '9️⃣': '8'
        }
        self.someone_won = False # If someone won it turns True
        self.running = True # Then the game ends, it turns false. If false player can't make moves
        self.destroy = True # If True this class object will be removed
        self.make_move_msgs = list() # This is a list of all the message's that says "{player} make a move!"
        self.turn_colour = {
            self.player_1.id: colour.Color.from_rgb(255, 0, 0),
            self.player_2.id: colour.Color.blue()
        }

        # This levels are for bots, how lower the level higher the change to do random move
        self.player_1_level = 0 if not self.player_1.bot else Leveling_System(str(self.player_1.id), 0).current_level
        self.player_2_level = 0 if not self.player_2.bot else Leveling_System(str(self.player_2.id), 0).current_level
        self.levels = {self.player_1.name: self.player_1_level, self.player_2.name: self.player_2_level}


    def __repr__(self):
        return '**%s**~**%s**//**%i**' % (self.player_1.name, self.player_2.name, self.ctx.message.id)


    async def print(self, board=None):
        if not board is None:
            line1 = ''.join(board[0:3])
            line2 = ''.join(board[3:6])
            line3 = ''.join(board[6:9])
            return f"{line1}\n{line2}\n{line3}"
        else:
            line1 = ''.join(self.gameBoard[0:3])
            line2 = ''.join(self.gameBoard[3:6])
            line3 = ''.join(self.gameBoard[6:9])
            return f"{line1}\n{line2}\n{line3}"


    async def game_end(self):
        self.running = False
        self.client.reactions_command[self.whos_turn_msg.id] = self.client.reactions_command[self.game_msg.id]
        del self.client.reactions_command[self.game_msg.id]
        await self.whos_turn_msg.add_reaction('🔄')
        for i in self.make_move_msgs:
            await i.delete()
        await asyncio.sleep(60)
        if self.destroy:
            if not self.current_game is None:
                if self.current_game in self.all_running_ttt:
                    await self.whos_turn_msg.remove_reaction('🔄', self.client.user)
                    del self.client.reactions_command[self.whos_turn_msg.id]
                    self.all_running_ttt.remove(self.current_game)


    async def smart_bot_move(self):
        move = None

        _other_player = self.player_2 if self.turn == self.player_1 else self.player_1

        for p in [self.turn, _other_player]:
            ox = self.o if p == self.player_1 else self.x
            for i in self.reactions: # self.reactions is like all the possible moves
                gameBoard_copy = self.gameBoard.copy()
                move_pos = self.move_choice[i]
                gameBoard_copy[int(move_pos)] = ox
                isWinner = await self.check_who_won(gameBoard_copy)

                if isWinner[0] == True and isWinner[1] == p:
                    move = i
                    return move

        open_corners = []
        for i in self.reactions:
            if i in ['1️⃣', '3️⃣', '7️⃣', '9️⃣']:
                open_corners.append(i)
        if len(open_corners) > 0:
            move = choice(open_corners)
            return move

        if '5️⃣' in self.reactions:
            move = '5️⃣'
            return move
        
        open_endges = []
        for i in self.reactions:
            if i in ['2️⃣', '4️⃣', '6️⃣', '8️⃣']:
                open_endges.append(i)
        if len(open_endges) > 0:
            move = choice(open_endges)
        
        return move


    async def send_msg(self, msg):
        await self.ctx.send(msg)


    async def move(self, emoji):
        if self.running:
            if self.turn.bot:
                move_pos = self.move_choice[emoji]
                self.gameBoard[int(move_pos)] = self.o if self.turn == self.player_1 else self.x
                del self.move_choice[emoji]
                self.reactions.remove(emoji)
            else:
                move_pos = self.move_choice[emoji.name]
                self.gameBoard[int(move_pos)] = self.o if self.turn == self.player_1 else self.x
                del self.move_choice[emoji.name]
                self.reactions.remove(emoji.name)
            
            await self.game_msg.edit(content=await self.print())

            self.count += 1

            if self.count >= 3:
                who_won = await self.check_who_won(self.gameBoard)
                if who_won[0]:
                    self.someone_won = True
                    winner_says = Data.read('server.json')['ttt_winners_says']
                    embed = discord.Embed(title='Winner!', colour=colour.Color.from_rgb(0, 255, 0)).set_author(name=who_won[1], icon_url=who_won[1].avatar_url)
                    embed.set_thumbnail(url=who_won[1].avatar_url)
                    embed.description = random.choice(winner_says)

                    exp_to_add = 500

                    member_exp = Leveling_System(str(who_won[1].id), exp_to_add)
                    member_exp.add()

                    await self.whos_turn_msg.edit(embed=embed)
                    await self.game_end()
                    return

            try:
                await self.make_move_msgs[-1].delete()
                self.make_move_msgs.remove(self.make_move_msgs[-1])
            except IndexError:
                pass

            if self.count >= 9:
                embed = discord.Embed(description=f"Tie")
                await self.whos_turn_msg.edit(embed=embed)
                await self.game_end()
                return
            else:
                if self.turn == self.player_1:
                    self.turn = self.player_2
                else:
                    self.turn = self.player_1
                embed = discord.Embed(colour=self.turn_colour[self.turn.id]).set_author(name='%s - turn' % self.turn.name, icon_url=self.turn.avatar_url)
                await self.whos_turn_msg.edit(embed=embed)
            
            if self.turn.bot and not self.count >= 9:
                await asyncio.sleep(1.5)
                if randint(0, self.levels[self.turn.name]) == self.levels[self.turn.name]:
                    move = choice(self.reactions)
                else:
                    move = await self.smart_bot_move()
                await self.move(move)
        else:
            print('The game is not running')


    async def check_who_won(self, game_board):
        # H check
        board = await self.print(game_board)
        board = board.split('\n')
        for line in board:
            if line == self.x * 3:  # X = player 2
                return True, self.player_2
            elif line == self.o * 3:    # O = player 1
                return True, self.player_1

        # V check
        v_gb = ['0', '0', '0', '0', '0', '0', '0', '0', '0']
        v_gb[0], v_gb[1], v_gb[2] = game_board[0], game_board[3], game_board[6] # Column 1
        v_gb[3], v_gb[4], v_gb[5] = game_board[1], game_board[4], game_board[7] # Column 2
        v_gb[6], v_gb[7], v_gb[8] = game_board[2], game_board[5], game_board[8] # Column 1
    
        v = await self.print(v_gb)
        v = v.split('\n')
        for line in v:
            if line == self.x * 3:
                return True, self.player_2
            elif line == self.o * 3:
                return True, self.player_1

        # D check
        if game_board[4] == self.x:
            if game_board[0] == self.x and game_board[8] == self.x:
                return True, self.player_2
            elif game_board[2] == self.x and game_board[6] == self.x:
                return True, self.player_2
        elif game_board[4] == self.o:
            if game_board[0] == self.o and game_board[8] == self.o:
                return True, self.player_1
            elif game_board[2] == self.o and game_board[6] == self.o:
                return True, self.player_1
        
        return False, 0